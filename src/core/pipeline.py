import time
import logging
import os
from dotenv import load_dotenv # Import this to read the .env file properly
from typing import List, Dict
from pypdf import PdfWriter, PdfReader

# Import our modules
from .database import DatabaseManager
from .file_utils import FileSystemManager
from ..extractors import get_document_info

# Setup Logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class PipelineOrchestrator:
    def __init__(self):
        # 1. Initialize Subsystems
        self.fs = FileSystemManager()
        
        # CORRECTED: Properly get path from env, or default to visible file
        db_path = os.getenv("DB_PATH", "merger_state.db")
        self.db = DatabaseManager(db_path) 
        
        # Define the strict merge order: PO -> DO -> SI
        self.type_priority = {'po': 1, 'do': 2, 'si': 3}

    def run(self):
        """
        The Main Control Loop.
        Runs one full pass of the pipeline.
        """
        logger.info(">>> Starting Pipeline Pass")

        # Step 1: Perception (Scan & Register)
        self._step_scan_inputs()

        # Step 2: Processing (Extract Data)
        self._step_process_files()

        # Step 3: Actuation (Merge Bundles)
        self._step_merge_documents()

        logger.info(">>> Pipeline Pass Completed")

    def _step_scan_inputs(self):
        """
        Scans folders and registers new files in the 'Memory' (DB).
        """
        logger.info("Scanning input directories...")
        # Actuator renames files to standard format
        found_files = self.fs.scan_and_rename()
        
        new_count = 0
        for file_path, filename, doc_type in found_files:
            # Register in DB (returns True if new)
            if self.db.register_file(file_path, filename, doc_type):
                new_count += 1
        
        if new_count > 0:
            logger.info(f"Registered {new_count} new files.")

    def _step_process_files(self):
        """
        Fetches 'PENDING' files and runs the Extraction Tools.
        """
        pending_files = self.db.get_pending_files()
        
        if not pending_files:
            return

        logger.info(f"Processing {len(pending_files)} pending files...")

        for file_path, doc_type, current_status in pending_files:
            try:
                # Update state to PROCESSING
                self.db.update_status(file_path, 'PROCESSING')

                # Call the Toolbox Manager
                doc_info = get_document_info(file_path, doc_type)

                if doc_info.po_number:
                    # Success: We found the "Universe ID"
                    self.db.update_status(file_path, 'SUCCESS', po_number=doc_info.po_number)
                    logger.info(f"✓ Solved: {doc_type.upper()} -> PO: {doc_info.po_number}")
                else:
                    # Failure: Move to Manual Review
                    self.db.update_status(file_path, 'MANUAL_REVIEW', error="No PO Number found")
                    logger.warning(f"⚠ Failed: Could not identify PO for {file_path}")

            except Exception as e:
                logger.error(f"CRITICAL ERROR processing {file_path}: {e}")
                self.db.update_status(file_path, 'FAILED', error=str(e))

    def _step_merge_documents(self):
        """
        Finds completed 'Universes' (PO bundles) and merges them.
        """
        # Ask DB for groups that are ready
        bundles = self.db.get_mergeable_bundles()
        
        for po_number, files in bundles.items():
            # Sort by priority: PO(1) -> DO(2) -> SI(3)
            sorted_files = sorted(
                files, 
                key=lambda x: self.type_priority.get(x['type'], 99)
            )

            try:
                merger = PdfWriter()
                file_paths_used = []

                for file_data in sorted_files:
                    path = file_data['path']
                    # Append to PDF
                    merger.append(path)
                    file_paths_used.append(path)

                # Actuation: Save the file
                output_path = self.fs.save_merged_pdf(merger, po_number)
                logger.info(f"★ MERGED: {po_number} ({len(sorted_files)} docs) -> {output_path}")

                # Update State: Mark these files as 'MERGED'
                for path in file_paths_used:
                    self.db.update_status(path, 'MERGED')
                    self.fs.move_to_archive(path) 

            except Exception as e:
                logger.error(f"Failed to merge bundle for PO {po_number}: {e}")