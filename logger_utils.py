import logging
import sys
from datetime import datetime
from typing import Any, Dict

class Logger:
    def __init__(self, name: str, level=logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def info(self, message: str):
        self.logger.info(message)
    
    def error(self, message: str):
        self.logger.error(message)
    
    def warning(self, message: str):
        self.logger.warning(message)
    
    def debug(self, message: str):
        self.logger.debug(message)

_default_logger = Logger(__name__)

def log_section(title: str, width: int = 60):
    _default_logger.info("=" * width)
    _default_logger.info(title)
    _default_logger.info("=" * width)

def log_starting(task: str):
    _default_logger.info(f"Starting {task}...")

def log_complete(task: str):
    _default_logger.info(f"✓ {task} complete")

def log_success(message: str):
    _default_logger.info(f"✓ {message}")

def log_error(message: str):
    _default_logger.error(f"✗ {message}")

def log_warning(message: str):
    _default_logger.warning(f"⚠ {message}")

def log_info(message: str):
    _default_logger.info(message)

def log_processing(item: str):
    _default_logger.info(f"Processing {item}...")

def log_initialized(component: str):
    _default_logger.info(f"✓ {component} initialized")

def log_connecting(target: str):
    _default_logger.info(f"Connecting to {target}...")

def log_connected(target: str):
    _default_logger.info(f"✓ Connected to {target}")

def log_query(query_text: str):
    _default_logger.info(f"Query: {query_text}")

def log_executing(action: str):
    _default_logger.info(f"Executing {action}...")

def log_result_count(count: int, item_type: str = "results"):
    _default_logger.info(f"✓ Found {count} {item_type}")

def log_chunk_progress(chunk_num: int, inserted: int, total: int):
    _default_logger.info(f"Chunk {chunk_num}: Inserted {inserted} records. Total: {total}")

def log_data_stats(message: str, stats: Dict[str, Any]):
    _default_logger.info(message)
    for key, value in stats.items():
        _default_logger.info(f"  {key}: {value}")

def log_cleaning_data():
    _default_logger.info("Cleaning data...")

def log_data_cleaned(shape: tuple):
    _default_logger.info(f"✓ Data cleaned. Shape: {shape}")

def log_creating_indexes():
    _default_logger.info("Creating indexes...")

def log_indexes_created():
    _default_logger.info("✓ Indexes created")

def log_load_summary(total: int, inserted: int, failed: int, duration: float):
    log_section("DATA LOAD COMPLETE")
    _default_logger.info(f"Total Records Processed: {total}")
    _default_logger.info(f"Successfully Inserted: {inserted}")
    _default_logger.info(f"Failed: {failed}")
    _default_logger.info(f"Duration: {duration:.2f} seconds")
    _default_logger.info("=" * 60)

def log_generating(item: str):
    _default_logger.info(f"Generating {item}...")

def log_analyzing(item: str):
    _default_logger.info(f"Analyzing {item}...")
