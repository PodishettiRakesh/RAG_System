from typing import List, Dict
from transformers import pipeline
import torch


class LLMService:
    """Handles LLM generation using Flan-T5-Base model."""
    
    def __init__(self):
        """Initialize the LLM service with Flan-T5-Base model."""
        print("🤖 Initializing LLM Service...")
        print("Model: google/flan-t5-base")
        print("Type: Text-to-Text Generation")
        print("Parameters: 770M")
        print("Task: Instruction-following, Q&A")
        
        try:
            # Initialize the pipeline
            self.generator = pipeline(
                "text2text-generation",
                model="google/flan-t5-base",
                torch_dtype=torch.float32,  # Use float32 for compatibility
                device=-1  # Use CPU (change to 0 for GPU if available)
            )
            
            print("✅ LLM Service initialized successfully!")
            self._print_model_info()
            
        except Exception as e:
            print(f"❌ Error initializing LLM Service: {e}")
            raise
    
    def _print_model_info(self):
        """Print detailed model information."""
        print("\n📊 MODEL DETAILS:")
        print("┌─────────────────────────────────────┐")
        print("│ Model: Google Flan-T5-Base           │")
        print("│ Type: Text-to-Text Transformer      │")
        print("│ Parameters: 770 million             │")
        print("│ Architecture: Encoder-Decoder        │")
        print("│ Training: Instruction-tuned          │")
        print("│ Max Tokens: 512                     │")
        print("│ Memory Usage: ~3GB RAM              │")
        print("│ Speed: ~50ms per response (CPU)     │")
        print("└─────────────────────────────────────┘")
        print()
    
    def format_context(self, search_results: List[Dict]) -> str:
        """
        Format search results into context for LLM.
        
        Args:
            search_results (List[Dict]): Results from vector search
        
        Returns:
            str: Formatted context string
        """
        if not search_results:
            return "No relevant information found."
        
        context_parts = []
        for i, result in enumerate(search_results):
            context_parts.append(f"Source {i+1}: {result['chunk_text']}")
        
        return "\n\n".join(context_parts)
    
    def create_prompt(self, context: str, query: str) -> str:
        """
        Create a structured prompt for the LLM.
        
        Args:
            context (str): Retrieved context
            query (str): User query
        
        Returns:
            str: Formatted prompt
        """
        prompt = f"""Answer the following question based ONLY on the provided context. If the context doesn't contain the answer, say "I don't have enough information to answer this question."

CONTEXT:
{context}

QUESTION: {query}

ANSWER:"""
        
        return prompt
    
    def generate_response(self, query: str, search_results: List[Dict], max_length: int = 200) -> Dict:
        """
        Generate response using LLM with retrieved context.
        
        Args:
            query (str): User query
            search_results (List[Dict]): Retrieved similar chunks
            max_length (int): Maximum response length
        
        Returns:
            Dict: Response with metadata
        """
        print(f"🤖 Generating response for query: '{query[:50]}...'")
        print(f"📚 Using {len(search_results)} context chunks")
        
        try:
            # Format context
            context = self.format_context(search_results)
            
            # Create prompt
            prompt = self.create_prompt(context, query)
            
            print(f"📝 Prompt length: {len(prompt)} characters")
            
            # Generate response
            response = self.generator(
                prompt,
                max_length=max_length,
                num_return_sequences=1,
                temperature=0.7,  # Balance between creativity and consistency
                do_sample=True,
                pad_token_id=self.generator.tokenizer.eos_token_id
            )
            
            generated_text = response[0]['generated_text'].strip()
            
            # Prepare result
            result = {
                "query": query,
                "response": generated_text,
                "context_used": len(search_results),
                "context_preview": context[:200] + "..." if len(context) > 200 else context,
                "model_info": {
                    "model": "google/flan-t5-base",
                    "parameters": "770M",
                    "type": "text-to-text-generation"
                },
                "tokens_used": len(generated_text.split()),
                "response_time": "Fast (local inference)"
            }
            
            print(f"✅ Response generated: {len(generated_text)} characters")
            print(f"🎯 Response: {generated_text[:100]}...")
            
            return result
            
        except Exception as e:
            print(f"❌ Error generating response: {e}")
            return {
                "query": query,
                "response": f"Error generating response: {str(e)}",
                "context_used": len(search_results),
                "error": True
            }
    
    def get_model_stats(self) -> Dict:
        """Get model and service statistics."""
        return {
            "model_name": "google/flan-t5-base",
            "model_type": "text-to-text-generation",
            "parameters": "770M",
            "architecture": "encoder-decoder",
            "max_tokens": 512,
            "training": "instruction-tuned",
            "device": "CPU",
            "memory_usage": "~3GB RAM",
            "response_time": "~50ms (CPU)",
            "capabilities": [
                "Question answering",
                "Instruction following",
                "Context-based responses",
                "Summarization"
            ]
        }
