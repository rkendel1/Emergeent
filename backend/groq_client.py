"""
GROQ API integration for AI functionality
"""
import os
import json
import httpx
from typing import List, Dict, Any

class GroqClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.groq.com/openai/v1"
        self.model = "llama3-8b-8192"  # Default GROQ model

    async def send_message(self, system_message: str, user_message: str) -> str:
        """Send a message to GROQ and get response"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                "model": self.model,
                "temperature": 0.7,
                "max_tokens": 2048
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    print(f"GROQ API error: {response.status_code} - {response.text}")
                    raise Exception(f"GROQ API error: {response.status_code}")
                    
        except Exception as e:
            print(f"GROQ API error: {e}")
            raise e

    def set_model(self, model_name: str):
        """Set the model to use"""
        self.model = model_name
        return self