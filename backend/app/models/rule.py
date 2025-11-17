from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class GivenCondition(BaseModel):
    """Given 조건"""
    aggregate: str
    state: Optional[str] = None
    conditions: List[str] = []

class Action(BaseModel):
    """Then 액션"""
    action: str  # recalculate_total, emit_event, call_service, etc
    params: Dict[str, Any] = {}
    
class NestedCondition(BaseModel):
    """중첩 조건"""
    condition: str
    then_actions: List[Action]

class Rule(BaseModel):
    """Given-When-Then 룰"""
    name: str
    given: GivenCondition
    when: str  # 이벤트 이름
    then: List[Action | NestedCondition]
    enabled: bool = True
    priority: int = 0  # 높을수록 우선
    description: Optional[str] = None

class RuleExecutionContext(BaseModel):
    """룰 실행 컨텍스트"""
    aggregate_id: str
    aggregate_type: str
    event: Dict[str, Any]
    current_state: Dict[str, Any]

class RuleExecutionResult(BaseModel):
    """룰 실행 결과"""
    rule_name: str
    status: str  # success, failed, skipped
    actions_executed: List[str]
    error: Optional[str] = None
