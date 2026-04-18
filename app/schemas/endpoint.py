from pydantic import BaseModel

class EndpointOut(BaseModel):
    endpoint_id: int
    url: str

    class Config:
        from_attributes = True