from pydantic import BaseModel, Field, field_validator


class QueryRequest(BaseModel):
    query: str = Field(min_length=3, max_length=500)

    @field_validator("query")
    @classmethod
    def strip_query(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("query must contain at least 3 characters")
        return v
