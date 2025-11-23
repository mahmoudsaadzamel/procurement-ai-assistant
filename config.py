import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "california_procurement")
    MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION", "purchase_orders")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    DATA_FILE = "PURCHASE ORDER DATA EXTRACT 2012-2015_0.csv"
    MAX_ITERATIONS = 3
    TEMPERATURE = 0.1
    
    @classmethod
    def validate(cls):
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not found. Please set it in .env file")
        return True
