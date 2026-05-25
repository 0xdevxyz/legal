from pydantic import BaseModel, field_validator
from typing import Optional


class JWTUserClaim(BaseModel):
    id: int
    user_id: str
    email: Optional[str] = None
    role: Optional[str] = None
    jti: str
    iat: int
    nbf: int
    exp: int
    iss: Optional[str] = None
    aud: Optional[str] = None
    type: Optional[str] = None

    @field_validator("id", mode="before")
    @classmethod
    def coerce_id_to_int(cls, v):
        try:
            return int(v)
        except (TypeError, ValueError):
            raise ValueError(f"id must be coercible to int, got: {v!r}")

    @field_validator("user_id", mode="before")
    @classmethod
    def coerce_user_id_to_str(cls, v):
        return str(v)

    model_config = {"extra": "allow"}
