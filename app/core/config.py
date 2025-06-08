from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Application configuration class.

    Loads environment variables from the .env file using Pydantic's BaseSettings.
    This ensures that all sensitive or environment-specific values are decoupled
    from the source code and loaded dynamically at runtime.
    """
    SECRET_KEY:str
    ALGORITHM:str
    ACCESS_TOKEN_EXPIRE_MINUTES:int


    POSTGRES_USER:str
    POSTGRES_PASSWORD:str
    POSTGRES_SERVER:str
    POSTGRES_PORT:str
    POSTGRES_DB:str

    @property
    def database_url(self)->str:
        return(f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
               f"{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}")
    class Config:
        env_file = ".env"



settings = Settings()