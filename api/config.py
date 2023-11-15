from pydantic_settings import BaseSettings

# Environment Variables
class Settings(BaseSettings):
    NAUTICAL_VERSION: str = "0.0.0"
    HTTP_REST_API_USERNAME: str = "admin"
    HTTP_REST_API_PASSWORD: str = "password"