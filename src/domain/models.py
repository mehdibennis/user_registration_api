import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    id: uuid.UUID
    email: str
    password_hash: str
    is_active: bool
    activation_code: Optional[str] = None
    activation_code_expires_at: Optional[datetime] = None
