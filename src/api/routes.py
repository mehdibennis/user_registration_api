from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies import get_current_user_email, get_user_service
from src.api.schemas import (
    ActivationRequest,
    ErrorResponse,
    UserCreateRequest,
    UserResponse,
)
from src.domain.exceptions import (
    ActivationCodeExpiredError,
    InvalidActivationCodeError,
    UserAlreadyActivatedError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from src.service.user_service import UserService

router = APIRouter(tags=["Users"])


@router.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="""
    Create a new user account with email and password.
    
    A 4-digit activation code will be sent to the provided email address.
    The code expires after 1 minute.
    """,
    responses={
        201: {"description": "User created successfully"},
        409: {"model": ErrorResponse, "description": "User already exists"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    },
)
async def register_user(
    request: UserCreateRequest, service: UserService = Depends(get_user_service)
):
    try:
        user = await service.register_user(request.email, request.password)
        return UserResponse(id=user.id, email=user.email, is_active=user.is_active)
    except UserAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post(
    "/users/activate",
    response_model=UserResponse,
    summary="Activate user account",
    description="""
    Activate a user account using the 4-digit code received by email.
    
    **Authentication**: Basic Auth (email:password)
    
    The activation code expires after 1 minute. If expired, use the 
    `/users/regenerate-code` endpoint to get a new code.
    """,
    responses={
        200: {"description": "Account activated successfully"},
        400: {"model": ErrorResponse, "description": "Invalid or expired code"},
        401: {"model": ErrorResponse, "description": "Invalid credentials"},
        409: {"model": ErrorResponse, "description": "Account already activated"},
    },
)
async def activate_user(
    request: ActivationRequest,
    email: str = Depends(get_current_user_email),
    service: UserService = Depends(get_user_service),
):
    try:
        user = await service.activate_user(email, request.code)
        return UserResponse(id=user.id, email=user.email, is_active=user.is_active)
    except (
        UserNotFoundError,
        InvalidActivationCodeError,
        ActivationCodeExpiredError,
    ) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except UserAlreadyActivatedError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post(
    "/users/regenerate-code",
    response_model=UserResponse,
    summary="Regenerate activation code",
    description="""
    Generate a new 4-digit activation code for a non-activated account.
    
    **Authentication**: Basic Auth (email:password)
    
    Use this endpoint if your previous activation code has expired.
    A new code will be sent to your email address.
    """,
    responses={
        200: {"description": "New activation code sent"},
        401: {"model": ErrorResponse, "description": "Invalid credentials"},
        404: {"model": ErrorResponse, "description": "User not found"},
        409: {"model": ErrorResponse, "description": "Account already activated"},
    },
)
async def regenerate_code(
    email: str = Depends(get_current_user_email),
    service: UserService = Depends(get_user_service),
):
    try:
        user = await service.regenerate_activation_code(email)
        return UserResponse(id=user.id, email=user.email, is_active=user.is_active)
    except UserNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except UserAlreadyActivatedError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
