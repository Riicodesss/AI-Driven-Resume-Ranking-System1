from pydantic import BaseModel
from typing import List, Optional

class JDInput(BaseModel):
    name: str
    jobDescription: str
    mustHave: List[str]
    goodToHave: List[str]
    experience: str
    certifications: List[str]
    candidateType: Optional[str] = "experienced"