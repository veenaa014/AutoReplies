from pydantic import BaseSettings


class Settings(BaseSettings):
    slack_oauth_token: str
    message_file_name: str

    class Config:
        env_file = ".env"
