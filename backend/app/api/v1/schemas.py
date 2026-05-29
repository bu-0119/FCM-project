from uuid import UUID

from pydantic import BaseModel, field_validator, ConfigDict


class BaseSchema(BaseModel):
    """Shared base that auto-converts UUID to str from ORM objects."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    @field_validator("id", "user_id", "post_id", "session_id", mode="before", check_fields=False)
    @classmethod
    def _coerce_uuid(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v
