import json
from typing import Dict, Any, List, Optional

from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools import Tool
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage, AIMessage, SystemMessage

from database import MongoDBManager
from config import Config
from logger_utils import log_initialized, log_executing, log_success, log_error, log_info


class ProcurementAssistant:
    """AI-powered procurement assistant using LangChain"""
    
    def __init__(self):
        """Initialize the procurement assistant"""
        Config.validate()
        
        self.db_manager = MongoDBManager()
        self.llm = ChatOpenAI(
            model=Config.OPENAI_MODEL,
            temperature=Config.TEMPERATURE,
            api_key=Config.OPENAI_API_KEY
        )
        
        # Get schema information for the agent
        self.schema_info = self._get_schema_context()
        
        # Initialize conversation history
        self.conversation_history: List[Dict[str, str]] = []
        
        log_initialized("Procurement Assistant")
    
    def _get_schema_context(self) -> str:
        """
        Generate schema context for the LLM (optimized - no expensive distinct queries)
        
        Returns:
            String containing schema information
        """
        schema_text = """
DATABASE SCHEMA INFORMATION:

Collection: purchase_orders

Key Fields and Types:
- Creation Date (datetime): System date when order was created
- Purchase Date (datetime): Date of purchase order entered by user
- Fiscal Year (string): Fiscal year (2012-2013, 2013-2014, 2014-2015)
- LPA Number (string): Contract Number (if present, it's contract spend)
- Purchase Order Number (string): PO number
- Requisition Number (string): Requisition number
- Acquisition Type (string): Type of acquisition (IT Goods, IT Services, Non-IT Goods, Non-IT Services)
- Sub-Acquisition Type (string): Sub-category of acquisition
- Acquisition Method (string): Method used for purchase (e.g., Statewide Contract, Informal Competitive, etc.)
- Sub-Acquisition Method (string): Sub-method of acquisition
- Department Name (string): Name of purchasing department
- Supplier Code (string): Supplier identifier
- Supplier Name (string): Name of supplier
- Supplier Qualifications (string): Certifications (CA-MB, CA-SB, CA-DVBE, etc.)
- Supplier Zip Code (string): Supplier's zip code
- CalCard (string): Whether state credit card was used (YES/NO)
- Item Name (string): Name of items purchased
- Item Description (string): Description of items
- Quantity (number): Quantity of items
- Unit Price (number): Price per unit
- Total Price (number): Total price (excluding tax/shipping)
- Classification Codes (string): UNSPSC codes
- Normalized UNSPSC (string): First 8 digits of UNSPSC
- Commodity Title (string): Commodity name from UNSPSC
- Class (string): Class number from UNSPSC
- Class Title (string): Class title from UNSPSC
- Family (string): Family number from UNSPSC
- Family Title (string): Family title from UNSPSC
- Segment (string): Segment number from UNSPSC
- Segment Title (string): Segment title from UNSPSC
- Location (string): Geographic location

IMPORTANT NOTES:
- California fiscal year runs from July 1 to June 30
- Quarter mapping: Q1 (Jul-Sep), Q2 (Oct-Dec), Q3 (Jan-Mar), Q4 (Apr-Jun)
- Use "Creation Date" for time-based queries (more reliable than Purchase Date)
- **CRITICAL**: Creation Date and Purchase Date are stored as ISO string format (e.g., "2013-08-27T00:00:00")
- **For date operations** ($month, $year, $dayOfMonth, etc.), you MUST convert string to Date first:
  Use: {{"$dateFromString": {{"dateString": "$Creation Date"}}}} before using date operators
- Example for quarterly analysis:
  [
    {{"$addFields": {{
      "date_obj": {{"$dateFromString": {{"dateString": "$Creation Date"}}}}
    }}}},
    {{"$addFields": {{
      "month": {{"$month": "$date_obj"}},
      "year": {{"$year": "$date_obj"}}
    }}}},
    ...rest of pipeline
  ]
- Total Price is numeric and ready for aggregation
- **IMPORTANT**: When summing Total Price, always filter for positive values to avoid NaN:
  Add a $match stage: {{"Total Price": {{"$gt": 0, "$type": "number"}}}} before $group stages
- All string fields should be matched exactly as they appear
- Fiscal Years available: 2012-2013, 2013-2014, 2014-2015
- Acquisition Types: IT Goods, IT Services, Non-IT Goods, Non-IT Services
- CalCard values: YES, NO
"""
        
        return schema_text
    
    def _execute_mongodb_query(
        self, 
        query_type: str, 
        query: str
    ) -> str:
        """
        Tool function to execute MongoDB queries
        
        Args:
            query_type: Type of query ('find' or 'aggregate')
            query: JSON string of the MongoDB query
            
        Returns:
            JSON string with results
        """
        try:
            log_executing(f"{query_type} query")
            
            # Parse the query
            query_dict = json.loads(query)
            
            if query_type == "aggregate":
                # Handle aggregation pipeline
                pipeline = query_dict if isinstance(query_dict, list) else query_dict.get("pipeline", [])
                results = self.db_manager.execute_aggregation(pipeline, limit=100)
            else:
                # Handle find query
                find_query = query_dict.get("query", {})
                results = self.db_manager.execute_query(find_query, limit=100)
            
            # Format results
            if not results:
                return json.dumps({"message": "No results found", "count": 0})
            
            # Limit result size for LLM processing
            summary = {
                "count": len(results),
                "results": results[:10] if len(results) > 10 else results,
                "note": f"Showing first 10 of {len(results)} results" if len(results) > 10 else ""
            }
            
            return json.dumps(summary, default=str)
            
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON format: {e}"
            log_error(error_msg)
            return json.dumps({"error": error_msg})
        except Exception as e:
            error_msg = f"Error executing query: {str(e)}"
            log_error(error_msg)
            return json.dumps({"error": error_msg})
    
    def _create_tools(self) -> List[Tool]:
        """
        Create tools for the agent
        
        Returns:
            List of LangChain tools
        """
        tools = [
            Tool(
                name="execute_mongodb_aggregate",
                description="""
Execute a MongoDB aggregation pipeline to analyze procurement data.
Input should be a JSON string containing an array representing the aggregation pipeline.

Example for total spending by fiscal year (CORRECT - filters positive values):
[
  {{
    "$match": {{
      "Total Price": {{"$gt": 0, "$type": "number"}}
    }}
  }},
  {{
    "$group": {{
      "_id": "$Fiscal Year",
      "total_spending": {{"$sum": "$Total Price"}},
      "order_count": {{"$sum": 1}}
    }}
  }},
  {{"$sort": {{"total_spending": -1}}}}
]

Example for quarterly analysis (CORRECT - filters positive values and converts string to Date):
[
  {{
    "$match": {{
      "Total Price": {{"$gt": 0, "$type": "number"}}
    }}
  }},
  {{
    "$addFields": {{
      "date_obj": {{"$dateFromString": {{"dateString": "$Creation Date"}}}}
    }}
  }},
  {{
    "$addFields": {{
      "month": {{"$month": "$date_obj"}},
      "year": {{"$year": "$date_obj"}}
    }}
  }},
  {{
    "$addFields": {{
      "quarter": {{
        "$switch": {{
          "branches": [
            {{"case": {{"$in": ["$month", [7, 8, 9]]}}, "then": "Q1"}},
            {{"case": {{"$in": ["$month", [10, 11, 12]]}}, "then": "Q2"}},
            {{"case": {{"$in": ["$month", [1, 2, 3]]}}, "then": "Q3"}},
            {{"case": {{"$in": ["$month", [4, 5, 6]]}}, "then": "Q4"}}
          ],
          "default": "Unknown"
        }}
      }}
    }}
  }},
  {{
    "$group": {{
      "_id": {{"year": "$year", "quarter": "$quarter"}},
      "total_spending": {{"$sum": "$Total Price"}}
    }}
  }},
  {{"$sort": {{"total_spending": -1}}}},
  {{"$limit": 1}}
]

Use this tool for:
- Aggregations (sum, avg, count)
- Grouping by fields
- Sorting results
- Complex analytical queries

CRITICAL: Always add a $match stage to filter for positive Total Price values when summing:
{{"$match": {{"Total Price": {{"$gt": 0, "$type": "number"}}}}}}
This prevents NaN results in aggregations.
""",
                func=lambda query: self._execute_mongodb_query("aggregate", query)
            ),
            Tool(
                name="execute_mongodb_find",
                description="""
Execute a MongoDB find query to retrieve specific procurement records.
Input should be a JSON string with a "query" field containing the filter criteria.

Example to find orders by department:
{{
  "query": {{
    "Department Name": "Consumer Affairs, Department of",
    "Fiscal Year": "2013-2014"
  }}
}}

Example to find orders in a price range:
{{
  "query": {{
    "Total Price": {{"$gte": 10000, "$lte": 50000}}
  }}
}}

Use this tool for:
- Finding specific records
- Filtering by field values
- Simple lookups
""",
                func=lambda query: self._execute_mongodb_query("find", query)
            )
        ]
        
        return tools
    
    def _create_agent_prompt(self) -> ChatPromptTemplate:
        """
        Create the agent prompt template
        
        Returns:
            ChatPromptTemplate for the agent
        """
        system_message = f"""You are an expert procurement data analyst assistant for California state procurement data.

{self.schema_info}

YOUR CAPABILITIES:
1. You can analyze procurement data from California state purchases (2012-2015)
2. You translate natural language questions into MongoDB queries
3. You execute queries and interpret results
4. You provide clear, accurate answers with relevant statistics

GUIDELINES FOR QUERY GENERATION:
1. Use aggregation pipelines for analytical questions (totals, averages, grouping)
2. Use find queries for looking up specific records
3. Always use "$Creation Date" for date-based queries
4. Field names must match exactly (case-sensitive, including spaces)
5. For quarterly analysis, remember CA fiscal year: Q1=Jul-Sep, Q2=Oct-Dec, Q3=Jan-Mar, Q4=Apr-Jun
6. When calculating quarters, use $month on the Creation Date field
7. Always sort results logically (e.g., by total descending, or date ascending)
8. Limit aggregation results when appropriate

RESPONSE FORMAT:
1. First, understand what the user is asking
2. Generate the appropriate MongoDB query
3. Execute the query using the tools
4. Interpret the results and provide a clear, concise answer
5. Include relevant numbers and statistics

MONEY FORMATTING GUIDELINES:
- Format all currency values in a human-readable way:
  * For billions: Use "B" (e.g., $54.94B instead of $54,936,189,540.20)
  * For millions: Use "M" (e.g., $125.5M instead of $125,500,000)
  * For thousands: Use "K" if over 10K (e.g., $15.2K instead of $15,200)
  * For values under 10K: Show full amount with commas (e.g., $5,432.50)
- Always include the dollar sign ($) before amounts
- Round to 2 decimal places for B/M/K format, or show full precision for smaller amounts
- Example: "$89.59B" is better than "$89,587,515,131.17"

Be precise, accurate, and helpful. If a query cannot be answered with the available data, explain why.
"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        return prompt
    
    def query(self, user_question: str) -> str:
        """
        Process a user question and return an answer
        
        Args:
            user_question: Natural language question from user
            
        Returns:
            Answer string
        """
        try:
            log_info(f"Processing query: {user_question}")
            
            # Create tools and agent
            tools = self._create_tools()
            prompt = self._create_agent_prompt()
            
            agent = create_openai_tools_agent(
                llm=self.llm,
                tools=tools,
                prompt=prompt
            )
            
            agent_executor = AgentExecutor(
                agent=agent,
                tools=tools,
                verbose=False,
                max_iterations=Config.MAX_ITERATIONS,
                handle_parsing_errors=True,
                return_intermediate_steps=False
            )
            
            # Execute the agent
            response = agent_executor.invoke({
                "input": user_question,
                "chat_history": self._format_chat_history()
            })
            
            answer = response.get("output", "I apologize, but I couldn't generate an answer.")
            
            # Update conversation history
            self.conversation_history.append({
                "role": "user",
                "content": user_question
            })
            self.conversation_history.append({
                "role": "assistant",
                "content": answer
            })
            
            log_success("Query processed successfully")
            return answer
            
        except Exception as e:
            error_msg = f"Error processing query: {str(e)}"
            log_error(error_msg)
            return f"I encountered an error while processing your question: {str(e)}"
    
    def _format_chat_history(self) -> List:
        """
        Format conversation history for the agent
        
        Returns:
            List of message objects
        """
        messages = []
        for msg in self.conversation_history[-10:]:  # Keep last 10 messages
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(AIMessage(content=msg["content"]))
        return messages
    
    def reset_conversation(self):
        """Reset the conversation history"""
        self.conversation_history = []
        log_info("Conversation history reset")
    
    def close(self):
        """Close database connection"""
        self.db_manager.close()


def main():
    """Main function for testing the agent"""
    assistant = ProcurementAssistant()
    
    try:
        # Test queries
        test_queries = [
            "How many total purchase orders are in the database?",
            "What was the total spending in fiscal year 2013-2014?",
            "Which quarter had the highest spending across all years?",
            "What are the top 5 most frequently ordered items?",
        ]
        
        print("\n" + "=" * 70)
        print("TESTING PROCUREMENT ASSISTANT")
        print("=" * 70)
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n{'='*70}")
            print(f"Q{i}: {query}")
            print('='*70)
            
            answer = assistant.query(query)
            print(f"\nAnswer: {answer}")
            
            input("\nPress Enter to continue to next query...")
    
    finally:
        assistant.close()


if __name__ == "__main__":
    main()


