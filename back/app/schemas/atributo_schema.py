from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date


class AtributoSchema(BaseModel):
    nombre: str
    valor: str