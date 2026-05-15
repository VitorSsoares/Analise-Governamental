from pydantic import BaseModel
from typing import Optional

class Parlamentar(BaseModel):
    id: Optional[int] = None
    nome: str
    partido: Optional[str] = None
    uf: Optional[str] = None
    foto_url: Optional[str] = None

    class Config:
        from_attributes = True