from datetime import timedelta

__all__ = ["CELERY_SCHEDULE"]

CELERY_SCHEDULE = {
    "retry_indexing": {
        "task": "docs.tasks.handle_fail_indexing",
        "schedule": timedelta(minutes=10),
    },
}
