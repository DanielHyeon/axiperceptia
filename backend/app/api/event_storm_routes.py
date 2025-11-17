from fastapi import APIRouter, HTTPException, Depends
from app.models.event_storm import AnalyzeRequest, RefineRequest, EventStormResult
from app.services.llm_service import LLMService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

def get_llm_service() -> LLMService:
    return LLMService()

@router.post("/analyze", response_model=EventStormResult)
async def analyze_business(
    request: AnalyzeRequest,
    llm: LLMService = Depends(get_llm_service)
):
    """
    비즈니스 설명을 이벤트 스토밍 분석
    
    LLM을 사용하여 Aggregates, Commands, Events, Policies 추출
    """
    try:
        result = await llm.analyze_business(
            description=request.description,
            examples=request.examples
        )
        return result
    except Exception as e:
        logger.error(f"이벤트 스토밍 분석 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/refine", response_model=EventStormResult)
async def refine_analysis(
    request: RefineRequest,
    llm: LLMService = Depends(get_llm_service)
):
    """
    사용자 피드백으로 분석 결과 개선
    """
    try:
        result = await llm.refine_result(
            current_result=request.current_result,
            feedback=request.feedback
        )
        return result
    except Exception as e:
        logger.error(f"개선 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))
