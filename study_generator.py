"""
Study material generator for creating summaries, flashcards, and quizzes
"""

import logging
from typing import Optional
from .groq_client import GroqClient

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StudyMaterialGenerator:
    """Generate various types of study materials using AI"""
    
    def __init__(self, groq_client: GroqClient):
        self.groq_client = groq_client
    
    async def generate_material(self, material_type: str, context: str, topic: Optional[str] = None) -> str:
        """
        Generate study material of specified type
        
        Args:
            material_type (str): Type of material to generate
            context (str): Source content
            topic (Optional[str]): Specific topic focus
            
        Returns:
            str: Generated study material
        """
        if not context.strip():
            raise ValueError("Context cannot be empty")
        
        if material_type not in ["summary", "flashcards", "quiz"]:
            raise ValueError(f"Unsupported material type: {material_type}")
        
        try:
            # Generate using Groq client
            material = await self.groq_client.generate_study_material(
                material_type, context, topic
            )
            
            # Post-process the material
            processed_material = self._post_process_material(material, material_type)
            
            logger.info(f"Generated {material_type} successfully")
            return processed_material
            
        except Exception as e:
            logger.error(f"Error generating {material_type}: {e}")
            raise
    
    def _post_process_material(self, material: str, material_type: str) -> str:
        """
        Post-process generated material for better formatting
        
        Args:
            material (str): Raw generated material
            material_type (str): Type of material
            
        Returns:
            str: Processed material
        """
        if not material:
            return f"Error: No {material_type} content was generated."
        
        # Clean up extra whitespace
        lines = [line.strip() for line in material.split('\n')]
        cleaned_lines = []
        
        for line in lines:
            if line:
                cleaned_lines.append(line)
            elif cleaned_lines and cleaned_lines[-1] != "":
                cleaned_lines.append("")
        
        processed = '\n'.join(cleaned_lines)
        
        # Add formatting based on material type
        if material_type == "summary":
            if not processed.startswith("#"):
                processed = f"# Study Summary\n\n{processed}"
        
        elif material_type == "flashcards":
            if "**Card" not in processed:
                # If the format is not as expected, try to structure it
                processed = self._format_flashcards(processed)
        
        elif material_type == "quiz":
            if "**Question" not in processed:
                # If the format is not as expected, try to structure it
                processed = self._format_quiz(processed)
        
        return processed
    
    def _format_flashcards(self, content: str) -> str:
        """Format content as flashcards if not already formatted"""
        lines = content.split('\n')
        formatted = "# Flashcards\n\n"
        
        # Simple heuristic to create flashcards from content
        card_num = 1
        for line in lines:
            if line and len(line) > 10:
                if '?' in line:
                    formatted += f"**Card {card_num}:**\n"
                    formatted += f"**Front:** {line}\n"
                    formatted += f"**Back:** [Answer based on study material]\n\n"
                    card_num += 1
        
        return formatted if card_num > 1 else content
    
    def _format_quiz(self, content: str) -> str:
        """Format content as quiz if not already formatted"""
        lines = content.split('\n')
        formatted = "# Quiz\n\n"
        
        # Simple heuristic to create quiz from content
        question_num = 1
        for line in lines:
            if line and len(line) > 20 and '?' in line:
                formatted += f"**Question {question_num}:** {line}\n"
                formatted += "A) Option A\n"
                formatted += "B) Option B\n"
                formatted += "C) Option C\n"
                formatted += "D) Option D\n"
                formatted += "**Correct Answer:** A\n"
                formatted += "**Explanation:** [Based on study material]\n\n"
                question_num += 1
                
                if question_num > 5:  # Limit to 5 questions
                    break
        
        return formatted if question_num > 1 else content