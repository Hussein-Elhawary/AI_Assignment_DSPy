#!/usr/bin/env python3
"""
Main entry point for the Retail Analytics AI Agent.
Processes batch questions from JSONL and outputs structured results.
"""

import argparse
import json
import ast
import sys
import os
from typing import Any, Dict

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.graph_hybrid import app


def parse_final_answer(answer_str: str, format_hint: str) -> Any:
    """
    Convert the final_answer string to the appropriate Python type based on format_hint.
    
    Args:
        answer_str: The string answer from DSPy
        format_hint: The expected format/type (e.g., "int", "float", "list[str]", "dict")
        
    Returns:
        Converted value in the appropriate type
    """
    answer_str = answer_str.strip()
    
    # Handle numeric types
    if format_hint.lower() == "int":
        try:
            # Extract first number found if answer contains text
            import re
            numbers = re.findall(r'-?\d+', answer_str)
            if numbers:
                return int(numbers[0])
            return int(answer_str)
        except (ValueError, IndexError):
            return 0
    
    elif format_hint.lower() == "float":
        try:
            import re
            # Extract first float found
            numbers = re.findall(r'-?\d+\.?\d*', answer_str)
            if numbers:
                return float(numbers[0])
            return float(answer_str)
        except (ValueError, IndexError):
            return 0.0
    
    # Handle list types
    elif "list" in format_hint.lower():
        try:
            # Try JSON parsing first
            if answer_str.startswith('['):
                return json.loads(answer_str)
            # Try ast.literal_eval
            return ast.literal_eval(answer_str)
        except (json.JSONDecodeError, ValueError, SyntaxError):
            # Fallback: split by common delimiters
            if ',' in answer_str:
                return [item.strip() for item in answer_str.split(',')]
            return [answer_str]
    
    # Handle dict type
    elif "dict" in format_hint.lower():
        try:
            if answer_str.startswith('{'):
                return json.loads(answer_str)
            return ast.literal_eval(answer_str)
        except (json.JSONDecodeError, ValueError, SyntaxError):
            return {"value": answer_str}
    
    # Default: return as string
    return answer_str


def process_question(question_obj: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a single question through the agent graph.
    
    Args:
        question_obj: Dictionary with 'id', 'question', and 'format_hint'
        
    Returns:
        Result dictionary with required fields
    """
    # Initialize state
    initial_state = {
        "question": question_obj.get("question", ""),
        "format_hint": question_obj.get("format_hint", "string"),
        "sql_query": "",
        "sql_result": {},
        "retrieved_docs": [],
        "final_answer": "",
        "confidence": 0.0,
        "explanation": "",
        "citations": [],
        "error_count": 0
    }
    
    # Run the graph
    try:
        final_state = app.invoke(initial_state)
    except Exception as e:
        print(f"Error processing question {question_obj.get('id', 'unknown')}: {e}", file=sys.stderr)
        final_state = initial_state
        final_state["final_answer"] = f"Error: {str(e)}"
        final_state["explanation"] = "An error occurred during processing."
        final_state["confidence"] = 0.0
    
    # Parse final answer to correct type
    parsed_answer = parse_final_answer(
        final_state.get("final_answer", ""),
        question_obj.get("format_hint", "string")
    )
    
    # Construct output
    result = {
        "id": question_obj.get("id", "unknown"),
        "final_answer": parsed_answer,
        "sql": final_state.get("sql_query", ""),
        "confidence": final_state.get("confidence", 0.0),
        "explanation": final_state.get("explanation", ""),
        "citations": final_state.get("citations", [])
    }
    
    return result


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Run Retail Analytics AI Agent on batch questions"
    )
    parser.add_argument(
        "--batch",
        required=True,
        help="Path to input JSONL file with questions"
    )
    parser.add_argument(
        "--out",
        required=True,
        help="Path to output JSONL file for results"
    )
    
    args = parser.parse_args()
    
    # Validate input file exists
    if not os.path.exists(args.batch):
        print(f"Error: Input file '{args.batch}' not found.", file=sys.stderr)
        sys.exit(1)
    
    # Process questions
    results = []
    with open(args.batch, 'r', encoding='utf-8') as infile:
        for line_num, line in enumerate(infile, 1):
            line = line.strip()
            if not line:
                continue
            
            try:
                question_obj = json.loads(line)
                print(f"Processing question {question_obj.get('id', line_num)}...", file=sys.stderr)
                
                result = process_question(question_obj)
                results.append(result)
                
                print(f"  ✓ Completed: {question_obj.get('id', line_num)}", file=sys.stderr)
                
            except json.JSONDecodeError as e:
                print(f"Error parsing line {line_num}: {e}", file=sys.stderr)
                continue
    
    # Write results
    with open(args.out, 'w', encoding='utf-8') as outfile:
        for result in results:
            outfile.write(json.dumps(result) + '\n')
    
    print(f"\n✓ Processed {len(results)} questions", file=sys.stderr)
    print(f"✓ Results written to: {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
