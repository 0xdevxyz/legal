from pydantic import BaseModel, ConfigDict
from typing import Optional, List


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user: dict

    model_config = ConfigDict(frozen=True, extra="forbid")


class RegisterResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user: dict

    model_config = ConfigDict(frozen=True, extra="forbid")


class RefreshResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

    model_config = ConfigDict(frozen=True, extra="forbid")


class MeResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    company: Optional[str] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    onboarding_completed: Optional[bool] = None
    role: Optional[str] = None
    plan_type: Optional[str] = None
    plan_limits: Optional[dict] = None
    active_modules: Optional[List[str]] = None

    model_config = ConfigDict(frozen=True, extra="allow")
