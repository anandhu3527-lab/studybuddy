from pydantic import BaseModel,Field

class Feedback(BaseModel):
    feed_giver:str
    feed_reciver:str
    feed_score:int
    feed_content:str
    