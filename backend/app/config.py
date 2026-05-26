from pydantic_settings import BaseSettings
from pydantic import Field, computed_field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # MongoDB credentials (separate for security)
    db_user: str = Field(default="")
    db_password: str = Field(default="")
    db_host: str = Field(default="localhost:27017")
    db_name: str = Field(default="edu_mind")
    db_options: str = Field(default="retryWrites=true&w=majority")

    langchain_api_key: str = Field(default="")
    langchain_tracing_v2: str = Field(default="")

    # JWT Settings
    jwt_secret_key: str = Field(default="your-secret-key-change-in-production")
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)
    refresh_token_expire_days: int = Field(default=7)

    # File uploads
    upload_dir: str = Field(default="./uploads")
    max_upload_size_mb: int = Field(default=50)

    # CORS
    cors_origins: str = Field(default="http://localhost:3000,http://localhost:5173")

    # AI / LLM
    groq_api_key: str = Field(default="")

    @computed_field
    @property
    def mongodb_url(self) -> str:
        """Construct MongoDB URL from separate credentials."""
        if self.db_user and self.db_password:
            # MongoDB Atlas (cloud)
            return f"mongodb+srv://{self.db_user}:{self.db_password}@{self.db_host}/?{self.db_options}"
        # Local MongoDB (no auth)
        return f"mongodb://{self.db_host}"

    @computed_field
    @property
    def database_name(self) -> str:
        """Alias for db_name."""
        return self.db_name

    @computed_field
    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
