from pydantic import BaseModel

class Email(BaseModel):
    senderEmail: str
    description: str
    subject: str
    senderName: str
    url:str