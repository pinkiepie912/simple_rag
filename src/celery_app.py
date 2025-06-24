import os
from pathlib import Path
from celery import Celery

from containers import Container


def _find_task_modules() -> list[str]:
    src_path = Path(__file__).parent

    task_modules = []
    for tasks_dir in src_path.glob("**/tasks"):
        for task_file in tasks_dir.glob("*.py"):
            if task_file.name == "__init__.py":
                continue
            module_path = task_file.relative_to(src_path).with_suffix("")
            import_path = str(module_path).replace(os.path.sep, ".")
            task_modules.append(import_path)

    print(f"Discovered Celery task modules (PYTHONPATH=src): {task_modules}")
    return task_modules


def create_celery_app() -> Celery:
    container = Container()
    config = container.config()

    celery_app = Celery(
        "tasks",
        broker=config.CELERY_BROKER_URL,
        backend=config.CELERY_BACKEND_URL,
        include=_find_task_modules(),
    )

    celery_app.conf.update(
        task_track_started=True,
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="Asia/Seoul",
        enable_utc=False,
    )

    return celery_app


celery_app = create_celery_app()
