from pydantic_settings import BaseSettings,SettingsConfigDict

class Setting(BaseSettings):
    TELEGRAM_BOT_TOKEN:str
    TELEGRAM_CHAT_ID:int
    DATABASE_URL:str
    SECRET_KEY:str
    ALGORITHM:str
    ACCESS_TOKEN_EXPIRE_MINUTES:int
    ALLOWED_ORIGINS: str = "*"
    model_config = SettingsConfigDict(env_file=".env")

settings = Setting()
