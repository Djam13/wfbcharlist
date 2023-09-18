from envparse import Env

env = Env()

DATABASE_URL = env.str(
    "DATABASE_URL",
    default="postgresql+asyncpg://postgres:postgres@0.0.0.0:5432/postgres" 
)
SECRET = env.str(
    "SECRET_KEY",
    default="123"
)