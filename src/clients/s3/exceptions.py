from base.api_exception import APIException


class FailToGeneratePresignedUrlError(APIException):
    status_code = 500
    code = "PRESIGNED_URL_GENERATION_FAILED"
    detail = "Failed to generate presigned URL"
    description = "파일 업로드 URL 생성에 실패했습니다."
    example = {"code": code, "detail": detail}


class FailToDownloadError(APIException):
    status_code = 500
    code = "DOWNLOAD_FAILED"
    detail = "Failed to download file"
    description = "파일 다운로드에 실패했습니다."
    example = {"code": code, "detail": detail}
