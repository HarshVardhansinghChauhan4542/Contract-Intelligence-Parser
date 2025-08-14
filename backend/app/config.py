from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    mongodb_url: str = "mongodb://localhost:27017"
    database_name: str = "contract_intelligence"
    
    llama_api_key: Optional[str] = None           
    huggingface_api_key: Optional[str] = None     
    hf_token: Optional[str] = None               
    upload_directory: str = "uploads"
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    processing_timeout: int = 300
    
    huggingface_model: str = "meta-llama/Llama-3.1-8B-Instruct"
    
    redis_url: str = "redis://localhost:6379"

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = "ignore" 

settings = Settings()
