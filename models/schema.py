from typing import List
from pydantic import BaseModel

class CriticResponse(BaseModel):
    problems: List[str]
    fixes: List[str]
