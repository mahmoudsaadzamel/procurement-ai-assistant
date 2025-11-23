# Data Setup Guide

This guide explains how to load the California procurement data into MongoDB and why we use 500,000 records.

## Understanding the Dataset

The dataset contains California state procurement records from fiscal years 2012-2013, 2013-2014, and 2014-2015. Each record represents a purchase order made by a state department.

### Dataset Details

- **Source File**: PURCHASE ORDER DATA EXTRACT 2012-2015_0.csv
- **Total Records in File**: 919,735 records
- **Records We Load**: 500,000 records
- **Total Spending**: Over $202 billion
- **Departments**: 111 state departments
- **Suppliers**: 24,169 unique suppliers

### Why Only 500,000 Records?

We load 500,000 records instead of all 919,735 for a specific reason:

**MongoDB Atlas Free Tier Limitation**

- MongoDB Atlas free tier (M0) provides 512MB of storage
- Each record with all fields takes approximately 1KB of space
- 500,000 records = approximately 500MB
- This fits comfortably within the 512MB limit with room for indexes

**Full Dataset Would Require**
- 919,735 records × 1KB = approximately 920MB
- This exceeds the free tier limit
- Would require a paid MongoDB tier ($9/month minimum)

For demonstration and testing purposes, 500,000 records provides:
- Sufficient data diversity for all query types
- Representative sample across all fiscal years
- All departments and acquisition types
- Accurate spending analysis
- Fast query performance

## Data Structure

Each record contains:

### Key Fields

- **Creation Date**: When the order was created in the system
- **Purchase Date**: Official purchase order date
- **Fiscal Year**: 2012-2013, 2013-2014, or 2014-2015
- **Department Name**: State department making the purchase
- **Supplier Name**: Company providing goods/services
- **Item Name**: Description of purchased item
- **Quantity**: Number of items ordered
- **Unit Price**: Price per item
- **Total Price**: Total cost of the order
- **Acquisition Type**: IT Goods, IT Services, Non-IT Goods, Non-IT Services
- **Acquisition Method**: How the purchase was made (contract, competitive bid, etc.)
- **CalCard**: Whether state credit card was used (YES/NO)

### Important Notes

- Dates are stored as ISO strings (e.g., "2013-08-27T00:00:00")
- California fiscal year runs July 1 to June 30
- Fiscal quarters: Q1 (Jul-Sep), Q2 (Oct-Dec), Q3 (Jan-Mar), Q4 (Apr-Jun)
- Some fields may be null or empty
- Total Price is filtered for positive values to avoid calculation errors

## Loading the Data

### Prerequisites

1. MongoDB Atlas account (free tier)
2. Database created (e.g., "california_procurement") # i use this name in the task 
3. Collection ready (e.g., "purchase_orders")
4. Connection string in `.env` file

### Step 1: Prepare Environment

Create a `.env` file in the project root with:

```
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
MONGODB_DATABASE=california_procurement
MONGODB_COLLECTION=purchase_orders
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-3.5-turbo
```

Replace:
- `username` with your MongoDB database username
- `password` with your database user password
- `cluster` with your cluster name
- `your_openai_key` with your OpenAI API key

### Step 2: Run Data Loader

The data loader reads the CSV file and loads it into MongoDB in chunks:

```bash
python data_loader.py
```

### What the Loader Does

1. **Reads CSV in chunks**: Processes 10,000 records at a time to avoid memory issues
2. **Cleans data**: 
   - Converts dates to ISO string format
   - Converts numeric fields (removes $ and commas)
   - Handles missing values (converts to None/null)
3. **Loads to MongoDB**: Inserts records in batches
4. **Creates indexes**: Adds indexes on commonly queried fields
5. **Verifies load**: Confirms all records were inserted successfully

### Loading Time

- Approximately 2-3 minutes for 500,000 records
- Depends on your internet connection speed
- MongoDB Atlas free tier is in the cloud

### Monitoring Progress

You'll see output like:

```
Chunk 1: Inserted 10000 records. Total: 10000
Chunk 2: Inserted 10000 records. Total: 20000
Chunk 3: Inserted 10000 records. Total: 30000
...
DATA LOAD COMPLETE
Total Records Processed: 500000
Successfully Inserted: 500000
Duration: 142.35 seconds
```

## Data Cleaning

The loader automatically cleans the data:

### Date Fields
- Parsed from various formats
- Converted to ISO 8601 standard (YYYY-MM-DDTHH:MM:SS)
- Invalid dates become null

### Numeric Fields
- $ symbols removed
- Commas removed (e.g., "1,234.56" becomes 1234.56)
- Invalid numbers become null
- Negative values kept (represent refunds/adjustments)

### Text Fields
- Trimmed of extra whitespace
- Empty strings remain empty
- No text transformations (preserves original data)

## Indexes Created

The loader creates indexes on frequently queried fields:

- Creation Date (for time-based queries)
- Fiscal Year (for year-based analysis)
- Department Name (for department queries)
- Supplier Name (for supplier analysis)
- Acquisition Method (for method analysis)
- Total Price (for spending calculations)

These indexes dramatically improve query performance.

## Verifying the Load

After loading, verify the data:

### Check Record Count

In MongoDB Atlas or using Python:

```python
from database import MongoDBManager

db = MongoDBManager()
stats = db.get_collection_stats()
print(f"Total documents: {stats['total_documents']}")
```

Expected output: 500,000 documents

### View Sample Data

```python
from database import MongoDBManager

db = MongoDBManager()
sample = db.get_sample_documents(1)
print(sample[0])
```

You should see a complete record with all fields.

## Troubleshooting

### "Collection already contains documents"

If you see this warning, the data is already loaded. The loader will continue from where it left off or skip if all data is present.

To reload from scratch:
1. Delete the collection in MongoDB Atlas
2. Run the loader again

### "Connection timeout"

- Check your internet connection
- Verify MongoDB Atlas is accessible
- Check IP whitelist in MongoDB Atlas Network Access

### "Invalid connection string"

- Verify MONGODB_URI in `.env`
- Check username and password are correct
- Ensure special characters in password are URL-encoded

### "Out of memory"

The loader processes data in chunks to avoid memory issues. If this still occurs:
- Reduce chunk_size in data_loader.py (default is 10000)
- Close other applications
- Restart Python and try again

## Data Quality

The 500,000 records include:

- All fiscal years represented (2012-2015)
- All departments represented
- All acquisition types and methods
- Representative supplier distribution
- Full range of purchase amounts
- Both CalCard and non-CalCard transactions

This ensures all query types return meaningful results.

## Next Steps

After loading the data:

1. Run the test suite: `python test_assistant.py`
2. Start the web app: `streamlit run app.py`
3. Try example queries to verify everything works
4. Explore the data through the interface

## Additional Information

For questions about specific fields, refer to:
- DGS PURCHASING DATA DICTIONARY.pdf (included in project)
- Assessment for AI Engineer Candidates.pdf (project requirements)

The data loader is designed to be idempotent - running it multiple times won't create duplicates. It checks for existing data and continues where it left off.

