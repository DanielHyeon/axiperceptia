from neo4j import AsyncGraphDatabase
from typing import List, Dict, Any, Optional
import logging
import json

logger = logging.getLogger(__name__)

class Neo4jClient:
    """Neo4j 비동기 클라이언트"""
    
    def __init__(self, uri: str, user: str, password: str):
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None
    
    async def connect(self):
        """Neo4j 연결"""
        self.driver = AsyncGraphDatabase.driver(
            self.uri,
            auth=(self.user, self.password)
        )
        # 연결 테스트
        async with self.driver.session() as session:
            result = await session.run("RETURN 1")
            await result.single()
        logger.info(f"Connected to Neo4j at {self.uri}")
    
    async def close(self):
        """연결 종료"""
        if self.driver:
            await self.driver.close()
            logger.info("Neo4j connection closed")
    
    async def execute(
        self, 
        query: str, 
        params: Dict[str, Any] = None
    ) -> List[Dict]:
        """Cypher 쿼리 실행"""
        async with self.driver.session() as session:
            result = await session.run(query, params or {})
            records = await result.data()
            return records
    
    async def execute_write(
        self,
        query: str,
        params: Dict[str, Any] = None
    ) -> List[Dict]:
        """쓰기 트랜잭션"""
        async with self.driver.session() as session:
            result = await session.run(query, params or {})
            records = await result.data()
            return records
    
    async def health_check(self) -> bool:
        """헬스 체크"""
        try:
            async with self.driver.session() as session:
                result = await session.run("RETURN 1")
                await result.single()
                return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    # Semantic Layer 쿼리들
    async def create_object_type(
        self,
        name: str,
        properties: Dict,
        invariants: List[str]
    ):
        """ObjectType 노드 생성"""
        query = """
        MERGE (ot:ObjectType {name: $name})
        SET ot.properties_json = $properties_json,
            ot.invariants = $invariants,
            ot.layer = 'semantic',
            ot.updated_at = timestamp()
        RETURN ot
        """
        return await self.execute_write(query, {
            'name': name,
            'properties_json': json.dumps(properties),
            'invariants': invariants
        })
    
    async def create_link_type(
        self,
        name: str,
        from_type: str,
        to_type: str,
        cardinality: str
    ):
        """LinkType 관계 생성"""
        query = """
        MATCH (from:ObjectType {name: $from_type})
        MATCH (to:ObjectType {name: $to_type})
        MERGE (from)-[link:LINK_TYPE {name: $name}]->(to)
        SET link.cardinality = $cardinality,
            link.layer = 'semantic'
        RETURN link
        """
        return await self.execute_write(query, {
            'name': name,
            'from_type': from_type,
            'to_type': to_type,
            'cardinality': cardinality
        })
    
    # Dynamic Layer 쿼리들
    async def create_instance(
        self,
        type_name: str,
        instance_id: str,
        properties: Dict[str, Any]
    ):
        """동적 인스턴스 생성"""
        # Cypher injection 방지를 위해 파라미터 사용
        query = f"""
        MATCH (ot:ObjectType {{name: $type_name}})
        CREATE (inst:{type_name}:DynamicInstance $properties)
        SET inst.id = $instance_id,
            inst.layer = 'dynamic',
            inst.created_at = timestamp()
        CREATE (inst)-[:INSTANCE_OF]->(ot)
        RETURN inst
        """
        
        props = {**properties, 'id': instance_id}
        return await self.execute_write(query, {
            'type_name': type_name,
            'instance_id': instance_id,
            'properties': props
        })
    
    async def get_instance(
        self,
        type_name: str,
        instance_id: str
    ) -> Optional[Dict]:
        """인스턴스 조회"""
        query = f"""
        MATCH (inst:{type_name}:DynamicInstance {{id: $instance_id}})
        RETURN inst
        """
        result = await self.execute(query, {
            'instance_id': instance_id
        })
        return result[0]['inst'] if result else None
    
    async def update_instance(
        self,
        type_name: str,
        instance_id: str,
        properties: Dict[str, Any]
    ):
        """인스턴스 업데이트"""
        set_clause = ", ".join([f"inst.{k} = ${k}" for k in properties.keys()])
        query = f"""
        MATCH (inst:{type_name}:DynamicInstance {{id: $instance_id}})
        SET {set_clause},
            inst.updated_at = timestamp()
        RETURN inst
        """
        params = {**properties, 'instance_id': instance_id}
        return await self.execute_write(query, params)
    
    async def delete_instance(
        self,
        type_name: str,
        instance_id: str
    ):
        """인스턴스 삭제"""
        query = f"""
        MATCH (inst:{type_name}:DynamicInstance {{id: $instance_id}})
        DETACH DELETE inst
        """
        return await self.execute_write(query, {
            'instance_id': instance_id
        })
    
    # 이벤트 로그
    async def create_event(
        self,
        event_type: str,
        aggregate_id: str,
        payload: Dict[str, Any]
    ):
        """도메인 이벤트 생성"""
        query = """
        CREATE (e:DomainEvent {
            type: $event_type,
            aggregate_id: $aggregate_id,
            payload: $payload,
            timestamp: timestamp()
        })
        WITH e
        MATCH (agg {id: $aggregate_id})
        CREATE (agg)-[:EMITTED]->(e)
        RETURN e
        """
        return await self.execute_write(query, {
            'event_type': event_type,
            'aggregate_id': aggregate_id,
            'payload': payload
        })
    
    async def get_event_stream(
        self,
        aggregate_id: str,
        limit: int = 100
    ) -> List[Dict]:
        """Aggregate의 이벤트 스트림 조회"""
        query = """
        MATCH (agg {id: $aggregate_id})-[:EMITTED]->(e:DomainEvent)
        RETURN e
        ORDER BY e.timestamp DESC
        LIMIT $limit
        """
        return await self.execute(query, {
            'aggregate_id': aggregate_id,
            'limit': limit
        })
