# The Database Layer [cite: 38]
import sqlite3
import logging
from datetime import datetime
from typing import Optional, List, Tuple

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        """
        Initializes the table if it doesn't exist.
        State Tracking:
        - PENDING: Found in folder, waiting for action.
        - PROCESSING: Currently being analyzed.
        - SUCCESS: PO found, ready for merge.
        - FAILED: Technical error (crash, permission issue).
        - MANUAL_REVIEW: Logic error (No PO found after all retries).
        """
        query = """
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT UNIQUE NOT NULL,
            filename TEXT NOT NULL,
            doc_type TEXT NOT NULL,
            status TEXT DEFAULT 'PENDING',
            po_number TEXT,
            error_message TEXT,
            retry_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        with self._get_connection() as conn:
            conn.execute(query)
            # Create an index on PO Number for fast grouping later
            conn.execute("CREATE INDEX IF NOT EXISTS idx_po_number ON files(po_number);")

    def register_file(self, file_path: str, filename: str, doc_type: str) -> bool:
        """
        Adds a new file to the queue. Returns False if it already exists.
        """
        try:
            with self._get_connection() as conn:
                conn.execute(
                    "INSERT INTO files (file_path, filename, doc_type) VALUES (?, ?, ?)",
                    (file_path, filename, doc_type)
                )
            return True
        except sqlite3.IntegrityError:
            # File already being tracked, ignore
            return False

    def update_status(self, file_path: str, status: str, po_number: Optional[str] = None, error: Optional[str] = None):
        """
        Updates the state of a file (e.g., transitions from PROCESSING -> SUCCESS).
        """
        query = """
        UPDATE files 
        SET status = ?, po_number = COALESCE(?, po_number), error_message = ?, updated_at = ?
        WHERE file_path = ?
        """
        with self._get_connection() as conn:
            conn.execute(query, (status, po_number, error, datetime.now(), file_path))

    def get_pending_files(self) -> List[Tuple[str, str, str]]:
        """
        Fetches the next batch of work (file_path, doc_type, status).
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT file_path, doc_type, status FROM files WHERE status = 'PENDING'"
            )
            return cursor.fetchall()

    def get_mergeable_bundles(self):
        """
        The 'Reducer' Logic:
        Finds all PO numbers that have a complete set of documents (or at least >1).
        Returns a dictionary grouping files by PO Number.
        """
        with self._get_connection() as conn:
            # Get all successfully processed files, grouped by PO
            cursor = conn.execute(
                "SELECT po_number, file_path, doc_type FROM files WHERE status = 'SUCCESS' AND po_number IS NOT NULL"
            )
            rows = cursor.fetchall()
        
        # Group in Python
        bundles = {}
        for po, path, type_ in rows:
            if po not in bundles:
                bundles[po] = []
            bundles[po].append({'path': path, 'type': type_})
        
        return bundles