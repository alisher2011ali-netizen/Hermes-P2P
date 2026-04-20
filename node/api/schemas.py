from pydantic import BaseModel


class MessagePacket(BaseModel):
    to_pubkey: str
    from_pubkey: str
    payload: str
    nonce: str
    signature: str
