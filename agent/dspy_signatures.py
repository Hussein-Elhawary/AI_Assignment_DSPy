import dspy
from typing import List


# Configure DSPy to use local Ollama model
dspy.settings.configure(
    lm=dspy.OllamaLocal(
        model="phi3.5:3.8b-mini-instruct-q4_K_M",
        base_url="http://localhost:11434",
        max_tokens=2000
    )
)


class RouterSignature(dspy.Signature):
    """Route the question to the appropriate tool: 'rag' for documentation lookup, 
    'sql' for database queries, or 'hybrid' for both."""
    
    question = dspy.InputField(desc="User's question about retail analytics")
    tool_choice = dspy.OutputField(desc="Tool to use: 'rag', 'sql', or 'hybrid'")


class SQLGeneratorSignature(dspy.Signature):
    """Generate SQL query based on the question, database schema, and constraints.
    
    Important: If CostOfGoods is missing, assume it is 0.7 * UnitPrice.
    """
    
    question = dspy.InputField(desc="User's question requiring SQL query")
    schema = dspy.InputField(desc="Database schema with table definitions")
    constraints = dspy.InputField(desc="Additional constraints or rules for query generation")
    sql_query = dspy.OutputField(desc="Valid SQL query to answer the question")


class SynthesizerSignature(dspy.Signature):
    """Synthesize a final answer from SQL data and/or RAG context."""
    
    question = dspy.InputField(desc="Original user question")
    sql_data = dspy.InputField(desc="Data retrieved from SQL query (as string)")
    context = dspy.InputField(desc="Relevant context chunks from documentation")
    format_hint = dspy.InputField(desc="Hint about desired output format")
    final_answer = dspy.OutputField(desc="Complete answer to the question")
    explanation = dspy.OutputField(desc="Explanation of how the answer was derived")


class RouterModule(dspy.Module):
    """Module for routing questions to appropriate tools."""
    
    def __init__(self):
        super().__init__()
        self.router = dspy.Predict(RouterSignature)
    
    def forward(self, question: str) -> str:
        """
        Route the question to the appropriate tool.
        
        Args:
            question: User's question
            
        Returns:
            Tool choice: 'rag', 'sql', or 'hybrid'
        """
        result = self.router(question=question)
        return result.tool_choice


class SQLGeneratorModule(dspy.Module):
    """Module for generating SQL queries using Chain of Thought reasoning."""
    
    def __init__(self):
        super().__init__()
        self.generator = dspy.ChainOfThought(SQLGeneratorSignature)
    
    def forward(self, question: str, schema: str, constraints: str = "") -> str:
        """
        Generate SQL query for the given question.
        
        Args:
            question: User's question
            schema: Database schema
            constraints: Additional constraints or rules
            
        Returns:
            SQL query string
        """
        result = self.generator(
            question=question,
            schema=schema,
            constraints=constraints
        )
        return result.sql_query


class SynthesizerModule(dspy.Module):
    """Module for synthesizing final answers from SQL data and RAG context."""
    
    def __init__(self):
        super().__init__()
        self.synthesizer = dspy.ChainOfThought(SynthesizerSignature)
    
    def forward(
        self, 
        question: str, 
        sql_data: str = "", 
        context: List[str] = None, 
        format_hint: str = ""
    ) -> dict:
        """
        Synthesize final answer from available data.
        
        Args:
            question: User's question
            sql_data: SQL query results as string
            context: List of relevant context chunks
            format_hint: Desired output format
            
        Returns:
            Dictionary with 'final_answer' and 'explanation' keys
        """
        if context is None:
            context = []
        
        result = self.synthesizer(
            question=question,
            sql_data=sql_data,
            context=context,
            format_hint=format_hint
        )
        
        return {
            "final_answer": result.final_answer,
            "explanation": result.explanation
        }
