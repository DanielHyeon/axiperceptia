from typing import Dict, List
import logging
import json

from app.db.neo4j_client import Neo4jClient
from app.models.event_storm import EventStormResult, Aggregate, Policy
from app.models.ontology import ObjectType, LinkType, Transformation, PropertyDef

logger = logging.getLogger(__name__)

class OntologyBuilder:
    """이벤트 스토밍 → Palantir 온톨로지 변환"""
    
    def __init__(self, neo4j: Neo4jClient):
        self.neo4j = neo4j
    
    async def build(self, event_storm: EventStormResult):
        """3-Layer 온톨로지 생성"""
        logger.info("온톨로지 빌드 시작...")
        
        # 1. Semantic Layer: ObjectType 생성
        for agg in event_storm.aggregates:
            await self._create_object_type(agg)
        
        # 2. Semantic Layer: LinkType 생성 (Policy 기반)
        for policy in event_storm.policies:
            await self._create_link_from_policy(policy, event_storm)
        
        # 3. Kinetic Layer: Transformation 생성
        for agg in event_storm.aggregates:
            await self._create_transformations(agg)
        
        logger.info("온톨로지 빌드 완료!")
        return {"status": "success", "aggregates": len(event_storm.aggregates)}
    
    async def _create_object_type(self, agg: Aggregate):
        """Aggregate → Neo4j ObjectType"""
        
        # 상태를 PropertyDef로 변환
        properties = {}
        for field, field_type in agg.state.items():
            properties[field] = {
                'type': field_type,
                'required': True
            }
        
        # ObjectType 노드 생성
        await self.neo4j.create_object_type(
            name=agg.name,
            properties=properties,
            invariants=agg.invariants
        )
        
        # Commands 저장
        for cmd in agg.commands:
            query = """
            MATCH (ot:ObjectType {name: $agg_name})
            MERGE (c:Command {name: $cmd_name, aggregate: $agg_name})
            SET c.parameters_json = $params_json
            MERGE (ot)-[:HAS_COMMAND]->(c)
            """
            await self.neo4j.execute_write(query, {
                'agg_name': agg.name,
                'cmd_name': cmd.name,
                'params_json': json.dumps([p if isinstance(p, dict) else {"name": p, "type": "any"} for p in cmd.parameters])
            })

        # Events 저장
        for evt in agg.events:
            query = """
            MATCH (ot:ObjectType {name: $agg_name})
            MERGE (e:EventType {name: $evt_name, aggregate: $agg_name})
            SET e.data_schema_json = $data_json
            MERGE (ot)-[:EMITS]->(e)
            """
            await self.neo4j.execute_write(query, {
                'agg_name': agg.name,
                'evt_name': evt.name,
                'data_json': json.dumps(evt.data)
            })
        
        logger.info(f"ObjectType 생성: {agg.name}")
    
    async def _create_link_from_policy(
        self,
        policy: Policy,
        event_storm: EventStormResult
    ):
        """Policy → LinkType"""
        # Policy: OrderPlaced → CreateShipment
        # 의미: Order -[TRIGGERS]-> Shipment
        
        # 트리거 이벤트를 발행하는 Aggregate 찾기
        source_agg = None
        for agg in event_storm.aggregates:
            if any(e.name == policy.trigger_event for e in agg.events):
                source_agg = agg
                break
        
        if not source_agg:
            return
        
        # 첫 번째 액션(Command)을 받는 Aggregate 찾기
        if not policy.actions:
            return
        
        target_cmd = policy.actions[0]
        target_agg = None
        for agg in event_storm.aggregates:
            if any(c.name == target_cmd for c in agg.commands):
                target_agg = agg
                break
        
        if not target_agg or source_agg.name == target_agg.name:
            return
        
        # LinkType 생성
        await self.neo4j.create_link_type(
            name=policy.name.upper(),
            from_type=source_agg.name,
            to_type=target_agg.name,
            cardinality="1:N"
        )
        
        logger.info(f"LinkType 생성: {source_agg.name} -[{policy.name}]-> {target_agg.name}")
    
    async def _create_transformations(self, agg: Aggregate):
        """Event → Transformation (Kinetic Layer)"""
        
        for evt in agg.events:
            # 기본 변환: 이벤트 발생 시 타임스탬프 업데이트
            query = """
            MATCH (ot:ObjectType {name: $agg_name})
            CREATE (trans:Transformation {
                name: $trans_name,
                trigger: $event_name,
                layer: 'kinetic',
                logic: 'SET aggregate.last_event = $event_name, aggregate.updated_at = timestamp()'
            })
            CREATE (ot)-[:HAS_TRANSFORMATION]->(trans)
            """
            
            await self.neo4j.execute_write(query, {
                'agg_name': agg.name,
                'trans_name': f"{agg.name}_{evt.name}_handler",
                'event_name': evt.name
            })
