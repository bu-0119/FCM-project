from uuid import UUID

from pydantic import BaseModel, model_validator, ConfigDict


class BaseSchema(BaseModel):
    """Shared base that auto-converts UUID to str from ORM objects."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    @model_validator(mode="before")
    @classmethod
    def _coerce_uuid(cls, data: dict) -> dict:
        if not isinstance(data, dict):
            return data
        for key, value in data.items():
            if isinstance(value, UUID):
                data[key] = str(value)
        return data
