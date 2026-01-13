"""
Hugging Face API Client
Client for working with Hugging Face Inference API models
"""
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from huggingface_hub import InferenceClient
except ImportError:
    logger.error("huggingface_hub is not installed. Install it with: pip install huggingface_hub")
    InferenceClient = None


class HFClient:
    """Client for working with Hugging Face Inference API"""
    
    # Default model name
    DEFAULT_MODEL = "Qwen/Qwen2.5-72B-Instruct:novita"
    # DEFAULT_MODEL = "Qwen/Qwen2.5-7B-Instruct:together"
    
    # System instruction for the AI model
    SYSTEM_INSTRUCTION = (
        "You are a finance support specialist in Somalia Bank. "
        "You know English and Somali language. "
        "You are helping the user to translate text from Somali to English, "
        "You will be given a text and you will need to translate it to English and identify the threat level and confidence score. Keep answer short and concise."
        "Also clasify its risk based on banks and how they operate, put it in risk parameter."
        "Keep answer in JSON format with: somali_text, english_text, threat_level, confidence_score, risk."
    )
    
    def __init__(self, api_key: Optional[str] = None, default_model: Optional[str] = None):
        """
        Initialize HF client
        
        Args:
            api_key: API key for HF (if not provided, taken from HF_TOKEN env var)
            default_model: Default model name (if not provided, uses DEFAULT_MODEL constant)
        """
        # Get API key: first from parameter, then from environment variable
        self.api_key = api_key or os.getenv("HF_TOKEN")
        self.default_model = default_model or self.DEFAULT_MODEL
        self.instruction = self.SYSTEM_INSTRUCTION
        
        if not self.api_key:
            logger.error("HF_TOKEN is not set!")
            self.client = None
            return
        
        if InferenceClient is None:
            logger.error("huggingface_hub is not installed. Install it with: pip install huggingface_hub")
            raise ImportError("huggingface_hub is not installed. Install it with: pip install huggingface_hub")
        
        try:
            logger.info("Creating InferenceClient with explicit api_key parameter...")
            # Pass API key explicitly via api_key parameter
            self.client = InferenceClient(api_key=self.api_key)
            logger.info(f"HF client initialized. Model: {self.default_model}")
        except Exception as e:
            logger.error(f"Error initializing HF client: {e}", exc_info=True)
            self.client = None
    
    def process_user_request(
        self,
        user_prompt: str,
        model: Optional[str] = None
    ) -> str:
        """
        Process user request with automatic instruction handling
        
        This method encapsulates the logic of processing user requests.
        It automatically applies the system instruction and handles the full request flow.
        
        Args:
            user_prompt: User's input prompt
            model: Model name (if not provided, uses default_model)
        
        Returns:
            Model response as a string
        """
        if not self.client:
            raise ValueError("HF client is not initialized. Check HF_TOKEN.")
        
        # The system instruction is sent as a system message
        # User prompt is sent as user message
        response = self.generate_content(
            contents=user_prompt,
            model=model
        )
        
        return response
    

    def generate_content(
        self,
        contents: str,
        model: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate content via HF Inference API
        
        Args:
            contents: Request text
            model: Model name (if not provided, uses default_model)
            **kwargs: Additional parameters for API
        
        Returns:
            Model response as a string
        """
        if not self.client:
            raise ValueError("HF client is not initialized. Check HF_TOKEN.")
        
        model = model or self.default_model

        if InferenceClient is None:
            raise ValueError("huggingface_hub package is not installed")
        
        try:
            # HF Inference API uses chat.completions.create with messages
            messages = [
                {
                    "role": "system",
                    "content": self.instruction
                },
                {
                    "role": "user",
                    "content": contents
                }
            ]
            
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                **kwargs
            )
            
            # Extract text from response
            if not response.choices or len(response.choices) == 0:
                raise ValueError("Empty response from HF API")
            
            message = response.choices[0].message
            if not message or not message.content:
                raise ValueError("Empty response content from HF API")
            
            return message.content
            
        except Exception as e:
            logger.error(f"Error generating content: {e}", exc_info=True)
            raise


    def is_available(self) -> bool:
        """
        Check if client is available
        
        Returns:
            True if client is available, False otherwise
        """
        return self.client is not None and self.api_key is not None
