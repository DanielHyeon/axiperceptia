from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum

class Layer(str, Enum):
    """Palantir 3-Layer"""
    SEMANTIC = "semantic"
    KINETIC = "kinetic"
    DYNAMIC = "dynamic"

class PropertyDef(BaseModel):
    """속성 정의"""
    type: str
    required: bool = False
    format: Optional[str] = None
    minimum: Optional[float] = None
    maximum: Optional[float] = None
    pattern: Optional[str] = None

class ObjectType(BaseModel):
    """Semantic Layer: 객체 타입 정의"""
    name: str = Field(..., pattern="^[A-Z][a-zA-Z0-9]*$")
    properties: Dict[str, PropertyDef]
    invariants: List[str] = []
    layer: Layer = Layer.SEMANTIC

class LinkType(BaseModel):
    """Semantic Layer: 관계 타입 정의"""
    name: str = Field(..., pattern="^[A-Z_]+$")
    from_type: str
    to_type: str
    cardinality: str = "1:N"  # 1:1, 1:N, N:M
    properties: Dict[str, PropertyDef] = {}
    layer: Layer = Layer.SEMANTIC

class Transformation(BaseModel):
    """Kinetic Layer: 변환 로직"""
    name: str
    trigger: str  # 이벤트 이름
    input: List[str]
    output: List[str]
    logic: str  # Cypher 또는 Python DSL
    layer: Layer = Layer.KINETIC

class DynamicInstance(BaseModel):
    """Dynamic Layer: 런타임 인스턴스"""
    id: str
    type: str
    properties: Dict[str, Any]
    state: str
    layer: Layer = Layer.DYNAMIC

class OntologySchema(BaseModel):
    """전체 온톨로지 스키마"""
    object_types: List[ObjectType]
    link_types: List[LinkType]
    transformations: List[Transformation]
    version: str = "1.0.0"
