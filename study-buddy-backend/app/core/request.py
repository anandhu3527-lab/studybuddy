from pydantic import BaseModel

class Request(BaseModel):
    sender_id:str
    reciver_id:str
