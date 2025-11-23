from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from typing import List, Dict, Any
from logger_utils import log_connected, log_error, log_result_count, log_info

from config import Config

class MongoDBManager:
    def __init__(self):
        self.client = None
        self.db = None
        self.collection = None
        self.connect()
    
    def connect(self):
        try:
            self.client = MongoClient(Config.MONGODB_URI)
            self.client.admin.command('ping')
            self.db = self.client[Config.MONGODB_DATABASE]
            self.collection = self.db[Config.MONGODB_COLLECTION]
            log_connected(f"MongoDB: {Config.MONGODB_DATABASE}")
            log_info(f"✓ Using collection: {Config.MONGODB_COLLECTION}")
        except ConnectionFailure as e:
            log_error(f"Failed to connect to MongoDB: {e}")
            raise
    
    def get_collection_stats(self) -> Dict[str, Any]:
        stats = {
            "total_documents": self.collection.count_documents({}),
            "database_name": self.db.name,
            "collection_name": self.collection.name,
            "indexes": list(self.collection.list_indexes())
        }
        return stats
    
    def execute_query(self, query: Dict[str, Any], limit: int = 100) -> List[Dict]:
        try:
            results = list(self.collection.find(query).limit(limit))
            log_result_count(len(results), "documents")
            return results
        except Exception as e:
            log_error(f"Error executing query: {e}")
            raise
    
    def execute_aggregation(self, pipeline: List[Dict], limit: int = 100) -> List[Dict]:
        try:
            if not any('$limit' in stage for stage in pipeline):
                pipeline.append({"$limit": limit})
            results = list(self.collection.aggregate(pipeline))
            log_result_count(len(results), "results")
            return results
        except Exception as e:
            log_error(f"Error executing aggregation: {e}")
            raise
    
    def get_sample_documents(self, count: int = 5) -> List[Dict]:
        return list(self.collection.find().limit(count))
    
    def get_schema_info(self) -> Dict[str, Any]:
        sample = self.collection.find_one()
        if not sample:
            return {"error": "Collection is empty"}
        schema = {}
        for key, value in sample.items():
            schema[key] = type(value).__name__
        categorical_fields = [
            "Fiscal Year", "Acquisition Type", "Acquisition Method", 
            "CalCard", "Department Name"
        ]
        distinct_values = {}
        for field in categorical_fields:
            try:
                values = self.collection.distinct(field)
                if len(values) <= 50:
                    distinct_values[field] = values
            except:
                pass
        return {
            "fields": schema,
            "sample_document": sample,
            "distinct_values": distinct_values
        }
    
    def close(self):
        if self.client:
            self.client.close()
            log_info("MongoDB connection closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
