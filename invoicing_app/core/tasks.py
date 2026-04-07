"""
Celery tasks for core operations.

These tasks run asynchronously in the background:
- Database backup creation
- System maintenance tasks
- Scheduled cleanup operations
"""

from celery import shared_task
from django.conf import settings
from django.db import connection
from pathlib import Path
import subprocess
import gzip
import shutil
from datetime import datetime
import time
import sqlite3
import logging

logger = logging.getLogger(__name__)


@shared_task(name="invoicing_app.core.tasks.create_database_backup")
def create_database_backup(user_id=None):
    """
    Create a compressed database backup asynchronously.

    This task:
    - Creates a database dump (mysqldump for MySQL, SQL dump for SQLite)
    - Compresses the backup with gzip
    - Saves backup metadata to database
    - Returns backup info

    Args:
        user_id: User ID who initiated the backup (for audit trail)

    Returns:
        dict: Backup status and details
    """
    from invoicing_app.core.models import Backup
    from django.contrib.auth.models import User

    try:
        logger.info("Starting database backup task...")

        # Get user if provided (for audit trail)
        created_by = None
        if user_id:
            try:
                created_by = User.objects.get(id=user_id)
            except User.DoesNotExist:
                pass

        # Create backups directory if it doesn't exist
        backup_dir = Path(settings.BASE_DIR) / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        backup_filename = f"invoice_backup_{timestamp}.sql"
        backup_path = backup_dir / backup_filename

        start_time = time.time()
        db_config = connection.settings_dict

        logger.info(f"Creating backup file: {backup_path}")

        # Create database dump based on database type
        if "mysql" in db_config.get("ENGINE", "").lower():
            # MySQL dump
            logger.info("Using mysqldump for MySQL database")
            cmd = [
                "mysqldump",
                "-h",
                db_config.get("HOST", "localhost"),
                "-u",
                db_config.get("USER", "root"),
            ]

            # Only add password if it exists
            if db_config.get("PASSWORD"):
                cmd.append(f'-p{db_config.get("PASSWORD")}')

            cmd.append(db_config.get("NAME"))

            with open(backup_path, "w", encoding="utf-8") as f:
                result = subprocess.run(
                    cmd, stdout=f, stderr=subprocess.PIPE, check=True
                )
                if result.returncode != 0:
                    raise Exception(f"mysqldump failed: {result.stderr.decode()}")
        else:
            # SQLite dump
            logger.info("Using SQLite dump for SQLite database")
            db_path = db_config.get("NAME")
            conn = sqlite3.connect(db_path)
            with open(backup_path, "w", encoding="utf-8") as f:
                for line in conn.iterdump():
                    f.write(f"{line}\n")
            conn.close()

        logger.info("Database dump created, compressing...")

        # Compress the backup
        duration = int(time.time() - start_time)
        compressed_path = Path(str(backup_path) + ".gz")

        with open(backup_path, "rb") as f_in:
            with gzip.open(compressed_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)

        # Delete uncompressed version
        backup_path.unlink()

        # Get file size
        file_size = compressed_path.stat().st_size
        file_size_mb = file_size / (1024 * 1024)

        logger.info(
            f"Backup compressed: {compressed_path.name} ({file_size_mb:.2f} MB)"
        )

        # Create backup record
        backup_record = Backup.objects.create(
            file_name=compressed_path.name,
            file_path=str(compressed_path),
            file_size=file_size,
            backup_type="database",
            duration_seconds=duration,
            status="complete",
            created_by=created_by,
            is_compressed=True,
            is_automated=False,
            notes=f'Asynchronous backup created by {created_by.username if created_by else "System"}',
        )

        logger.info(f"Backup record created: {backup_record.file_name}")

        return {
            "success": True,
            "message": f"✅ Backup created successfully: {compressed_path.name} ({file_size_mb:.1f} MB)",
            "file_name": compressed_path.name,
            "file_size": file_size_mb,
            "duration": duration,
            "backup_id": backup_record.id,
        }

    except Exception as e:
        logger.error(f"Backup task failed: {str(e)}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Backup failed: {str(e)}",
            "error": str(e),
        }


@shared_task(name="invoicing_app.core.tasks.cleanup_old_backups")
def cleanup_old_backups(days=30):
    """
    Delete backup files older than specified days.

    Scheduled task that runs to manage backup storage.

    Args:
        days: Number of days to keep backups (default: 30)
    """
    from invoicing_app.core.models import Backup
    from datetime import timedelta

    try:
        logger.info(f"Starting backup cleanup: keeping backups from last {days} days")

        cutoff_date = datetime.now() - timedelta(days=days)

        # Find old backups
        old_backups = Backup.objects.filter(created_at__lt=cutoff_date)

        deleted_count = 0
        deleted_size = 0

        for backup in old_backups:
            try:
                backup_path = Path(backup.file_path)
                if backup_path.exists():
                    file_size = backup_path.stat().st_size
                    backup_path.unlink()
                    deleted_size += file_size
                    logger.info(f"Deleted backup: {backup.file_name}")

                backup.delete()
                deleted_count += 1
            except Exception as e:
                logger.error(f"Could not delete backup {backup.file_name}: {str(e)}")

        deleted_size_mb = deleted_size / (1024 * 1024)
        logger.info(
            f"Cleanup complete: Deleted {deleted_count} backups ({deleted_size_mb:.2f} MB)"
        )

        return {
            "success": True,
            "deleted_count": deleted_count,
            "deleted_size_mb": deleted_size_mb,
        }

    except Exception as e:
        logger.error(f"Backup cleanup failed: {str(e)}", exc_info=True)
        return {"success": False, "error": str(e)}
