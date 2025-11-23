from typing import Dict, Any, List
from datetime import datetime
import math
from logger_utils import log_generating, log_analyzing

from database import MongoDBManager


class DataExplorer:
    """Explores and analyzes the procurement dataset"""
    
    def __init__(self):
        """Initialize data explorer"""
        self.db_manager = MongoDBManager()
    
    def get_overview(self) -> Dict[str, Any]:
        """
        Get high-level overview of the dataset
        
        Returns:
            Dictionary with dataset overview statistics
        """
        log_generating("dataset overview")
        
        overview = {
            "total_records": self.db_manager.collection.count_documents({}),
            "fiscal_years": self.db_manager.collection.distinct("Fiscal Year"),
            "departments": len(self.db_manager.collection.distinct("Department Name")),
            "suppliers": len(self.db_manager.collection.distinct("Supplier Name")),
            "acquisition_types": self.db_manager.collection.distinct("Acquisition Type"),
            "acquisition_methods": self.db_manager.collection.distinct("Acquisition Method")
        }
        
        # Calculate total spending (filter for positive numbers to avoid NaN)
        import math
        total_spending = list(self.db_manager.collection.aggregate([
            {
                "$match": {
                    "Total Price": {"$gt": 0, "$type": "number"}
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total": {"$sum": "$Total Price"}
                }
            }
        ]))
        
        if total_spending and total_spending[0].get("total") is not None:
            total = total_spending[0].get("total", 0)
            if isinstance(total, (int, float)) and not (math.isnan(total) if isinstance(total, float) else False):
                overview["total_spending"] = total
        
        return overview
    
    def analyze_spending_by_fiscal_year(self) -> List[Dict[str, Any]]:
        """
        Analyze spending patterns by fiscal year
        
        Returns:
            List of spending by fiscal year
        """
        log_analyzing("spending by fiscal year")
        
        pipeline = [
            {
                "$match": {
                    "Total Price": {"$gt": 0, "$type": "number"}
                }
            },
            {
                "$group": {
                    "_id": "$Fiscal Year",
                    "total_spending": {"$sum": "$Total Price"},
                    "order_count": {"$sum": 1},
                    "avg_order_value": {"$avg": "$Total Price"}
                }
            },
            {"$sort": {"_id": 1}}
        ]
        
        return self.db_manager.execute_aggregation(pipeline, limit=10)
    
    def analyze_spending_by_department(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """
        Analyze spending by department
        
        Args:
            top_n: Number of top departments to return
            
        Returns:
            List of top spending departments
        """
        log_analyzing(f"top {top_n} departments by spending")
        
        pipeline = [
            {
                "$match": {
                    "Total Price": {"$gt": 0, "$type": "number"}
                }
            },
            {
                "$group": {
                    "_id": "$Department Name",
                    "total_spending": {"$sum": "$Total Price"},
                    "order_count": {"$sum": 1}
                }
            },
            {"$sort": {"total_spending": -1}},
            {"$limit": top_n}
        ]
        
        return self.db_manager.execute_aggregation(pipeline, limit=top_n)
    
    def analyze_acquisition_methods(self) -> List[Dict[str, Any]]:
        """
        Analyze usage of different acquisition methods
        
        Returns:
            List of acquisition methods with statistics
        """
        log_analyzing("acquisition methods")
        
        pipeline = [
            {
                "$match": {
                    "Total Price": {"$gt": 0, "$type": "number"}
                }
            },
            {
                "$group": {
                    "_id": "$Acquisition Method",
                    "count": {"$sum": 1},
                    "total_spending": {"$sum": "$Total Price"},
                    "avg_order_value": {"$avg": "$Total Price"}
                }
            },
            {"$sort": {"total_spending": -1}}
        ]
        
        return self.db_manager.execute_aggregation(pipeline, limit=50)
    
    def get_top_suppliers(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """
        Get top suppliers by spending
        
        Args:
            top_n: Number of top suppliers to return
            
        Returns:
            List of top suppliers
        """
        log_analyzing(f"top {top_n} suppliers")
        
        pipeline = [
            {
                "$match": {
                    "Total Price": {"$gt": 0, "$type": "number"}
                }
            },
            {
                "$group": {
                    "_id": "$Supplier Name",
                    "total_spending": {"$sum": "$Total Price"},
                    "order_count": {"$sum": 1}
                }
            },
            {"$sort": {"total_spending": -1}},
            {"$limit": top_n}
        ]
        
        return self.db_manager.execute_aggregation(pipeline, limit=top_n)
    
    def get_top_items(self, top_n: int = 20) -> List[Dict[str, Any]]:
        """
        Get most frequently ordered items
        
        Args:
            top_n: Number of top items to return
            
        Returns:
            List of most common items
        """
        log_analyzing(f"top {top_n} most ordered items")
        
        pipeline = [
            {
                "$match": {
                    "Item Name": {"$ne": ""},
                    "Total Price": {"$gt": 0, "$type": "number"}
                }
            },
            {
                "$group": {
                    "_id": "$Item Name",
                    "order_count": {"$sum": 1},
                    "total_quantity": {"$sum": "$Quantity"},
                    "total_spending": {"$sum": "$Total Price"}
                }
            },
            {"$sort": {"order_count": -1}},
            {"$limit": top_n}
        ]
        
        return self.db_manager.execute_aggregation(pipeline, limit=top_n)
    
    def analyze_quarterly_spending(self, fiscal_year: str = None) -> List[Dict[str, Any]]:
        """
        Analyze spending by quarter
        
        Args:
            fiscal_year: Specific fiscal year to analyze (optional)
            
        Returns:
            List of quarterly spending
        """
        log_analyzing("quarterly spending")
        
        # Build match stage
        match_stage = {}
        if fiscal_year:
            match_stage = {"Fiscal Year": fiscal_year}
        
        match_conditions = {"Total Price": {"$gt": 0, "$type": "number"}}
        if match_stage:
            match_conditions.update(match_stage)
        
        pipeline = [
            {"$match": match_conditions},
            {
                "$addFields": {
                    "date_obj": {"$dateFromString": {"dateString": "$Creation Date"}}
                }
            },
            {
                "$addFields": {
                    "creation_month": {"$month": "$date_obj"}
                }
            },
            {
                "$addFields": {
                    "quarter": {
                        "$switch": {
                            "branches": [
                                {"case": {"$in": ["$creation_month", [7, 8, 9]]}, "then": "Q1"},
                                {"case": {"$in": ["$creation_month", [10, 11, 12]]}, "then": "Q2"},
                                {"case": {"$in": ["$creation_month", [1, 2, 3]]}, "then": "Q3"},
                                {"case": {"$in": ["$creation_month", [4, 5, 6]]}, "then": "Q4"}
                            ],
                            "default": "Unknown"
                        }
                    }
                }
            },
            {
                "$group": {
                    "_id": {
                        "fiscal_year": "$Fiscal Year",
                        "quarter": "$quarter"
                    },
                    "total_spending": {"$sum": "$Total Price"},
                    "order_count": {"$sum": 1}
                }
            },
            {"$sort": {"_id.fiscal_year": 1, "_id.quarter": 1}}
        ]
        
        return self.db_manager.execute_aggregation(pipeline, limit=50)
    
    def print_overview(self):
        """Print a formatted overview of the dataset"""
        overview = self.get_overview()
        
        print("\n" + "=" * 70)
        print("PROCUREMENT DATASET OVERVIEW")
        print("=" * 70)
        print(f"Total Records:        {overview['total_records']:,}")
        print(f"Total Spending:       ${overview.get('total_spending', 0):,.2f}")
        print(f"Fiscal Years:         {', '.join(map(str, sorted(overview['fiscal_years'])))}")
        print(f"Unique Departments:   {overview['departments']:,}")
        print(f"Unique Suppliers:     {overview['suppliers']:,}")
        print(f"\nAcquisition Types:    {', '.join(overview['acquisition_types'])}")
        print(f"\nAcquisition Methods:  {len(overview['acquisition_methods'])} unique methods")
        print("=" * 70)
    
    def close(self):
        """Close database connection"""
        self.db_manager.close()


def main():
    """Main function for data exploration"""
    explorer = DataExplorer()
    
    try:
        # Print overview
        explorer.print_overview()
        
        # Spending by fiscal year
        print("\n" + "=" * 70)
        print("SPENDING BY FISCAL YEAR")
        print("=" * 70)
        fiscal_data = explorer.analyze_spending_by_fiscal_year()
        for item in fiscal_data:
            print(f"{item['_id']}: ${item['total_spending']:,.2f} "
                  f"({item['order_count']:,} orders)")
        
        # Top departments
        print("\n" + "=" * 70)
        print("TOP 10 DEPARTMENTS BY SPENDING")
        print("=" * 70)
        dept_data = explorer.analyze_spending_by_department(10)
        for i, dept in enumerate(dept_data, 1):
            print(f"{i}. {dept['_id']}: ${dept['total_spending']:,.2f} "
                  f"({dept['order_count']:,} orders)")
        
        # Top items
        print("\n" + "=" * 70)
        print("TOP 10 MOST FREQUENTLY ORDERED ITEMS")
        print("=" * 70)
        items_data = explorer.get_top_items(10)
        for i, item in enumerate(items_data, 1):
            print(f"{i}. {item['_id']}: {item['order_count']:,} orders, "
                  f"${item['total_spending']:,.2f}")
        
    finally:
        explorer.close()


if __name__ == "__main__":
    main()


