from base.dto import SnakeToCamelBaseModel

__all__ = ["PresignedUrlMetadata"]


class PresignedUrlMetadata(SnakeToCamelBaseModel):
    doc_id: str
    origin_filename: str
