from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PORT: int = 8000
    ENV: str = "development"
    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379/0"
    JWT_SECRET: str
    JWT_EXPIRE: str = "15m"
    JWT_REFRESH_EXPIRE: str = "7d"
    GROQ_API_KEY: str
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    RESEND_API_KEY: str
    EMAIL_FROM: str = "noreply@healthcoach.app"
    EXERCISE_DB_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"
    FIREBASE_SERVICE_ACCOUNT_PATH: str = ""
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""

    class Config:
        env_file = ".env"

settings = Settings()
