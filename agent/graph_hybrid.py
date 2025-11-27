from typing import TypedDict, List, Dict, Any, Literal
from langgraph.graph import StateGraph, END
import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.dspy_signatures import RouterModule, SQLGeneratorModule, SynthesizerModule
from agent.rag.retrieval import LocalRetriever
from agent.rag.tools.sqlite_tool import SQLiteTool


# State Definition
class AgentState(TypedDict):
    """State for the retail analytics agent."""
    question: str
    format_hint: str
    sql_query: str
    sql_result: Dict[str, Any]  # {"columns": [...], "rows": [...], "error": str}
    retrieved_docs: List[Dict[str, str]]  # [{"doc_id": str, "content": str}]
    final_answer: str
    confidence: float
    explanation: str
    citations: List[str]
    error_count: int


# Initialize tools and modules
retriever = LocalRetriever(docs_path="docs/")
db_tool = SQLiteTool(db_path="agent/rag/northwind.db")
router_module = RouterModule()
sql_generator = SQLGeneratorModule()
synthesizer = SynthesizerModule()


# Node Implementations
def router_node(state: AgentState) -> AgentState:
    """Route the question to appropriate tool(s)."""
    try:
        tool_choice = router_module.forward(question=state["question"])
        # Normalize the choice
        tool_choice = tool_choice.lower().strip()
        if tool_choice not in ["rag", "sql", "hybrid"]:
            tool_choice = "hybrid"  # Default fallback
    except Exception as e:
        print(f"Router error: {e}, defaulting to hybrid")
        tool_choice = "hybrid"
    
    state["route"] = tool_choice
    return state


def retrieval_node(state: AgentState) -> AgentState:
    """Retrieve relevant documentation chunks."""
    docs = retriever.search(query=state["question"], k=3)
    state["retrieved_docs"] = docs
    return state


def planner_node(state: AgentState) -> AgentState:
    """
    Extract constraints or prepare context for SQL generation.
    Simple pass-through for now; can be enhanced to extract dates, entities, etc.
    """
    # Could add logic to extract date ranges, product categories, etc.
    # For now, just ensure error_count is initialized
    if "error_count" not in state:
        state["error_count"] = 0
    return state


def sql_gen_node(state: AgentState) -> AgentState:
    """Generate SQL query using DSPy with error feedback."""
    try:
        schema = db_tool.get_schema()
        
        # Build constraints including error feedback if exists
        constraints = "Use SQLite syntax. Table names with spaces use [brackets]. Join tables appropriately. For date functions, use strftime (e.g., strftime('%Y', OrderDate) for year)."
        
        # If there was a previous error, include it in the context
        if state.get("sql_result") and state["sql_result"].get("error"):
            previous_query = state.get("sql_query", "")
            error_msg = state["sql_result"]["error"]
            constraints += f"\n\nPrevious query failed:\nQuery: {previous_query}\nError: {error_msg}\nPlease fix the error and generate a corrected query."
        
        sql_query = sql_generator.forward(
            question=state["question"],
            schema=schema,
            constraints=constraints
        )
        
        # Clean up the SQL query - remove markdown code blocks and extra whitespace
        sql_query = sql_query.strip()
        # Remove markdown SQL code blocks
        if sql_query.startswith("```sql"):
            sql_query = sql_query[6:]  # Remove ```sql
        if sql_query.startswith("```"):
            sql_query = sql_query[3:]  # Remove ```
        if sql_query.endswith("```"):
            sql_query = sql_query[:-3]  # Remove trailing ```
        sql_query = sql_query.strip()
        
        state["sql_query"] = sql_query
    except Exception as e:
        print(f"SQL generation error: {e}")
        # Provide a simple fallback query
        state["sql_query"] = "SELECT 'Error generating query' as error"
        state["sql_result"] = {"error": str(e), "rows": [], "columns": []}
    
    return state


def executor_node(state: AgentState) -> AgentState:
    """Execute the SQL query."""
    sql_query = state["sql_query"]
    result = db_tool.execute_query(sql_query)
    state["sql_result"] = result
    
    # Track error count
    if result.get("error"):
        state["error_count"] = state.get("error_count", 0) + 1
    
    return state


def synthesizer_node(state: AgentState) -> AgentState:
    """Synthesize final answer from SQL data and/or RAG context."""
    try:
        # Prepare SQL data as string
        sql_data = ""
        if state.get("sql_result"):
            if state["sql_result"].get("error"):
                sql_data = f"SQL Error: {state['sql_result']['error']}"
            else:
                sql_data = json.dumps({
                    "columns": state["sql_result"].get("columns", []),
                    "rows": state["sql_result"].get("rows", [])
                }, indent=2)
        
        # Prepare context from retrieved docs
        context = [doc["content"] for doc in state.get("retrieved_docs", [])]
        
        # Get format hint
        format_hint = state.get("format_hint", "Provide a clear, concise answer.")
        
        # Synthesize answer
        result = synthesizer.forward(
            question=state["question"],
            sql_data=sql_data,
            context=context,
            format_hint=format_hint
        )
        
        state["final_answer"] = result["final_answer"]
        state["explanation"] = result["explanation"]
        
        # Generate citations
        citations = []
        # Add doc IDs from retrieved docs
        for doc in state.get("retrieved_docs", []):
            citations.append(doc["doc_id"])
        
        # Add table names from SQL query if available
        if state.get("sql_query") and not state["sql_result"].get("error"):
            # Simple extraction of table names (could be more sophisticated)
            tables = ["Orders", "Order Details", "Products", "Customers"]
            for table in tables:
                if table in state["sql_query"]:
                    citations.append(f"Table: {table}")
        
        state["citations"] = list(set(citations))  # Remove duplicates
        
        # Set confidence (simple heuristic)
        if state["sql_result"].get("error"):
            state["confidence"] = 0.3
        elif state.get("retrieved_docs") and len(state["retrieved_docs"]) > 0:
            state["confidence"] = 0.9
        else:
            state["confidence"] = 0.7
            
    except Exception as e:
        print(f"Synthesizer error: {e}")
        state["final_answer"] = "Unable to generate answer due to processing error."
        state["explanation"] = f"Error: {str(e)}"
        state["confidence"] = 0.1
        state["citations"] = []
    
    return state


# Conditional Routing Functions
def route_after_router(state: AgentState) -> Literal["retrieval_node", "planner_node"]:
    """Decide next step after router."""
    route = state.get("route", "hybrid")
    
    if route == "rag":
        return "retrieval_node"
    elif route == "sql":
        return "planner_node"
    else:  # hybrid
        return "retrieval_node"


def route_after_retrieval(state: AgentState) -> Literal["planner_node", "synthesizer_node"]:
    """Route after retrieval based on original routing decision."""
    route = state.get("route", "hybrid")
    
    if route in ["sql", "hybrid"]:
        return "planner_node"
    else:  # rag only
        return "synthesizer_node"


def route_after_executor(state: AgentState) -> Literal["sql_gen_node", "synthesizer_node"]:
    """Check for SQL errors and decide whether to retry or proceed."""
    has_error = bool(state["sql_result"].get("error"))
    error_count = state.get("error_count", 0)
    
    if has_error and error_count < 2:
        # Retry SQL generation
        return "sql_gen_node"
    else:
        # Proceed to synthesis
        return "synthesizer_node"


# Build the Graph
def build_graph() -> StateGraph:
    """Build and compile the retail analytics agent graph."""
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("router_node", router_node)
    workflow.add_node("retrieval_node", retrieval_node)
    workflow.add_node("planner_node", planner_node)
    workflow.add_node("sql_gen_node", sql_gen_node)
    workflow.add_node("executor_node", executor_node)
    workflow.add_node("synthesizer_node", synthesizer_node)
    
    # Set entry point
    workflow.set_entry_point("router_node")
    
    # Add edges
    # Router -> Conditional (Retrieval or Planner)
    workflow.add_conditional_edges(
        "router_node",
        route_after_router,
        {
            "retrieval_node": "retrieval_node",
            "planner_node": "planner_node"
        }
    )
    
    # Retrieval -> Conditional (Planner or Synthesizer)
    workflow.add_conditional_edges(
        "retrieval_node",
        route_after_retrieval,
        {
            "planner_node": "planner_node",
            "synthesizer_node": "synthesizer_node"
        }
    )
    
    # Planner -> SQL Gen
    workflow.add_edge("planner_node", "sql_gen_node")
    
    # SQL Gen -> Executor
    workflow.add_edge("sql_gen_node", "executor_node")
    
    # Executor -> Conditional (Retry SQL Gen or Synthesizer)
    workflow.add_conditional_edges(
        "executor_node",
        route_after_executor,
        {
            "sql_gen_node": "sql_gen_node",
            "synthesizer_node": "synthesizer_node"
        }
    )
    
    # Synthesizer -> END
    workflow.add_edge("synthesizer_node", END)
    
    return workflow


# Compile the graph
app = build_graph().compile()


if __name__ == "__main__":
    """Test the graph structure."""
    print("=" * 60)
    print("Retail Analytics Agent - Graph Structure")
    print("=" * 60)
    
    # Print graph information
    print("\nGraph compiled successfully!")
    print("\nNodes in the graph:")
    print("  1. router_node - Routes questions to appropriate tools")
    print("  2. retrieval_node - Retrieves documentation chunks")
    print("  3. planner_node - Extracts constraints and prepares context")
    print("  4. sql_gen_node - Generates SQL queries (with repair loop)")
    print("  5. executor_node - Executes SQL queries")
    print("  6. synthesizer_node - Synthesizes final answers")
    
    print("\nGraph Flow:")
    print("  Entry -> Router -> [Retrieval | Planner]")
    print("  Retrieval -> [Planner | Synthesizer]")
    print("  Planner -> SQL Gen -> Executor")
    print("  Executor -> [SQL Gen (repair) | Synthesizer] (max 2 retries)")
    print("  Synthesizer -> END")
    
    print("\nRepair Loop:")
    print("  - SQL errors trigger retry (max 2 attempts)")
    print("  - Error feedback included in next generation")
    
    # Try to visualize if mermaid is available
    try:
        print("\n" + "=" * 60)
        print("Graph Visualization (Mermaid):")
        print("=" * 60)
        print(app.get_graph().draw_mermaid())
    except Exception as e:
        print(f"\nVisualization not available: {e}")
    
    print("\n" + "=" * 60)
    print("Graph is ready for execution!")
    print("=" * 60)
