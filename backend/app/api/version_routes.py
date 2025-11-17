from fastapi import APIRouter, HTTPException
from typing import List
import app.dependencies as deps
from app.models.version import (
    SaveVersionRequest,
    UpdateVersionRequest,
    ProjectVersion,
    VersionSummary
)
import json
import logging
from uuid import uuid4

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/save", response_model=ProjectVersion)
async def save_version(request: SaveVersionRequest):
    """새 버전 저장"""
    try:
        version_id = str(uuid4())

        # 버전 번호 계산
        version_number = 1
        if request.parent_version_id:
            # 부모 버전이 있으면 버전 번호 증가
            parent_query = """
            MATCH (v:ProjectVersion {id: $parent_id})
            RETURN v.version as version
            """
            parent_result = await deps.neo4j_client.execute(parent_query, {
                'parent_id': request.parent_version_id
            })
            if parent_result:
                version_number = parent_result[0]['version'] + 1

        # Neo4j에 버전 저장
        query = """
        CREATE (v:ProjectVersion {
            id: $id,
            name: $name,
            description: $description,
            version: $version,
            business_description: $business_description,
            llm_result_json: $llm_result_json,
            flow_state_json: $flow_state_json,
            created_at: datetime(),
            updated_at: datetime()
        })
        RETURN v, toString(v.created_at) as created_at, toString(v.updated_at) as updated_at
        """

        result = await deps.neo4j_client.execute_write(query, {
            'id': version_id,
            'name': request.name,
            'description': request.description or "",
            'version': version_number,
            'business_description': request.business_description,
            'llm_result_json': json.dumps(request.llm_result) if request.llm_result else None,
            'flow_state_json': json.dumps(request.flow_state.dict()) if request.flow_state else None
        })

        if not result:
            raise HTTPException(status_code=500, detail="Failed to save version")

        # 부모 버전과의 관계 생성
        if request.parent_version_id:
            relation_query = """
            MATCH (parent:ProjectVersion {id: $parent_id})
            MATCH (child:ProjectVersion {id: $child_id})
            CREATE (parent)-[:HAS_CHILD_VERSION]->(child)
            """
            await deps.neo4j_client.execute_write(relation_query, {
                'parent_id': request.parent_version_id,
                'child_id': version_id
            })

        logger.info(f"버전 저장 완료: {version_id}")

        return ProjectVersion(
            id=version_id,
            name=request.name,
            description=request.description or "",
            version=version_number,
            business_description=request.business_description,
            llm_result=request.llm_result,
            flow_state=request.flow_state,
            created_at=result[0]['created_at'],
            updated_at=result[0]['updated_at']
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"버전 저장 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", response_model=List[VersionSummary])
async def list_versions():
    """모든 버전 목록 조회"""
    try:
        query = """
        MATCH (v:ProjectVersion)
        OPTIONAL MATCH (v)-[:HAS_ONTOLOGY]->(o:ObjectType)
        RETURN v,
               toString(v.created_at) as created_at,
               toString(v.updated_at) as updated_at,
               count(o) > 0 as has_ontology
        ORDER BY v.created_at DESC
        """

        result = await deps.neo4j_client.execute(query)

        versions = []
        for record in result:
            v = record['v']
            versions.append(VersionSummary(
                id=v['id'],
                name=v['name'],
                description=v.get('description', ''),
                version=v['version'],
                created_at=record['created_at'],
                updated_at=record['updated_at'],
                has_llm_result=v.get('llm_result_json') is not None,
                has_flow_state=v.get('flow_state_json') is not None,
                has_ontology=record['has_ontology']
            ))

        return versions

    except Exception as e:
        logger.error(f"버전 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{version_id}", response_model=ProjectVersion)
async def get_version(version_id: str):
    """특정 버전 상세 조회"""
    try:
        query = """
        MATCH (v:ProjectVersion {id: $version_id})
        OPTIONAL MATCH (v)-[:HAS_ONTOLOGY]->(o:ObjectType)
        RETURN v,
               toString(v.created_at) as created_at,
               toString(v.updated_at) as updated_at,
               collect(o.name) as ontology_types
        """

        result = await deps.neo4j_client.execute(query, {'version_id': version_id})

        if not result:
            raise HTTPException(status_code=404, detail="Version not found")

        v = result[0]['v']
        llm_result = None
        flow_state = None

        if v.get('llm_result_json'):
            llm_result = json.loads(v['llm_result_json'])

        if v.get('flow_state_json'):
            flow_state = json.loads(v['flow_state_json'])

        return ProjectVersion(
            id=v['id'],
            name=v['name'],
            description=v.get('description', ''),
            version=v['version'],
            business_description=v['business_description'],
            llm_result=llm_result,
            flow_state=flow_state,
            ontology_id=','.join(result[0]['ontology_types']) if result[0]['ontology_types'] else None,
            created_at=result[0]['created_at'],
            updated_at=result[0]['updated_at']
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"버전 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{version_id}", response_model=ProjectVersion)
async def update_version(version_id: str, request: UpdateVersionRequest):
    """버전 업데이트"""
    try:
        # 업데이트할 필드 동적 생성
        set_clauses = ["v.updated_at = datetime()"]
        params = {'version_id': version_id}

        if request.name is not None:
            set_clauses.append("v.name = $name")
            params['name'] = request.name

        if request.description is not None:
            set_clauses.append("v.description = $description")
            params['description'] = request.description

        if request.business_description is not None:
            set_clauses.append("v.business_description = $business_description")
            params['business_description'] = request.business_description

        if request.llm_result is not None:
            set_clauses.append("v.llm_result_json = $llm_result_json")
            params['llm_result_json'] = json.dumps(request.llm_result)

        if request.flow_state is not None:
            set_clauses.append("v.flow_state_json = $flow_state_json")
            params['flow_state_json'] = json.dumps(request.flow_state.dict())

        query = f"""
        MATCH (v:ProjectVersion {{id: $version_id}})
        SET {', '.join(set_clauses)}
        RETURN v, toString(v.created_at) as created_at, toString(v.updated_at) as updated_at
        """

        result = await deps.neo4j_client.execute_write(query, params)

        if not result:
            raise HTTPException(status_code=404, detail="Version not found")

        v = result[0]['v']
        llm_result = None
        flow_state = None

        if v.get('llm_result_json'):
            llm_result = json.loads(v['llm_result_json'])

        if v.get('flow_state_json'):
            flow_state = json.loads(v['flow_state_json'])

        logger.info(f"버전 업데이트 완료: {version_id}")

        return ProjectVersion(
            id=v['id'],
            name=v['name'],
            description=v.get('description', ''),
            version=v['version'],
            business_description=v['business_description'],
            llm_result=llm_result,
            flow_state=flow_state,
            created_at=result[0]['created_at'],
            updated_at=result[0]['updated_at']
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"버전 업데이트 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{version_id}")
async def delete_version(version_id: str):
    """버전 삭제"""
    try:
        query = """
        MATCH (v:ProjectVersion {id: $version_id})
        DETACH DELETE v
        RETURN count(*) as deleted
        """

        result = await deps.neo4j_client.execute_write(query, {'version_id': version_id})

        if not result or result[0]['deleted'] == 0:
            raise HTTPException(status_code=404, detail="Version not found")

        logger.info(f"버전 삭제 완료: {version_id}")
        return {"status": "success", "deleted_id": version_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"버전 삭제 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{version_id}/link-ontology")
async def link_ontology(version_id: str):
    """버전과 현재 온톨로지 연결"""
    try:
        # 현재 존재하는 ObjectType들과 버전 연결
        query = """
        MATCH (v:ProjectVersion {id: $version_id})
        MATCH (ot:ObjectType)
        MERGE (v)-[:HAS_ONTOLOGY]->(ot)
        RETURN count(ot) as linked_count
        """

        result = await deps.neo4j_client.execute_write(query, {'version_id': version_id})

        linked_count = result[0]['linked_count'] if result else 0
        logger.info(f"온톨로지 연결 완료: {version_id}, {linked_count}개 타입")

        return {
            "status": "success",
            "version_id": version_id,
            "linked_object_types": linked_count
        }

    except Exception as e:
        logger.error(f"온톨로지 연결 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))
