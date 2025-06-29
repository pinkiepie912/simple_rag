import os
import uuid

import pymysql
import pymysql.cursors
from celery import Celery

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

celery_app = Celery(
    "tasks",
    broker=f"redis://{REDIS_HOST}:{REDIS_PORT}/0",
    backend=f"redis://{REDIS_HOST}:{REDIS_PORT}/1",
    task_serializer="msgpack",
    result_serializer="msgpack",
    accept_content=["msgpack"],
)


def lambda_handler(event, _):
    try:
        s3_record = event["Records"][0]["s3"]
        bucket_name = s3_record["bucket"]["name"]
        object_key = s3_record["object"]["key"]
    except (KeyError, IndexError):
        return {"statusCode": 400, "body": "Invalid S3 event format"}

    print(f"File received: s3://{bucket_name}/{object_key}")

    # Extract doc_id from object_key (last part without extension)
    doc_id = uuid.UUID(os.path.splitext(object_key.split("/")[-1])[0]).hex

    # Connect to MySQL
    connection = pymysql.connect(
        host=os.getenv("DB_WRITE_URL", "db"),
        user=os.getenv("DB_WRITE_USER", "root"),
        password=os.getenv("DB_WRITE_PASSWORD", "rag"),
        database=os.getenv("DB_WRITE_NAME", "rag"),
        cursorclass=pymysql.cursors.DictCursor,
    )

    try:
        with connection.cursor() as cursor:
            # Update status to "uploaded" for the given doc_id
            sql = "UPDATE docs SET status = %s WHERE id = %s"
            cursor.execute(sql, ("UPLOADED", doc_id))
            connection.commit()
    finally:
        connection.close()

    celery_app.send_task(
        "docs.tasks.index_docs", args=[{"bucket": bucket_name, "key": object_key}]
    )

    return {"statusCode": 200}
