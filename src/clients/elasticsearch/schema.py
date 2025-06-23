from pydantic import BaseModel, Field
from uuid import UUID


class DocMetadata(BaseModel):
    ext: str = Field(..., description="File extension of the document")


class DocSchema(BaseModel):
    id: UUID = Field(
        ..., description="Unique identifier for the document schema", alias="_id"
    )
    doc_id: UUID = Field(..., description="Unique identifier for the document")
    order: int = Field(..., description="Order of the document")
    content: str = Field(..., description="Content of the document")

    @classmethod
    def create_map(cls, analyzer: str):
        return {
            "doc_id": {"type": "keyword"},
            "order": {"type": "integer"},
            "content": {"type": "text", "analyzer": analyzer},
            "metadata": {
                "type": "object",
                "properties": {
                    "ext": {
                        "type": "keyword",
                    }
                },
            },
        }
