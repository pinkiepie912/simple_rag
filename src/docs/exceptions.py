from base.api_exception import APIException


class NotAllowedExtensionError(APIException):
    status_code = 400
    code = "NOT_ALLOWED_EXTENSION"
    detail = "Not allowed file extension"
    description = "허용되지 않는 파일 확장자입니다."
    example = {"code": code, "detail": detail}


class DocumentSizeLimitExceededError(APIException):
    status_code = 400
    code = "DOCUMENT_SIZE_LIMIT_EXCEEDED"
    detail = "Document size limit exceeded"
    description = "문서 크기가 제한을 초과했습니다."
    example = {"code": code, "detail": detail}


class FailToGeneratePresignedUrlError(APIException):
    status_code = 500
    code = "PRESIGNED_URL_GENERATION_FAILED"
    detail = "Failed to generate presigned URL"
    description = "파일 업로드 URL 생성에 실패했습니다."
    example = {"code": code, "detail": detail}
