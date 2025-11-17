from fastapi import APIRouter, HTTPException, Depends
from app.models.event_storm import EventStormResult
from app.services.ontology_builder import OntologyBuilder
from app.db.neo4j_client import Neo4jClient
import app.dependencies as deps
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

def get_ontology_builder() -> OntologyBuilder:
    return OntologyBuilder(deps.neo4j_client)

@router.post("/build")
async def build_ontology(
    event_storm: EventStormResult,
    builder: OntologyBuilder = Depends(get_ontology_builder)
):
    """
    이벤트 스토밍 결과 → Neo4j 온톨로지 생성
    
    Semantic + Kinetic Layer를 Neo4j에 생성
    """
    try:
        result = await builder.build(event_storm)
        return result
    except Exception as e:
        logger.error(f"온톨로지 빌드 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/schema/{aggregate_name}")
async def get_aggregate_schema(aggregate_name: str):
    """특정 Aggregate의 스키마 조회"""
    try:
        query = """
        MATCH (ot:ObjectType {name: $name})
        OPTIONAL MATCH (ot)-[:HAS_COMMAND]->(cmd:Command)
        OPTIONAL MATCH (ot)-[:EMITS]->(evt:EventType)
        RETURN ot, collect(DISTINCT cmd) as commands, collect(DISTINCT evt) as events
        """
        result = await deps.neo4j_client.execute(query, {'name': aggregate_name})
        
        if not result:
            raise HTTPException(status_code=404, detail="Aggregate not found")
        
        return result[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"스키마 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list")
async def list_aggregates():
    """모든 Aggregate 목록 조회"""
    try:
        query = """
        MATCH (ot:ObjectType)
        RETURN ot.name as name, ot.properties as properties
        ORDER BY ot.name
        """
        result = await deps.neo4j_client.execute(query)
        return result
    except Exception as e:
        logger.error(f"Aggregate 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/load")
async def load_ontology():
    """Neo4j에서 전체 온톨로지를 불러와서 EventStormResult 형태로 반환"""
    try:
        import json

        # 1. 모든 ObjectType과 관련 Command, Event 조회
        aggregates_query = """
        MATCH (ot:ObjectType)
        OPTIONAL MATCH (ot)-[:HAS_COMMAND]->(cmd:Command)
        OPTIONAL MATCH (ot)-[:EMITS]->(evt:EventType)
        RETURN ot.name as name,
               ot.properties_json as properties_json,
               ot.invariants as invariants,
               collect(DISTINCT {name: cmd.name, parameters_json: cmd.parameters_json}) as commands,
               collect(DISTINCT {name: evt.name, data_schema_json: evt.data_schema_json}) as events
        ORDER BY ot.name
        """

        aggregates_result = await deps.neo4j_client.execute(aggregates_query)

        aggregates = []
        for record in aggregates_result:
            # properties JSON 파싱
            properties = {}
            if record.get('properties_json'):
                try:
                    props = json.loads(record['properties_json'])
                    # PropertyDef 형식을 단순 타입 맵으로 변환
                    for key, val in props.items():
                        if isinstance(val, dict) and 'type' in val:
                            properties[key] = val['type']
                        else:
                            properties[key] = str(val)
                except:
                    properties = {}

            # Commands 변환
            commands = []
            for cmd in record.get('commands', []):
                if cmd.get('name'):
                    params = []
                    if cmd.get('parameters_json'):
                        try:
                            params = json.loads(cmd['parameters_json'])
                        except:
                            params = []
                    commands.append({
                        'name': cmd['name'],
                        'parameters': params,
                        'triggered_by': 'user'
                    })

            # Events 변환
            events = []
            for evt in record.get('events', []):
                if evt.get('name'):
                    data = {}
                    if evt.get('data_schema_json'):
                        try:
                            data = json.loads(evt['data_schema_json'])
                        except:
                            data = {}
                    events.append({
                        'name': evt['name'],
                        'data': data
                    })

            aggregates.append({
                'name': record['name'],
                'commands': commands,
                'events': events,
                'state': properties,
                'invariants': record.get('invariants', [])
            })

        # 2. LinkType (관계) 조회하여 Policies로 변환
        links_query = """
        MATCH (from:ObjectType)-[link:LINK_TYPE]->(to:ObjectType)
        RETURN link.name as name,
               from.name as from_type,
               to.name as to_type
        """

        links_result = await deps.neo4j_client.execute(links_query)

        policies = []
        for i, record in enumerate(links_result):
            # LinkType을 Policy로 변환
            # from_type의 첫 번째 이벤트를 trigger_event로
            # to_type의 첫 번째 커맨드를 action으로
            from_agg = next((a for a in aggregates if a['name'] == record['from_type']), None)
            to_agg = next((a for a in aggregates if a['name'] == record['to_type']), None)

            trigger_event = ''
            actions = []

            if from_agg and from_agg['events']:
                trigger_event = from_agg['events'][0]['name']
            if to_agg and to_agg['commands']:
                actions = [to_agg['commands'][0]['name']]

            policies.append({
                'name': record['name'],
                'trigger_event': trigger_event,
                'actions': actions,
                'description': f"{record['from_type']} -> {record['to_type']}"
            })

        logger.info(f"온톨로지 로드 완료: {len(aggregates)} aggregates, {len(policies)} policies")

        return {
            'aggregates': aggregates,
            'policies': policies
        }

    except Exception as e:
        logger.error(f"온톨로지 로드 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))
