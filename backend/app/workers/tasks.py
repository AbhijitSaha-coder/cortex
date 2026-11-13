from app.workers.celery_app import celery_app
from app.db.session import SessionLocal
from app.services.ingestion.pipeline import IngestionPipeline
from app.core.logging import logger


@celery_app.task(bind=True, max_retries=2, default_retry_delay=5)
def ingest_file_task(self, document_id: str, user_id: str, file_path: str, file_name: str, file_type: str):
    """Celery background task for asynchronous file ingestion."""
    logger.info(f"[Task] Ingesting file for doc: {document_id}")
    db = SessionLocal()
    try:
        with open(file_path, "rb") as f:
            file_bytes = f.read()

        pipeline = IngestionPipeline(db)
        pipeline.process_file_content(
            document_id=document_id,
            user_id=user_id,
            file_bytes=file_bytes,
            file_name=file_name,
            file_type=file_type,
        )
        return {"status": "success", "document_id": document_id}
    except Exception as exc:
        logger.error(f"[Task Error] Ingestion failed: {exc}")
        db.close()
        raise self.retry(exc=exc)
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=2, default_retry_delay=5)
def ingest_url_task(self, document_id: str, user_id: str, url: str):
    """Celery background task for asynchronous web URL ingestion."""
    logger.info(f"[Task] Ingesting URL for doc: {document_id} ({url})")
    db = SessionLocal()
    try:
        pipeline = IngestionPipeline(db)
        pipeline.process_url(
            document_id=document_id,
            user_id=user_id,
            url=url,
        )
        return {"status": "success", "document_id": document_id}
    except Exception as exc:
        logger.error(f"[Task Error] URL ingestion failed: {exc}")
        db.close()
        raise self.retry(exc=exc)
    finally:
        db.close()

