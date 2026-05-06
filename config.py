"""Use pydantic settings for type validation and occurs error directly when type/var is not matched/missing"""

from pydantic_settings import BaseSettings, SettingsConfigDict

#BaseSettings inherit the class an ability to read .env while SettingConfigDict as a helper for configuration info to BaseSettings 
class Settings(BaseSettings):

    #read env files and check it to the types below
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore", #ignore unknown vars instead of crashing
    )

    #database
    db_user: str
    db_password: str
    db_name: str
    db_host: str = "localhost"
    db_port: int = 5432

    #redis
    redis_host: str = "localhost"
    redis_port: int = 6379

    #llm and rag
    llm_model: str = "qwen2.5:14b"
    embedding_model: str = "mxbai-embed-large"
    vector_db_path: str | None = None
    phone_number: str | None = None

    #logging and session
    session_ttl_seconds: int = 1800
    log_level: str = "INFO"

    #@property to access method below like an attributes ( class.att only, without () )
    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        )
    
    @property
    def redis_url(self) -> str:
        return (
            f"redis://{self.redis_host}:{self.redis_port}/0"
        )

#will be imported to other files
settings = Settings() 