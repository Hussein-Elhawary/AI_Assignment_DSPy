import dspy
from typing import List, Optional, Any
from llama_cpp import Llama


# Load the GGUF model using llama-cpp-python
llama_model = Llama(
    model_path="models/phi3.5.gguf",
    n_ctx=4096,           # Context window
    n_gpu_layers=0,       # CPU only (set to -1 for full GPU)
    verbose=False,        # Reduce logging
    n_threads=4           # Number of CPU threads
)


# Create a DSPy-compatible LM class
class LlamaCppLM(dspy.BaseLM):
    """DSPy-compatible wrapper for llama-cpp-python."""
    
    def __init__(self, model, model_name="phi3.5"):
        self.llama_model = model
        self.model_name = model_name
        self.history = []
        self.provider = "llama-cpp"
        self.kwargs = {
            "temperature": 0.7,
            "max_tokens": 2000,
            "top_p": 0.95,
            "stop": ["<|end|>", "<|endoftext|>", "</s>"]
        }
        # Initialize parent class with model name
        super().__init__(model=model_name)
    
    def basic_request(self, prompt: str, **kwargs) -> dict:
        """Generate completion for the given prompt."""
        # Merge default kwargs with provided ones
        generation_kwargs = {**self.kwargs, **kwargs}
        
        # Format prompt for Phi-3.5 instruct model
        formatted_prompt = f"<|user|>\n{prompt}<|end|>\n<|assistant|>\n"
        
        # Generate response
        response = self.llama_model(
            formatted_prompt,
            max_tokens=generation_kwargs.get('max_tokens', 2000),
            temperature=generation_kwargs.get('temperature', 0.7),
            top_p=generation_kwargs.get('top_p', 0.95),
            stop=generation_kwargs.get('stop', ["<|end|>", "</s>"]),
            echo=False
        )
        
        # Extract text from response
        text = response['choices'][0]['text'].strip()
        
        # DSPy expects 'prompt' field in the response for completion models
        return {
            "choices": [{
                "text": text,
                "message": {"content": text, "role": "assistant"}
            }],
            "usage": response.get('usage', {})
        }
    
    def __call__(self, prompt=None, messages=None, **kwargs):
        """DSPy interface for generation."""
        if prompt is None and messages:
            # Handle messages format
            prompt = messages[-1].get('content', '') if isinstance(messages, list) else str(messages)
        elif prompt is None:
            prompt = ""
            
        response = self.basic_request(prompt, **kwargs)
        return [choice["text"] for choice in response["choices"]]


# Configure DSPy with the wrapped model
lm = LlamaCppLM(llama_model, model_name="phi3.5")
dspy.settings.configure(lm=lm)
print("DSPy configured with llama-cpp-python using models/phi3.5.gguf")


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
        # Use Predict instead of ChainOfThought for simpler output
        self.router = dspy.Predict(RouterSignature)
    
    def forward(self, question: str) -> str:
        """
        Route the question to the appropriate tool.
        
        Args:
            question: User's question
            
        Returns:
            Tool choice: 'rag', 'sql', or 'hybrid'
        """
        try:
            result = self.router(question=question)
            return result.tool_choice if hasattr(result, 'tool_choice') else "hybrid"
        except:
            return "hybrid"


class SQLGeneratorModule(dspy.Module):
    """Module for generating SQL queries using Chain of Thought reasoning."""
    
    def __init__(self):
        super().__init__()
        # Try to load optimized version if it exists
        import os
        optimized_path = os.path.join(
            os.path.dirname(__file__), 
            "sql_gen_optimized.json"
        )
        
        # Use Predict for better local model compatibility
        if os.path.exists(optimized_path):
            print(f"Loading optimized SQL Generator from {optimized_path}")
            try:
                self.generator = dspy.ChainOfThought(SQLGeneratorSignature)
                self.generator.load(optimized_path)
            except:
                self.generator = dspy.Predict(SQLGeneratorSignature)
        else:
            # Use Predict instead of ChainOfThought for local models
            self.generator = dspy.Predict(SQLGeneratorSignature)
    
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
        try:
            result = self.generator(
                question=question,
                schema=schema,
                constraints=constraints
            )
            return result.sql_query if hasattr(result, 'sql_query') else "SELECT 1"
        except Exception as e:
            print(f"SQL generation failed: {e}")
            return "SELECT 1"


class SynthesizerModule(dspy.Module):
    """Module for synthesizing final answers from SQL data and RAG context."""
    
    def __init__(self):
        super().__init__()
        # Use Predict for better local model compatibility
        self.synthesizer = dspy.Predict(SynthesizerSignature)
    
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
        
        try:
            result = self.synthesizer(
                question=question,
                sql_data=sql_data,
                context=context,
                format_hint=format_hint
            )
            
            return {
                "final_answer": result.final_answer if hasattr(result, 'final_answer') else "No answer generated",
                "explanation": result.explanation if hasattr(result, 'explanation') else "Unable to explain"
            }
        except Exception as e:
            print(f"Synthesis failed: {e}")
            return {
                "final_answer": "Error generating answer",
                "explanation": str(e)
            }
