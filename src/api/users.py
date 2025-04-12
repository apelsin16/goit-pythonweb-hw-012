from fastapi import APIRouter, Depends, Request, UploadFile, File
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.schemas import User
from src.services.auth import get_current_user
from src.conf.config import config as settings
from src.services.users import UserService

import cloudinary
import cloudinary.uploader
import cloudinary.api


router = APIRouter(prefix="/users", tags=["users"])
limiter = Limiter(key_func=get_remote_address)


@router.get("/me", response_model=User, description="No more than 10 requests per minute")
@limiter.limit("5/minute")
async def me(request: Request, user: User = Depends(get_current_user)):
    return user


class UploadFileService:
    def __init__(self, cloud_name: str, api_key: str, api_secret: str):
        self.cloud_name = cloud_name
        self.api_key = api_key
        self.api_secret = api_secret
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret
        )

    def upload_file(self, file: UploadFile, username: str):
        result = cloudinary.uploader.upload(file.file, folder=f'avatars/{username}')
        return result['secure_url']



@router.patch("/avatar", response_model=User)
async def update_avatar_user(
        file: UploadFile = File(),
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
):
    avatar_url = UploadFileService(
        settings.CLD_NAME, settings.CLD_API_KEY, settings.CLD_API_SECRET
    ).upload_file(file, user.username)

    user_service = UserService(db)
    user = await user_service.update_avatar_url(user.email, avatar_url)

    return user
