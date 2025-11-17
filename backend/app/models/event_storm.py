from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Any, Optional, Union

class Command(BaseModel):
    """도메인 명령"""
    name: str = Field(..., pattern="^[A-Z][a-zA-Z0-9]*$")
    parameters: List[Union[Dict[str, str], str]] = []
    triggered_by: str = "user"  # user, policy, external

    @field_validator('parameters', mode='before')
    @classmethod
    def normalize_parameters(cls, v):
        """문자열 리스트를 딕셔너리 리스트로 변환"""
        if isinstance(v, list):
            normalized = []
            for item in v:
                if isinstance(item, str):
                    # 문자열인 경우 딕셔너리로 변환
                    normalized.append({"name": item, "type": "any"})
                else:
                    normalized.append(item)
            return normalized
        return v

class Event(BaseModel):
    """도메인 이벤트"""
    name: str = Field(..., pattern="^[A-Z][a-zA-Z0-9]*$")
    data: Dict[str, Any] = {}
    
class Aggregate(BaseModel):
    """DDD Aggregate"""
    name: str = Field(..., pattern="^[A-Z][a-zA-Z0-9]*$")
    commands: List[Command]
    events: List[Event]
    state: Dict[str, str]  # field_name: type
    invariants: List[str] = []
    
class Policy(BaseModel):
    """비즈니스 정책 (Saga)"""
    name: str
    trigger_event: str
    actions: List[str]  # Command 이름들
    description: Optional[str] = None

class ReadModel(BaseModel):
    """읽기 모델 (CQRS)"""
    name: str
    source_events: List[str]
    projections: Dict[str, str]

class EventStormResult(BaseModel):
    """LLM 이벤트 스토밍 분석 결과"""
    aggregates: List[Aggregate]
    policies: List[Policy]
    read_models: List[ReadModel] = []
    version: str = "1.0.0"

class AnalyzeRequest(BaseModel):
    """이벤트 스토밍 분석 요청"""
    description: str = Field(..., min_length=10)
    examples: Optional[List[Dict]] = None

class RefineRequest(BaseModel):
    """이벤트 스토밍 개선 요청"""
    current_result: EventStormResult
    feedback: str
