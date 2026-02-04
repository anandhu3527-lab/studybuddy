from pydantic import BaseModel,Field,EmailStr,field_validator
import re
from typing import Optional



class User(BaseModel):
    name:str
    subjects: list[str]
    study_time:str
    year:int
    study_mode:str
    course:str
    interested_field:str
    email: EmailStr
    gender:str
    number_permission:str
    number:str = Field(
        pattern=r"^[6-9]\d{9}$"
    )
    password:str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")

        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain uppercase letter")

        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain lowercase letter")

        if not re.search(r"\d", v):
            raise ValueError("Password must contain a number")

        if not re.search(r"[!@#$%^&*()]", v):
            raise ValueError("Password must contain special character")

        return v


class filter(BaseModel):
    subject:Optional[ list[str] ]=None
    study_mode:Optional[str]=None
    year:Optional[int]=0
    course:Optional[str]=None
    interested_field:Optional[str]=None



class update(BaseModel):

    subject:Optional[ list[str] ]=None
    study_mode:Optional[str]=None
    study_time:Optional[str]=None,
    year:Optional[int]=None
    course:Optional[str]=None
    interested_field:Optional[str]=None
    number_permission:Optional[str]=None
