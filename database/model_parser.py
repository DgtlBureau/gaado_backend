"""
Model Parser for Gemini responses
Parses JSON responses from Gemini API and extracts structured data
"""
import json
import logging
from typing import Optional
from database.models import ProcessedCommentCreate

logger = logging.getLogger(__name__)


class ModelParser:
    """Parser for AI API JSON responses"""
    
    @staticmethod
    def parse_ai_response(response_text: str, raw_comment_id: Optional[int] = None) -> Optional[ProcessedCommentCreate]:
        """
        Parse JSON response from Gemini API and return ProcessedCommentCreate model
        
        Args:
            response_text: Raw text response from Gemini (should contain JSON)
            raw_comment_id: Optional raw_comment_id if already known
        
        Returns:
            ProcessedCommentCreate model instance with parsed data
            Returns None if parsing fails
        """
        try:
            # Try to extract JSON from response text
            # Gemini might return JSON wrapped in markdown code blocks or plain JSON
            text = response_text.strip()
            
            # Remove markdown code blocks if present
            if text.startswith("```json"):
                text = text[7:]  # Remove ```json
            elif text.startswith("```"):
                text = text[3:]  # Remove ```
            
            if text.endswith("```"):
                text = text[:-3]  # Remove closing ```
            
            text = text.strip()
            
            # Parse JSON
            parsed_data = json.loads(text)
            
            # Extract fields according to ProcessedComment model
            threat_level_slug = parsed_data.get("threat_level")
            
            # Normalize threat_level_slug to slug format (lowercase, no spaces)
            if threat_level_slug:
                threat_level_slug = str(threat_level_slug).strip().lower()
            
            # Extract and validate confidence_score
            confidence_score = parsed_data.get("confidence_score")
            if confidence_score is not None:
                try:
                    confidence_score = float(confidence_score)
                    # Ensure it's in valid range
                    if confidence_score < 0.0 or confidence_score > 1.0:
                        logger.warning(f"confidence_score out of range: {confidence_score}, clamping to [0.0, 1.0]")
                        confidence_score = max(0.0, min(1.0, confidence_score))
                except (ValueError, TypeError):
                    logger.warning(f"Invalid confidence_score: {confidence_score}")
                    confidence_score = None
            
            # Extract risk from response
            risk = parsed_data.get("risk")
            if risk:
                risk = str(risk).strip()
            
            # Create ProcessedCommentCreate model instance
            processed_comment = ProcessedCommentCreate(
                raw_comment_id=raw_comment_id,  # Will be set later in main.py if None
                translation_en=parsed_data.get("english_text"),
                threat_level_slug=threat_level_slug,
                confidence_score=confidence_score,
                dialect=None,  # Not provided by Gemini yet
                keywords=None,  # Not provided by Gemini yet
                risk=risk,
                is_reviewed=False
            )
            
            logger.info(f"Successfully parsed Gemini response into ProcessedCommentCreate: "
                       f"translation_en={processed_comment.translation_en}, "
                       f"threat_level_slug={processed_comment.threat_level_slug}, "
                       f"confidence_score={processed_comment.confidence_score}")
            
            return processed_comment
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Gemini response: {e}")
            logger.debug(f"Response text: {response_text}")
            return None
        except Exception as e:
            logger.error(f"Error parsing Gemini response: {e}", exc_info=True)
            return None

