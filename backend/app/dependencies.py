from app.db.neo4j_client import Neo4jClient

# Neo4j 클라이언트 전역 인스턴스
neo4j_client: Neo4jClient = None

def get_neo4j_client() -> Neo4jClient:
    return neo4j_client
