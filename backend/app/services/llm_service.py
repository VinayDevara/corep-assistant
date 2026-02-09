import os
from groq import Groq
from typing import List, Dict, Optional
import json
from tenacity import retry, stop_after_attempt, wait_exponential


class LLMService:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY", "")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable not set")
        
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"  # Updated to supported model
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def generate_structured_output(
        self,
        query: str,
        scenario: Optional[str],
        regulatory_context: List[Dict],
        template_type: str
    ) -> Dict:
        """Generate structured COREP output based on query and regulatory context"""
        
        # Build context from regulatory references
        context_text = "\n\n".join([
            f"**{ref['document']} - {ref['section']}**\n{ref['content']}"
            for ref in regulatory_context
        ])
        
        # System prompt for structured output
        system_prompt = f"""You are an expert UK banking regulatory reporting assistant specializing in PRA COREP reporting.

Your task is to analyze regulatory requirements and generate structured output for COREP templates.

Template Type: {template_type}

Instructions:
1. Carefully analyze the regulatory context provided
2. Answer the user's question with reference to specific rules
3. Generate structured data for the COREP template fields
4. Provide justification for each field using specific regulatory references
5. Assign confidence scores (0.0-1.0) based on clarity of regulatory guidance
6. Output MUST be valid JSON following the exact schema provided

Output Schema:
{{
  "fields": [
    {{
      "field_id": "string (e.g., 'CR1_010_010')",
      "field_name": "string (descriptive name)",
      "value": "any (number, string, or null if not determinable)",
      "justification": "string (explain reasoning with regulatory references)",
      "regulatory_references": ["list of document sections used"],
      "confidence_score": float (0.0-1.0)
    }}
  ],
  "summary": "string (brief summary of findings)",
  "key_considerations": ["list of important points to note"]
}}"""

        user_prompt = f"""Query: {query}

{f"Scenario: {scenario}" if scenario else ""}

Regulatory Context:
{context_text}

Based on the above regulatory context, generate structured output for the {template_type} COREP template. 
Ensure all field values are justified with specific regulatory references."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,  # Low temperature for consistency
                max_tokens=4000,
                response_format={"type": "json_object"}  # Enforce JSON output
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            print(f"LLM generation error: {e}")
            raise
    
    def extract_answer(
        self,
        query: str,
        regulatory_context: List[Dict]
    ) -> str:
        """Extract a direct answer to the query from regulatory context"""
        
        context_text = "\n\n".join([
            f"**{ref['document']} - {ref['section']}**\n{ref['content']}"
            for ref in regulatory_context
        ])
        
        system_prompt = """You are an expert UK banking regulatory assistant. 
Provide clear, accurate answers based on PRA Rulebook and COREP guidance.
Cite specific sections when answering."""
        
        user_prompt = f"""Question: {query}

Regulatory Context:
{context_text}

Provide a clear, concise answer with specific regulatory references."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"LLM answer extraction error: {e}")
            raise
