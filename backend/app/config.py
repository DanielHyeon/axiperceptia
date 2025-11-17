from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"
    
    # Kafka
    kafka_bootstrap_servers: str = "localhost:9092"
    
    # LLM
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    llm_provider: str = "openai"  # openai or anthropic
    llm_model: str = "gpt-4-turbo-preview"
    llm_temperature: float = 0.3
    
    # FastAPI
    backend_port: int = 8000
    cors_origins: List[str] = ["http://localhost:5173"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
