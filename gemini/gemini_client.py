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
        logger.info("=" * 80)
        logger.info("GEMINI CLIENT INIT - Starting initialization")
        logger.info("=" * 80)
        
        # Get API key: first from parameter, then from environment variable
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.default_model = default_model or self.DEFAULT_MODEL
        self.instruction = self.SYSTEM_INSTRUCTION
        
        logger.info(f"API key parameter provided: {api_key is not None}")
        logger.info(f"GEMINI_API_KEY from environment: {'SET' if os.getenv('GEMINI_API_KEY') else 'NOT SET'}")
        logger.info(f"API key being used: {'SET' if self.api_key else 'NOT SET'}")
        if self.api_key:
            logger.info(f"API key length: {len(self.api_key)} characters")
            logger.info(f"API key prefix: {self.api_key[:10]}...")
        
        if not self.api_key:
            logger.error("GEMINI_API_KEY is not set!")
            logger.error("API key must be provided via api_key parameter or set in GEMINI_API_KEY environment variable")
            self.client = None
            return
        
        if genai is None:
            logger.error("google-genai is not installed. Install it with: pip install google-genai")
            raise ImportError("google-genai is not installed. Install it with: pip install google-genai")
        
        try:
            logger.info("Creating genai.Client with explicit api_key parameter...")
            # Pass API key explicitly via api_key parameter
            self.client = genai.Client(api_key=self.api_key)
            logger.info(f"✓ Gemini client successfully initialized!")
            logger.info(f"  Default model: {self.default_model}")
            logger.info(f"  Client created: {self.client is not None}")
            logger.info("=" * 80)
        except Exception as e:
            logger.error(f"✗ Error initializing Gemini client: {e}", exc_info=True)
            logger.error(f"Error type: {type(e).__name__}")
            self.client = None
            logger.info("=" * 80)
    
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

        try:
            response = self.client.models.generate_content(
                model=model,
                contents=contents,
                config=genai.types.GenerateContentConfig(
                    system_instruction=self.instruction
                )
            )
            
            logger.info(f"Content successfully generated. Model: {model}")
            logger.info(f"Response: {response.text}")
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
        
        logger.info("=" * 80)
        logger.info("GEMINI CHAT REQUEST")
        logger.info("=" * 80)
        logger.info(f"User prompt: {user_prompt}")
        logger.info(f"Model: {model or self.default_model}")
        logger.info(f"System instruction: {self.instruction}")
        logger.info("-" * 80)
        
        # The system instruction is automatically applied via GenerateContentConfig
        # User prompt is sent as contents
        response = self.generate_content(
            contents=user_prompt,
            model=model
        )
        
        logger.info(f"Response received: {response}")
        logger.info("=" * 80)
        
        return response
    
    def is_available(self) -> bool:
        """
        Check if client is available
        
        Returns:
            True if client is available, False otherwise
        """
        return self.client is not None and self.api_key is not None
