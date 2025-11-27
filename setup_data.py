#!/usr/bin/env python3
"""
Setup script to create the evaluation dataset file.
"""

import json


def create_evaluation_dataset():
    """Create the sample_questions_hybrid_eval.jsonl file with exact content."""
    
    # Evaluation questions (EXACT content - do not modify)
    questions = [
        {"id":"rag_policy_beverages_return_days","question":"According to the product policy, what is the return window (days) for unopened Beverages? Return an integer.","format_hint":"int"},
        {"id":"hybrid_top_category_qty_summer_1997","question":"During 'Summer Beverages 1997' as defined in the marketing calendar, which product category had the highest total quantity sold? Return {category:str, quantity:int}.","format_hint":"{category:str, quantity:int}"},
        {"id":"hybrid_aov_winter_1997","question":"Using the AOV definition from the KPI docs, what was the Average Order Value during 'Winter Classics 1997'? Return a float rounded to 2 decimals.","format_hint":"float"},
        {"id":"sql_top3_products_by_revenue_alltime","question":"Top 3 products by total revenue all-time. Revenue uses Order Details: SUM(UnitPrice*Quantity*(1-Discount)). Return list[{product:str, revenue:float}].","format_hint":"list[{product:str, revenue:float}]"},
        {"id":"hybrid_revenue_beverages_summer_1997","question":"Total revenue from the 'Beverages' category during 'Summer Beverages 1997' dates. Return a float rounded to 2 decimals.","format_hint":"float"},
        {"id":"hybrid_best_customer_margin_1997","question":"Per the KPI definition of gross margin, who was the top customer by gross margin in 1997? Assume CostOfGoods is approximated by 70% of UnitPrice if not available. Return {customer:str, margin:float}.","format_hint":"{customer:str, margin:float}"}
    ]
    
    # Write to JSONL file
    with open("sample_questions_hybrid_eval.jsonl", "w", encoding="utf-8") as f:
        for question in questions:
            f.write(json.dumps(question) + "\n")
    
    print("=" * 70)
    print("✓✓✓ Evaluation dataset created successfully! ✓✓✓")
    print("=" * 70)
    print(f"\nCreated: sample_questions_hybrid_eval.jsonl")
    print(f"Total questions: {len(questions)}")
    print("\nQuestion types:")
    print("  - RAG-only: 1 question (rag_policy_*)")
    print("  - SQL-only: 1 question (sql_top3_*)")
    print("  - Hybrid: 4 questions (hybrid_*)")
    print("\nYou can now run:")
    print("  python run_agent_hybrid.py --batch sample_questions_hybrid_eval.jsonl --out outputs_hybrid.jsonl")


if __name__ == "__main__":
    create_evaluation_dataset()
