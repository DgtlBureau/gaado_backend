"""
Google Gemini API Client
Client for working with Google Gemini API models
"""
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from google import genai
except ImportError:
    logger.error("google-genai is not installed. Install it with: pip install google-genai")
    genai = None


class GeminiClient:
    """Client for working with Google Gemini API"""
    
    # Default model name
    DEFAULT_MODEL = "gemini-3-flash-preview"
    
    # System instruction for the AI model
    SYSTEM_INSTRUCTION = (
        "You are a finance support specialist in Somalia Bank. "
        "You know English and Somali language. "
        "You are helping the user to translate text from Somali to English, "
        "You will be given a text and you will need to translate it to English and identify the threat level and confidence score. Keep answer short and concise."
        "Keep answer in JSON format with: somali_text, english_text, threat_level, confidence_score."
    )
    
    def __init__(self, api_key: Optional[str] = None, default_model: Optional[str] = None):
        """
        Initialize Gemini client
        
        Args:
            api_key: API key for Gemini (if not provided, taken from GEMINI_API_KEY env var)
            default_model: Default model name (if not provided, uses DEFAULT_MODEL constant)
        """
        # Get API key: first from parameter, then from environment variable
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.default_model = default_model or self.DEFAULT_MODEL
        self.instruction = self.SYSTEM_INSTRUCTION
        
        if not self.api_key:
            logger.error("GEMINI_API_KEY is not set!")
            self.client = None
            return
        
        if genai is None:
            logger.error("google-genai is not installed. Install it with: pip install google-genai")
            raise ImportError("google-genai is not installed. Install it with: pip install google-genai")
        
        try:
            logger.info("Creating genai.Client with explicit api_key parameter...")
            # Pass API key explicitly via api_key parameter
            self.client = genai.Client(api_key=self.api_key)
            logger.info(f"Gemini client initialized. Model: {self.default_model}")
        except Exception as e:
            logger.error(f"Error initializing Gemini client: {e}", exc_info=True)
            self.client = None
    
    def generate_content(
        self,
        contents: str,
        model: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate content via Gemini API
        
        Args:
            contents: Request text
            model: Model name (if not provided, uses default_model)
            **kwargs: Additional parameters for API
        
        Returns:
            Model response as a string
        """
        if not self.client:
            raise ValueError("Gemini client is not initialized. Check GEMINI_API_KEY.")
        
        model = model or self.default_model

        if genai is None:
            raise ValueError("google-genai package is not installed")
        
        try:
            response = self.client.models.generate_content(
                model=model,
                contents=contents,
                config=genai.types.GenerateContentConfig(
                    system_instruction=self.instruction
                )
            )
            
            if response.text is None:
                raise ValueError("Empty response from Gemini API")
            
            return response.text
            
        except Exception as e:
            logger.error(f"Error generating content: {e}", exc_info=True)
            raise
    
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
            raise ValueError("Gemini client is not initialized. Check GEMINI_API_KEY.")
        
        # The system instruction is automatically applied via GenerateContentConfig
        # User prompt is sent as contents
        response = self.generate_content(
            contents=user_prompt,
            model=model
        )
        
        return response
    
    def is_available(self) -> bool:
        """
        Check if client is available
        
        Returns:
            True if client is available, False otherwise
        """
        return self.client is not None and self.api_key is not None
