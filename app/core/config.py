from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SECRET_KEY:str
    ALGORITHM:str
    ACCESS_TOKEN_EXPIRE_MINUTES:int
    POSTGRES_USER:str
    POSTGRES_PASSWORD:str
    POSTGRES_SERVER:str
    POSTGRES_PORT:str
    POSTGRES_DB:str
    GOOGLE_CLIENT_ID:str
    GOOGLE_CLIENT_SECRET:str

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding="utf-8",
        extra="ignore",
    )


    @property
    def database_url(self)->str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"f"{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"



settings = Settings()