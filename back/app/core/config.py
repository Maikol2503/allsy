from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str

    GOOGLE_API_KEY: str
    GOOGLE_CX: str
    OPENROUTER_API_KEY: str
    YOUTUBE_API_KEY: str

    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_BUCKET_NAME: str
    AWS_REGION: str

    class Config:
        env_file = ".env"

settings = Settings()
