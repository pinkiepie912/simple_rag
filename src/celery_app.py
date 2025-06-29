import os
from pathlib import Path

from celery import Celery
from celery.signals import worker_process_init, worker_process_shutdown

from celery_containers import CeleryContainer
from celery_schedule import CELERY_SCHEDULE
from config.config import Config


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


class CeleryApp(Celery):
    container: CeleryContainer


def create_celery_app() -> Celery:
    config = Config()
    container = CeleryContainer()

    container.config.from_pydantic(config)

    tasks_to_wire = _find_task_modules()
    container.wire(modules=tasks_to_wire)

    celery_app = CeleryApp(
        "tasks",
        broker=config.CELERY.BROKER_URL,
        backend=config.CELERY.BACKEND_URL,
        include=tasks_to_wire,
    )

    celery_app.conf.update(
        task_track_started=True,
        task_serializer="msgpack",
        accept_content=["msgpack", "json"],
        result_serializer="msgpack",
        timezone="Asia/Seoul",
        enable_utc=False,
    )

    celery_app.conf.beat_schedule = CELERY_SCHEDULE
    celery_app.container = container

    @worker_process_init.connect(sender=celery_app)
    def init_worker(**kwargs):
        celery_app.container.es_client()

    @worker_process_shutdown.connect(sender=celery_app)
    def shutdown_worker(**kwargs):
        celery_app.container.shutdown_resources()

    return celery_app


celery_app = create_celery_app()
