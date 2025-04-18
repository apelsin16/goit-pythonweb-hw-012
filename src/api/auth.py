from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.schemas import UserCreate, Token, User, RequestEmail
from src.services.auth import create_access_token, get_email_from_token, create_reset_token, decode_reset_token
from src.services.hash import Hash
from src.services.mail import send_email, send_reset_password_email
from src.services.users import UserService

from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="src/services/templates")

router = APIRouter(prefix="/auth", tags=["auth"])


# Реєстрація користувача
@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register_user(
        user_data: UserCreate,
        background_tasks: BackgroundTasks,
        request: Request,
        db: Session = Depends(get_db),
):
    user_service = UserService(db)

    email_user = await user_service.get_user_by_email(user_data.email)
    if email_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Користувач з таким email вже існує",
        )

    username_user = await user_service.get_user_by_username(user_data.username)
    if username_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Користувач з таким іменем вже існує",
        )
    user_data.password = Hash().get_password_hash(user_data.password)
    new_user = await user_service.create_user(user_data)

    background_tasks.add_task(
        send_email, new_user.email, new_user.username, request.base_url
    )

    return new_user


# Логін користувача
@router.post("/login", response_model=Token)
async def login_user(
        form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user_service = UserService(db)
    user = await user_service.get_user_by_username(form_data.username)
    if not user or not Hash().verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неправильний логін або пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.confirmed:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Електронна адреса не підтверджена",
        )
    access_token = await create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/confirmed_email/{token}")
async def confirmed_email(token: str, db: Session = Depends(get_db)):
    email = await get_email_from_token(token)
    user_service = UserService(db)
    user = await user_service.get_user_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error"
        )
    if user.confirmed:
        return {"message": "Ваша електронна пошта вже підтверджена"}
    await user_service.confirmed_email(email)
    return {"message": "Електронну пошту підтверджено"}


@router.post("/request_email")
async def request_email(
        body: RequestEmail,
        background_tasks: BackgroundTasks,
        request: Request,
        db: Session = Depends(get_db),
):
    user_service = UserService(db)
    user = await user_service.get_user_by_email(body.email)

    if user.confirmed:
        return {"message": "Ваша електронна пошта вже підтверджена"}
    if user:
        background_tasks.add_task(
            send_email, user.email, user.username, request.base_url
        )
    return {"message": "Перевірте свою електронну пошту для підтвердження"}


@router.post("/send-reset-password-token")
async def send_reset_password_token(
        body: RequestEmail,
        background_tasks: BackgroundTasks,
        request: Request,
        db: Session = Depends(get_db),
):
    user_service = UserService(db)
    user = await user_service.get_user_by_email(body.email)

    if user is None:
        raise HTTPException(status_code=404, detail="Користувача з таким email не знайдено")

    background_tasks.add_task(
        send_reset_password_email, user.email, user.username, str(request.base_url)
    )
    return {"message": "Посилання для скидання пароля було надіслано на вашу електронну пошту"}


@router.get("/reset-password")
async def reset_password_form(request: Request, token: str):
    try:
        # Перевірка токену
        email = decode_reset_token(token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    # Повертаємо форму для скидання пароля
    return templates.TemplateResponse("reset_password_form.html", {"request": request, "token": token})


@router.post("/reset-password")
async def reset_password(
        token: str = Form(...),
        new_password: str = Form(...),
        db: AsyncSession = Depends(get_db),
):
    try:
        email = decode_reset_token(token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user_service = UserService(db)
    hashed_password = Hash().get_password_hash(new_password)
    await user_service.update_password(email, hashed_password)
    return {"msg": "Password updated successfully"}
