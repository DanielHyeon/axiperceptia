from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import app.dependencies as deps
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/instances/{aggregate_type}")
async def get_instances(
    aggregate_type: str,
    limit: int = 100
):
    """특정 타입의 모든 인스턴스 조회"""
    try:
        query = f"""
        MATCH (inst:{aggregate_type}:DynamicInstance)
        RETURN inst
        LIMIT $limit
        """
        result = await deps.neo4j_client.execute(query, {'limit': limit})
        return result
    except Exception as e:
        logger.error(f"인스턴스 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/instance/{aggregate_type}/{instance_id}")
async def get_instance(
    aggregate_type: str,
    instance_id: str
):
    """특정 인스턴스 조회"""
    try:
        instance = await deps.neo4j_client.get_instance(aggregate_type, instance_id)
        if not instance:
            raise HTTPException(status_code=404, detail="Instance not found")
        return instance
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"인스턴스 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/events/{aggregate_id}")
async def get_event_stream(
    aggregate_id: str,
    limit: int = 100
):
    """Aggregate의 이벤트 스트림 조회"""
    try:
        events = await deps.neo4j_client.get_event_stream(aggregate_id, limit)
        return events
    except Exception as e:
        logger.error(f"이벤트 스트림 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))
