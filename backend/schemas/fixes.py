from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Any, Dict


class FixGenerateRequest(BaseModel):
    website_id: Optional[int] = None
    scan_id: Optional[int] = None
    issue_ids: Optional[List[int]] = None
    fix_type: Optional[str] = None

    model_config = ConfigDict(frozen=True, extra="allow")


class FixGenerateResponse(BaseModel):
    fix_id: Optional[int] = None
    status: str
    message: Optional[str] = None
    fixes: Optional[List[Dict[str, Any]]] = None

    model_config = ConfigDict(frozen=True, extra="allow")


class FixApplyRequest(BaseModel):
    fix_id: int
    confirm: bool = False

    model_config = ConfigDict(frozen=True, extra="allow")


class FixApplyResponse(BaseModel):
    fix_id: int
    status: str
    applied_at: Optional[str] = None
    message: Optional[str] = None

    model_config = ConfigDict(frozen=True, extra="allow")


class FixHistoryItem(BaseModel):
    fix_id: int
    website_id: Optional[int] = None
    fix_type: Optional[str] = None
    status: str
    created_at: Optional[str] = None
    applied_at: Optional[str] = None

    model_config = ConfigDict(frozen=True, extra="allow")
