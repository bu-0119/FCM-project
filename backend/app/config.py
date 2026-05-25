from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    app_name: str = "FCM AI Butler"
    debug: bool = True

    # Database
    database_url: str = "postgresql+asyncpg://fcm:fcm@localhost:5432/fcm"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 days

    # WeChat
    wechat_appid: str = ""
    wechat_secret: str = ""

    # LLM (OpenAI-compatible)
    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"

    # External APIs
    football_data_api_key: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
