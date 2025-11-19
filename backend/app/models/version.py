from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class FlowNode(BaseModel):
    """Vue Flow 노드 데이터"""
    id: str
    type: str
    position: Dict[str, float]
    width: Optional[float] = 250
    height: Optional[float] = 200
    data: Dict[str, Any]


class FlowEdge(BaseModel):
    """Vue Flow 엣지 데이터"""
    id: str
    source: str
    target: str
    label: Optional[str] = ""
    type: Optional[str] = "smoothstep"
    animated: Optional[bool] = True


class FlowState(BaseModel):
    """Vue Flow 전체 상태"""
    nodes: List[FlowNode]
    edges: List[FlowEdge]


class ProjectVersion(BaseModel):
    """프로젝트 버전 정보"""
    id: Optional[str] = None
    name: str = Field(..., min_length=1)
    description: str = ""
    version: int = 1
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    # 저장된 데이터
    business_description: str
    llm_result: Optional[Dict[str, Any]] = None
    flow_state: Optional[FlowState] = None
    ontology_id: Optional[str] = None  # Neo4j 온톨로지와 매핑


class SaveVersionRequest(BaseModel):
    """버전 저장 요청"""
    name: str = Field(..., min_length=1)
    description: Optional[str] = ""
    business_description: str = Field(..., min_length=10)
    llm_result: Optional[Dict[str, Any]] = None
    flow_state: Optional[FlowState] = None
    parent_version_id: Optional[str] = None  # 기존 버전에서 파생된 경우


class UpdateVersionRequest(BaseModel):
    """버전 업데이트 요청"""
    name: Optional[str] = None
    description: Optional[str] = None
    business_description: Optional[str] = None
    llm_result: Optional[Dict[str, Any]] = None
    flow_state: Optional[FlowState] = None


class VersionSummary(BaseModel):
    """버전 목록용 요약 정보"""
    id: str
    name: str
    description: str
    version: int
    created_at: str
    updated_at: str
    has_llm_result: bool
    has_flow_state: bool
    has_ontology: bool
