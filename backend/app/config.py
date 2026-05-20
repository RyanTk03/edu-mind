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

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
