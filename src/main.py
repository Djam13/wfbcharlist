import os
from fastapi import FastAPI, HTTPException
from fastapi_login import LoginManager
from fastapi.routing import APIRouter
#from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Boolean, String, UUID
from pydantic import BaseModel, EmailStr, field_validator
import settings
import uuid
import re
import uvicorn


engine = create_async_engine(settings.DATABASE_URL)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    is_active = Column(Boolean(), default=True)


class UserDAL:
    """Data Access Layer for user object"""
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
    
    async def create_user(self, name: str, email: str) -> User:
        new_user = User(name = name,
                        email = email)
        self.db_session.add(new_user)
        await self.db_session.flush()
        return new_user
    

LETTER_PATTERN = re.compile(r"^[а-яА-Яa-zA-Z\-]+$")

class TunedModel(BaseModel):
    class Config:
        """tells pydantic to convert even non dict obj to json"""

        from_attributes = True

class ShowUser(TunedModel):
    user_id: uuid.UUID
    name: str
    email: EmailStr
    is_active: bool


class UserCreate(BaseModel):
    name: str
    email: EmailStr

    @field_validator("name")
    def validate_name(cls, value):
        if not LETTER_PATTERN.match(value):
            raise HTTPException(
                status_code=422, detail="Name should contains only letters"
            )
        return value




SECRET = settings.SECRET
app = FastAPI(title="wfb_api")
manager = LoginManager(SECRET, '/login')

user_router = APIRouter()

async def _create_new_user(body: UserCreate) -> ShowUser:
    async with async_session() as session:
        async with session.begin():
            user_dal = UserDAL(session)
            user = await user_dal.create_user(
                name=body.name,
                email=body.email,
            )
            return ShowUser(
                user_id=user.user_id,
                name=user.name,
                email=user.email,
                is_active=user.is_active,
            )


@user_router.post("/", response_model=ShowUser)
async def create_user(body: UserCreate) -> ShowUser:
    return await _create_new_user(body)

# create the instance for the routes
main_api_router = APIRouter()

# set routes to the app instance
main_api_router.include_router(user_router, prefix="/user", tags=["user"])
app.include_router(main_api_router)

if __name__ == "__main__":
    # run app on the host and port
    uvicorn.run(app, host="0.0.0.0", port=8000)