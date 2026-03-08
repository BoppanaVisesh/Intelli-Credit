"""
LLM Service supporting multiple providers (free alternatives to OpenAI)
"""
import os
import json
from typing import Optional, Dict, Any, List
from enum import Enum
import google.generativeai as genai
import requests


class LLMProvider(str, Enum):
    GEMINI = "gemini"  # FREE: 1500 req/day, 60 req/min
    OLLAMA = "ollama"  # FREE: Runs locally, no API costs
    GROQ = "groq"      # FREE tier available


class LLMService:
    """
    Unified LLM service supporting multiple free providers.
    Default: Google Gemini (free tier)
    """
    
    def __init__(
        self, 
        provider: LLMProvider = LLMProvider.GEMINI,
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.provider = provider
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        
        # Default models for each provider
        self.model = model or {
            LLMProvider.GEMINI: "gemini-1.5-flash",  # Fast & free
            LLMProvider.OLLAMA: "llama3",
            LLMProvider.GROQ: "llama3-70b-8192"
        }.get(provider, "gemini-1.5-flash")
        
        # Initialize provider
        if provider == LLMProvider.GEMINI:
            genai.configure(api_key=self.api_key)
            self.client = genai.GenerativeModel(self.model)
        elif provider == LLMProvider.OLLAMA:
            self.base_url = "http://localhost:11434/api/generate"
        elif provider == LLMProvider.GROQ:
            self.base_url = "https://api.groq.com/openai/v1/chat/completions"
    
    def generate_text(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate text using the configured LLM provider.
        
        Args:
            prompt: User prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-1)
            system_prompt: System/instruction prompt
            
        Returns:
            Generated text response
        """
        if self.provider == LLMProvider.GEMINI:
            return self._generate_gemini(prompt, max_tokens, temperature, system_prompt)
        elif self.provider == LLMProvider.OLLAMA:
            return self._generate_ollama(prompt, max_tokens, temperature, system_prompt)
        elif self.provider == LLMProvider.GROQ:
            return self._generate_groq(prompt, max_tokens, temperature, system_prompt)
    
    def _generate_gemini(
        self, 
        prompt: str, 
        max_tokens: int, 
        temperature: float,
        system_prompt: Optional[str]
    ) -> str:
        """Generate using Google Gemini (FREE: 1500 req/day)"""
        try:
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            
            generation_config = genai.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
            )
            
            response = self.client.generate_content(
                full_prompt,
                generation_config=generation_config
            )
            
            return response.text
        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")
    
    def _generate_ollama(
        self, 
        prompt: str, 
        max_tokens: int, 
        temperature: float,
        system_prompt: Optional[str]
    ) -> str:
        """Generate using Ollama (FREE: Runs locally, install from ollama.ai)"""
        try:
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            
            payload = {
                "model": self.model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }
            
            response = requests.post(self.base_url, json=payload, timeout=120)
            response.raise_for_status()
            
            return response.json()["response"]
        except requests.exceptions.ConnectionError:
            raise Exception(
                "Ollama not running. Install from https://ollama.ai and run: ollama pull llama3"
            )
        except Exception as e:
            raise Exception(f"Ollama error: {str(e)}")
    
    def _generate_groq(
        self, 
        prompt: str, 
        max_tokens: int, 
        temperature: float,
        system_prompt: Optional[str]
    ) -> str:
        """Generate using Groq (FREE tier available)"""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            response = requests.post(self.base_url, headers=headers, json=payload)
            response.raise_for_status()
            
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            raise Exception(f"Groq API error: {str(e)}")
    
    def generate_structured(
        self,
        prompt: str,
        schema: Dict[str, Any],
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate structured JSON output matching the provided schema.
        
        Args:
            prompt: User prompt
            schema: JSON schema describing expected output
            system_prompt: System instructions
            
        Returns:
            Parsed JSON response matching schema
        """
        schema_str = json.dumps(schema, indent=2)
        full_system_prompt = f"""{system_prompt or ''}

You must respond with valid JSON matching this exact schema:
{schema_str}

Only output the JSON, no additional text."""
        
        response_text = self.generate_text(
            prompt=prompt,
            system_prompt=full_system_prompt,
            temperature=0.3  # Lower temp for structured output
        )
        
        # Extract JSON from response
        try:
            # Try to parse directly
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
                return json.loads(json_str)
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
                return json.loads(json_str)
            else:
                raise ValueError(f"Could not parse JSON from response: {response_text[:200]}")


# Convenience functions

def get_llm_service(provider: str = "gemini") -> LLMService:
    """
    Get LLM service instance.
    
    Args:
        provider: "gemini" (free), "ollama" (free local), or "groq" (free tier)
    """
    from core.config import get_settings
    settings = get_settings()
    
    if provider == "gemini":
        return LLMService(
            provider=LLMProvider.GEMINI,
            api_key=settings.GEMINI_API_KEY
        )
    elif provider == "ollama":
        return LLMService(provider=LLMProvider.OLLAMA)
    elif provider == "groq":
        return LLMService(
            provider=LLMProvider.GROQ,
            api_key=os.getenv("GROQ_API_KEY")
        )
    else:
        raise ValueError(f"Unknown provider: {provider}")


# Example usage
if __name__ == "__main__":
    # Using free Gemini API
    llm = get_llm_service("gemini")
    
    response = llm.generate_text(
        prompt="Explain debt service coverage ratio in 2 sentences.",
        system_prompt="You are a credit analyst assistant."
    )
    print("Gemini:", response)
    
    # Using structured output
    schema = {
        "sentiment": "string (POSITIVE/NEGATIVE/NEUTRAL)",
        "confidence": "number (0-1)",
        "summary": "string"
    }
    
    result = llm.generate_structured(
        prompt="Analyze sentiment: 'Company shows strong growth with excellent management'",
        schema=schema
    )
    print("Structured:", result)
