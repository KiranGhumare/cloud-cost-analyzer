from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_default_region: str = "us-east-1"

    anthropic_api_key: str
    gemini_api_key: str = ""
    openai_api_key: str = ""

    database_url: str

    model_config = {"env_file": ".env"}


settings = Settings()
