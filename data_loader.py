import pandas as pd
from typing import Dict, Any
from datetime import datetime
from logger_utils import log_cleaning_data, log_data_cleaned, log_starting, log_chunk_progress, log_load_summary, log_creating_indexes, log_success, log_error, log_warning, log_info, log_section

from database import MongoDBManager
from config import Config

class DataLoader:
    def __init__(self):
        self.db_manager = MongoDBManager()
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        log_cleaning_data()
        df_clean = df.copy()
        date_columns = ['Creation Date', 'Purchase Date']
        for col in date_columns:
            if col in df_clean.columns:
                df_clean[col] = pd.to_datetime(df_clean[col], errors='coerce')
                df_clean[col] = df_clean[col].apply(
                    lambda x: x.isoformat() if pd.notna(x) and x is not None else None
                )
        numeric_columns = ['Quantity', 'Unit Price', 'Total Price']
        for col in numeric_columns:
            if col in df_clean.columns:
                if df_clean[col].dtype == 'object':
                    df_clean[col] = df_clean[col].str.replace('$', '', regex=False)
                    df_clean[col] = df_clean[col].str.replace(',', '', regex=False)
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
                df_clean[col] = df_clean[col].where(pd.notnull(df_clean[col]), None)
        df_clean = df_clean.where(pd.notnull(df_clean), None)
        log_data_cleaned(df_clean.shape)
        return df_clean
    
    def load_csv_to_mongodb(
        self, 
        file_path: str, 
        chunk_size: int = 10000,
        max_records: int = None
    ) -> Dict[str, Any]:
        log_starting(f"data load from: {file_path}")
        stats = {
            "total_records": 0,
            "inserted_records": 0,
            "failed_records": 0,
            "start_time": datetime.now()
        }
        try:
            existing_count = self.db_manager.collection.count_documents({})
            if existing_count > 0:
                log_warning(
                    f"Collection already contains {existing_count} documents. "
                    "Will continue loading remaining data..."
                )
            chunk_iter = pd.read_csv(file_path, chunksize=chunk_size)
            for i, chunk in enumerate(chunk_iter):
                if max_records and stats["total_records"] >= max_records:
                    log_info(f"Reached maximum records limit: {max_records}")
                    break
                chunk_clean = self.clean_data(chunk)
                records = chunk_clean.to_dict('records')
                if max_records:
                    remaining = max_records - stats["total_records"]
                    records = records[:remaining]
                try:
                    result = self.db_manager.collection.insert_many(records)
                    inserted = len(result.inserted_ids)
                    stats["inserted_records"] += inserted
                    stats["total_records"] += len(records)
                    log_chunk_progress(i+1, inserted, stats['total_records'])
                except Exception as e:
                    log_error(f"Error inserting chunk {i+1}: {e}")
                    stats["failed_records"] += len(records)
            self._create_indexes()
            stats["end_time"] = datetime.now()
            stats["duration"] = (stats["end_time"] - stats["start_time"]).total_seconds()
            stats["status"] = "success"
            log_load_summary(
                stats['total_records'],
                stats['inserted_records'],
                stats['failed_records'],
                stats['duration']
            )
            return stats
        except Exception as e:
            log_error(f"Error loading data: {e}")
            stats["status"] = "error"
            stats["error_message"] = str(e)
            return stats
    
    def _create_indexes(self):
        log_creating_indexes()
        indexes = [
            ("Creation Date", 1),
            ("Fiscal Year", 1),
            ("Department Name", 1),
            ("Supplier Name", 1),
            ("Acquisition Method", 1),
            ("Total Price", 1)
        ]
        for field, order in indexes:
            try:
                self.db_manager.collection.create_index([(field, order)])
                log_success(f"Created index on: {field}")
            except Exception as e:
                log_warning(f"Could not create index on {field}: {e}")
    
    def verify_data_load(self) -> Dict[str, Any]:
        log_starting("verification")
        stats = self.db_manager.get_collection_stats()
        sample_docs = self.db_manager.get_sample_documents(3)
        verification = {
            "total_documents": stats["total_documents"],
            "sample_documents": sample_docs,
            "collection_name": stats["collection_name"]
        }
        log_success(f"Verification complete. Found {stats['total_documents']} documents")
        return verification
    
    def close(self):
        self.db_manager.close()

def main():
    log_section("CA PROCUREMENT DATA LOADER")
    loader = DataLoader()
    try:
        stats = loader.load_csv_to_mongodb(
            file_path=Config.DATA_FILE,
            chunk_size=10000,
            max_records=None
        )
        if stats.get("status") in ["success", "skipped"]:
            verification = loader.verify_data_load()
            log_section("VERIFICATION RESULTS")
            log_info(f"Total Documents: {verification['total_documents']}")
            log_info("Sample Document (first record):")
            if verification['sample_documents']:
                sample = verification['sample_documents'][0]
                for key, value in list(sample.items())[:10]:
                    log_info(f"  {key}: {value}")
    except Exception as e:
        log_error(f"Failed to load data: {e}")
        raise
    finally:
        loader.close()

if __name__ == "__main__":
    main()
