"""
Groq API client for generating answers and study materials
"""

import os
import asyncio
import logging
from typing import Optional
from groq import Groq

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GroqClient:
    """Async Groq client for AI text generation"""
    
    def __init__(self):
        self.api_key = os.getenv('GROQ_API_KEY')
        self.client = None
        self.model = "llama3-70b-8192"
        
        if self.api_key:
            try:
                self.client = Groq(api_key=self.api_key)
                logger.info("Groq client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {e}")
                self.client = None
        else:
            logger.warning("GROQ_API_KEY not found in environment variables")
    
    def is_available(self) -> bool:
        """Check if Groq client is available"""
        return self.client is not None
    
    async def generate_answer(self, question: str, context: str) -> str:
        """
        Generate an answer to a question based on provided context
        
        Args:
            question (str): User's question
            context (str): Retrieved context from documents
            
        Returns:
            str: Generated answer
        """
        if not self.is_available():
            raise Exception("Groq API not available. Please check your GROQ_API_KEY.")
        
        prompt = self._create_qa_prompt(question, context)
        
        try:
            # Run the synchronous Groq call in a thread pool
            response = await asyncio.get_event_loop().run_in_executor(
                None, self._make_groq_call, prompt, 500
            )
            
            answer = response.choices[0].message.content
            return answer.strip() if answer else "No response generated."
            
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            raise Exception(f"Failed to generate answer: {str(e)}")
    
    async def generate_study_material(self, material_type: str, context: str, topic: Optional[str] = None) -> str:
        """
        Generate study materials based on context
        
        Args:
            material_type (str): Type of material ("summary", "flashcards", "quiz")
            context (str): Source content
            topic (Optional[str]): Specific topic focus
            
        Returns:
            str: Generated study material
        """
        if not self.is_available():
            raise Exception("Groq API not available. Please check your GROQ_API_KEY.")
        
        prompt = self._create_study_prompt(material_type, context, topic)
        
        try:
            # Adjust max tokens based on material type
            max_tokens = 1000 if material_type == "quiz" else 800
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, self._make_groq_call, prompt, max_tokens
            )
            
            content = response.choices[0].message.content
            return content.strip() if content else f"No {material_type} generated."
            
        except Exception as e:
            logger.error(f"Error generating {material_type}: {e}")
            raise Exception(f"Failed to generate {material_type}: {str(e)}")
    
    def _make_groq_call(self, prompt: str, max_tokens: int):
        """Make synchronous Groq API call"""
        return self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=max_tokens,
            top_p=0.9
        )
    
    def _create_qa_prompt(self, question: str, context: str) -> str:
        """Create prompt for Q&A"""
        return f"""You are a helpful study assistant. Answer the student's question based ONLY on the provided context. If the answer is not found in the context, say "I cannot find the answer in the provided study materials."

Be clear, concise, and educational in your response. Use bullet points or numbered lists when appropriate to make the information easy to understand.

**CONTEXT:**
{context}

**QUESTION:**
{question}

**ANSWER:**"""
    
    def _create_study_prompt(self, material_type: str, context: str, topic: Optional[str] = None) -> str:
        """Create prompt for study material generation"""
        topic_text = f" focusing on {topic}" if topic else ""
        
        if material_type == "summary":
            return f"""Create a comprehensive summary of the following study material{topic_text}. 

Make the summary:
- Well-organized with clear sections
- Easy to understand for students
- Include key concepts and important details
- Use bullet points and subheadings where appropriate

**STUDY MATERIAL:**
{context}

**SUMMARY:**"""
        
        elif material_type == "flashcards":
            return f"""Create 8-10 flashcards from the following study material{topic_text}.

Format each flashcard as:
**Card [number]:**
**Front:** [Question or term]
**Back:** [Answer or definition]

Make the flashcards cover the most important concepts and ensure they are good for memorization and review.

**STUDY MATERIAL:**
{context}

**FLASHCARDS:**"""
        
        elif material_type == "quiz":
            return f"""Create a 5-question multiple choice quiz from the following study material{topic_text}.

Format each question as:
**Question [number]:** [Question text]
A) [Option A]
B) [Option B]
C) [Option C]
D) [Option D]
**Correct Answer:** [Letter]
**Explanation:** [Brief explanation]

Make sure the questions test understanding of key concepts, not just memorization.

**STUDY MATERIAL:**
{context}

**QUIZ:**"""
        
        else:
            return f"""Generate educational content of type "{material_type}" from the following study material{topic_text}:

{context}"""