from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    github_token: str = Field(default="", alias="GITHUB_TOKEN")
    llm_provider: str = Field(default="glm", alias="LLM_PROVIDER")
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    glm_api_key: str = Field(default="", alias="GLM_API_KEY")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
