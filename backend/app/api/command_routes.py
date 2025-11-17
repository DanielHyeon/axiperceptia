from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import app.dependencies as deps
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class CommandRequest(BaseModel):
    aggregate_id: str | None = None
    params: Dict[str, Any]

@router.post("/{command_name}")
async def execute_command(
    command_name: str,
    request: CommandRequest
):
    """
    Command 실행
    
    예: POST /commands/PlaceOrder
    """
    try:
        # Aggregate ID 생성 (없으면)
        agg_id = request.aggregate_id or str(uuid4())
        
        # Command가 속한 Aggregate 찾기
        query = """
        MATCH (cmd:Command {name: $cmd_name})<-[:HAS_COMMAND]-(ot:ObjectType)
        RETURN ot.name as aggregate_type
        """
        result = await deps.neo4j_client.execute(query, {'cmd_name': command_name})

        if not result:
            raise HTTPException(status_code=404, detail="Command not found")

        agg_type = result[0]['aggregate_type']

        # 인스턴스 생성 (간단 구현)
        await deps.neo4j_client.create_instance(
            type_name=agg_type,
            instance_id=agg_id,
            properties=request.params
        )

        # 이벤트 생성 (Command → Event 매핑은 실제론 더 복잡)
        event_name = command_name.replace("Place", "Placed").replace("Create", "Created")
        await deps.neo4j_client.create_event(
            event_type=event_name,
            aggregate_id=agg_id,
            payload=request.params
        )
        
        return {
            "status": "success",
            "aggregate_id": agg_id,
            "event": event_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Command 실행 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))
