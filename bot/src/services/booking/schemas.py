from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, Field, model_validator


class User(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    id: int | None = None
    fullname: str | None = None


class SessionAdd(BaseModel):
    date: date
    time: time
    user: User = Field(default_factory=User)


class Session(SessionAdd):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    id: int
    created_at: datetime

    @model_validator(mode='before')
    @classmethod
    def handle_flat_fields(cls, values):
        if isinstance(values, dict):
            if 'user_id' in values and 'fullname' in values:
                if 'user' not in values or not values['user']:
                    values['user'] = {
                        'id': values['user_id'],
                        'fullname': values['fullname']
                    }
        return values
