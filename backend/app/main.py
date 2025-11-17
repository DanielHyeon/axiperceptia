from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.db.neo4j_client import Neo4jClient
import app.dependencies as deps

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작 시
    deps.neo4j_client = Neo4jClient(
        uri=settings.neo4j_uri,
        user=settings.neo4j_user,
        password=settings.neo4j_password
    )
    try:
        await deps.neo4j_client.connect()
        print("✅ Neo4j 연결 성공")
    except Exception as e:
        print(f"⚠️ Neo4j 연결 실패 (서버는 계속 실행됩니다): {e}")

    yield

    # 종료 시
    if deps.neo4j_client and deps.neo4j_client.driver:
        await deps.neo4j_client.close()
        print("👋 Neo4j 연결 종료")

# Import routes after dependencies are set up to avoid circular imports
from app.api import event_storm_routes, ontology_routes, command_routes, query_routes, version_routes

app = FastAPI(
    title="Business OS API",
    description="LLM 기반 이벤트 드리븐 온톨로지 시스템",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(event_storm_routes.router, prefix="/api/event-storm", tags=["Event Storming"])
app.include_router(ontology_routes.router, prefix="/api/ontology", tags=["Ontology"])
app.include_router(command_routes.router, prefix="/api/commands", tags=["Commands"])
app.include_router(query_routes.router, prefix="/api/queries", tags=["Queries"])
app.include_router(version_routes.router, prefix="/api/versions", tags=["Versions"])

@app.get("/")
async def root():
    return {
        "message": "Business OS API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "neo4j": await deps.neo4j_client.health_check() if deps.neo4j_client else False
    }
