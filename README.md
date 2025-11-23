# California Procurement Assistant

An AI-powered assistant that analyzes California state procurement data using natural language queries. Built with LangChain, OpenAI GPT-3.5, MongoDB, and Streamlit.

## Overview

This application allows users to ask questions about California state procurement data from 2012-2015 in plain English. The AI agent automatically translates questions into MongoDB queries, executes them, and returns clear, formatted answers.

## Features

- Natural language query interface
- Automatic MongoDB query generation
- Conversation memory for follow-up questions
- Real-time data analysis
- Clean, intuitive web interface
- Pre-built quick actions for common queries

## Technology Stack

- **AI Framework**: LangChain for agent orchestration
- **Language Model**: OpenAI GPT-4.5 Turbo
- **Database**: MongoDB Atlas (cloud)
- **Web Interface**: Streamlit
- **Data Processing**: Pandas, PyMongo
- **Python**: 3.9+

## Project Structure

```
├── app.py                  # Streamlit web interface
├── ai_agent.py            # LangChain AI agent
├── database.py            # MongoDB connection and queries
├── data_explorer.py       # Data analysis utilities
├── data_loader.py         # CSV to MongoDB data loader
├── config.py              # Configuration management
├── logger_utils.py        # Centralized logging
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (create this)
└── DATA_SETUP.md          # Data loading guide
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Environment Variables

Create a `.env` file in the project root:

```
MONGODB_URI=your_mongodb_atlas_connection_string
MONGODB_DATABASE=california_procurement
MONGODB_COLLECTION=purchase_orders
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=Model_to_use
```

### 3. Load Data into MongoDB

See `DATA_SETUP.md` for detailed instructions.

```bash
python data_loader.py
```

### 4. Run the Application

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## Usage

### Web Interface

1. Open the application in your browser
2. Type a question in natural language
3. Press Enter or click a quick action button
4. View the AI-generated response

### Example Questions

- "What was the total spending in fiscal year 2013-2014?"
- "Which department spent the most money?"
- "What are the top 5 most frequently ordered items?"
- "Which quarter had the highest spending?"
- "Compare IT Goods vs Non-IT Goods spending"

### Command Line Interface

```bash
python cli.py
```

## Key Components

### AI Agent (`ai_agent.py`)

The core component that:
- Understands natural language questions
- Generates MongoDB queries dynamically
- Executes queries and interprets results
- Formats responses in human-readable form
- Maintains conversation context

### Data Explorer (`data_explorer.py`)

Pre-built analytics functions for:
- Spending analysis by fiscal year
- Top departments and suppliers
- Acquisition method analysis
- Quarterly spending trends
- Most frequently ordered items

### Database Layer (`database.py`)

Handles all MongoDB operations:
- Connection management
- Query execution (find and aggregation)
- Schema introspection
- Error handling

## Testing

Run the test suite to verify functionality:

```bash
python test_assistant.py
```

## Performance

- Average query response time: 5-8 seconds
- Supports 500,000 records efficiently
- Optimized MongoDB aggregation pipelines
- Cached sidebar data to reduce repeated queries

## Design Decisions

### Why MongoDB?

MongoDB's aggregation framework is ideal for complex analytical queries on semi-structured data. It handles grouping, sorting, and calculations efficiently.

### Why LangChain?

LangChain provides a robust framework for building AI agents with tool use, memory management, and error handling built in.

### Why GPT-3.5?

GPT-3.5 Turbo offers the best balance of performance, accuracy, and cost for this use case.

## Architecture

The application follows a clean, modular architecture:

1. **User Interface Layer**: Streamlit app for user interaction
2. **AI Agent Layer**: LangChain agent for query understanding
3. **Data Layer**: MongoDB for storage and queries
4. **Utility Layer**: Logging, configuration, data exploration

Each layer is independent and can be tested/modified separately.

## Contributing

The codebase is organized for clarity:
- Each file has a single responsibility
- Functions are reusable and well-defined
- No hardcoded queries - all dynamically generated
- Comprehensive error handling throughout

## Requirements

- Python 3.9 or higher
- MongoDB Atlas account (free tier works)
- OpenAI API key
- 4GB RAM minimum
- Internet connection for API calls

## Troubleshooting

**MongoDB Connection Issues**
- Verify your connection string in `.env`
- Check IP whitelist in MongoDB Atlas (add 0.0.0.0/0 for testing)
- Ensure database user credentials are correct

**Slow Query Performance**
- Verify MongoDB indexes are created
- Check your internet connection
- Consider upgrading to a paid MongoDB tier for better performance

**OpenAI API Errors**
- Verify your API key is valid
- Check your OpenAI account has credits
- Ensure OPENAI_API_KEY is set in `.env`

## License

This project was developed as part of an AI Engineering assessment.

## Contact

For questions or issues, please refer to the documentation in `DATA_SETUP.md`.
