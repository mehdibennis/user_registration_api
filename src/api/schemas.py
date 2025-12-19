import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreateRequest(BaseModel):
    """Request body for user registration."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"email": "user@example.com", "password": "securePassword123"}
        }
    )

    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(
        ..., min_length=8, description="Password (minimum 8 characters)"
    )


class UserResponse(BaseModel):
    """Response body containing user information."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "user@example.com",
                "is_active": False,
            }
        }
    )

    id: uuid.UUID = Field(..., description="Unique user identifier")
    email: EmailStr = Field(..., description="User's email address")
    is_active: bool = Field(..., description="Whether the account is activated")


class ActivationRequest(BaseModel):
    """Request body for account activation."""

    model_config = ConfigDict(json_schema_extra={"example": {"code": "1234"}})

    code: str = Field(
        ...,
        min_length=4,
        max_length=4,
        pattern=r"^\d{4}$",
        description="4-digit activation code received by email",
    )


class ErrorResponse(BaseModel):
    """Standard error response."""

    model_config = ConfigDict(
        json_schema_extra={"example": {"detail": "Error description"}}
    )

    detail: str = Field(..., description="Error message")
