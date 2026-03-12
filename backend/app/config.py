from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    secret_key: str

    xero_client_id: str = ""
    xero_client_secret: str = ""
    xero_redirect_uri: str = "http://localhost:8000/api/xero/callback"

    myob_client_id: str = ""
    myob_client_secret: str = ""
    myob_redirect_uri: str = "http://localhost:8000/api/myob/callback"

    frontend_url: str = "http://localhost:5173"

    class Config:
        env_file = ".env"


settings = Settings()
