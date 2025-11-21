from dotenv import load_dotenv
load_dotenv()
import os
from typing import List

class Settings:
    # Database Configuration
    MONGO_HOST: str = os.getenv("MONGO_HOST")
    MONGO_PORT: int = int(os.getenv("MONGO_PORT"))
    MONGO_USERNAME: str = os.getenv("MONGO_USERNAME")
    MONGO_PASSWORD: str = os.getenv("MONGO_PASSWORD")
    MONGO_DB_NAME: str = os.getenv("MONGO_DB_NAME")

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 540

    # CORS
    @property
    def ALLOWED_ORIGINS(self) -> List[str]:
        origins = os.getenv("ALLOWED_ORIGINS")
        return [origin.strip() for origin in origins.split(",")]

    @property
    def mongo_url(self) -> str:
        return f"mongodb://{self.MONGO_USERNAME}:{self.MONGO_PASSWORD}@{self.MONGO_HOST}:{self.MONGO_PORT}/?authSource=admin"

settings = Settings()
