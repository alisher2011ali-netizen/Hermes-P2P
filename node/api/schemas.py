from pydantic import BaseModel
from typing import Optional


class MessagePacket(BaseModel):
    to_pubkey: str
    from_pubkey: str
    msg_type: str = "TEXT"
    payload: str
    file_id: Optional[str] = None
    nonce: str
    signature: str
    timestamp: str
