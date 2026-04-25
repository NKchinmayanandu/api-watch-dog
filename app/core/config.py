from pydantic_settings import BaseSettings,SettingsConfigDict

class Setting(BaseSettings):
    TELEGRAM_BOT_TOKEN:str
    DATABASE_URL:str
    SECRET_KEY:str
    ALGORITHM:str
    ACCESS_TOKEN_EXPIRE_MINUTES:int
    model_config = SettingsConfigDict(env_file=".env")

settings = Setting()
