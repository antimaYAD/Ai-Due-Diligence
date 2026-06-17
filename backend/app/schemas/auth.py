from pydantic import BaseModel, EmailStr, field_validator


def validate_bcrypt_password(password: str) -> str:
    if len(password.encode("utf-8")) > 72:
        raise ValueError("Password must be 72 bytes or fewer")
    return password


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    organization_id: str | None = None

    @field_validator("password")
    @classmethod
    def password_within_bcrypt_limit(cls, password: str) -> str:
        return validate_bcrypt_password(password)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_within_bcrypt_limit(cls, password: str) -> str:
        return validate_bcrypt_password(password)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: str
    name: str
    email: str
    role: str
    organization_id: str | None

    class Config:
        from_attributes = True
