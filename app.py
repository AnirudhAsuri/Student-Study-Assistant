#!/usr/bin/env python3
"""
Student Study Assistant - Web-based RAG application
Features: PDF upload, document processing, Q&A, and study material generation
"""

import os
import json
import uuid
from pathlib import Path
from typing import List, Dict, Optional
from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

# Import our custom services
from services.pdf_processor import extract_text_from_pdf, extract_text_from_txt
from services.rag_engine import RAGEngine
from services.groq_client import GroqClient
from services.study_generator import StudyMaterialGenerator

# Initialize FastAPI app
app = FastAPI(
    title="Student Study Assistant",
    description="AI-powered study assistant with PDF processing and material generation",
    version="2.0"
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize services
rag_engine = RAGEngine()
groq_client = GroqClient()
study_generator = StudyMaterialGenerator(groq_client)

# Ensure upload and data directories exist
Path("uploads").mkdir(exist_ok=True)
Path("data").mkdir(exist_ok=True)

# Store file metadata
files_db = {}

# Pydantic models
class QuestionRequest(BaseModel):
    question: str

class GenerateRequest(BaseModel):
    material_type: str  # "summary", "flashcards", "quiz"
    topic: Optional[str] = None

class FileResponse(BaseModel):
    id: str
    filename: str
    size: int
    status: str


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the main application page"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload and process PDF or text files"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected")
    
    # Validate file type
    allowed_extensions = {'.pdf', '.txt'}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type. Please upload PDF or TXT files."
        )
    
    # Generate unique file ID
    file_id = str(uuid.uuid4())
    safe_filename = f"{file_id}_{file.filename}"
    file_path = Path("uploads") / safe_filename
    
    try:
        # Save uploaded file
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Extract text based on file type
        if file_ext == '.pdf':
            text_content = extract_text_from_pdf(str(file_path))
        else:  # .txt
            text_content = extract_text_from_txt(str(file_path))
        
        if not text_content.strip():
            os.remove(file_path)
            raise HTTPException(
                status_code=400, 
                detail="Could not extract readable text from the file"
            )
        
        # Store file metadata
        files_db[file_id] = {
            "id": file_id,
            "filename": file.filename,
            "safe_filename": safe_filename,
            "size": len(content),
            "status": "uploaded",
            "text_length": len(text_content)
        }
        
        # Add to RAG index
        rag_engine.add_document(file_id, text_content, file.filename)
        files_db[file_id]["status"] = "indexed"
        
        return FileResponse(
            id=file_id,
            filename=file.filename,
            size=len(content),
            status="indexed"
        )
        
    except Exception as e:
        # Clean up on error
        if file_path.exists():
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


@app.get("/files")
async def list_files():
    """Get list of uploaded files"""
    return {"files": list(files_db.values())}


@app.delete("/files/{file_id}")
async def delete_file(file_id: str):
    """Delete a file and remove from index"""
    if file_id not in files_db:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_info = files_db[file_id]
    safe_filename = file_info["safe_filename"]
    file_path = Path("uploads") / safe_filename
    
    # Remove physical file
    if file_path.exists():
        os.remove(file_path)
    
    # Remove from RAG index
    rag_engine.remove_document(file_id)
    
    # Remove from database
    del files_db[file_id]
    
    return {"message": "File deleted successfully"}


@app.post("/ask")
async def ask_question(request: QuestionRequest):
    """Answer questions using RAG"""
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    if not rag_engine.has_documents():
        raise HTTPException(
            status_code=400, 
            detail="No documents uploaded. Please upload PDF or text files first."
        )
    
    try:
        # Get relevant context
        context_result = rag_engine.retrieve_context(request.question)
        
        if not context_result["context"]:
            return {
                "answer": "I cannot find relevant information in your uploaded documents to answer this question.",
                "sources": [],
                "confidence": 0.0
            }
        
        # Generate answer using Groq
        answer = await groq_client.generate_answer(request.question, context_result["context"])
        
        return {
            "answer": answer,
            "sources": context_result["sources"],
            "confidence": context_result["avg_similarity"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")


@app.post("/generate")
async def generate_materials(request: GenerateRequest):
    """Generate study materials (summaries, flashcards, quizzes)"""
    if not rag_engine.has_documents():
        raise HTTPException(
            status_code=400, 
            detail="No documents uploaded. Please upload PDF or text files first."
        )
    
    valid_types = ["summary", "flashcards", "quiz"]
    if request.material_type not in valid_types:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid material type. Must be one of: {valid_types}"
        )
    
    try:
        # Get context for generation
        if request.topic:
            # Topic-specific generation
            context_result = rag_engine.retrieve_context(request.topic, top_k=5)
            context = context_result["context"]
        else:
            # Use entire corpus for general materials
            context = rag_engine.get_full_context()
        
        if not context:
            raise HTTPException(
                status_code=400, 
                detail="No content available for material generation"
            )
        
        # Generate study materials
        material = await study_generator.generate_material(
            request.material_type, 
            context, 
            request.topic
        )
        
        return {
            "material_type": request.material_type,
            "content": material,
            "topic": request.topic
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating materials: {str(e)}")


@app.get("/status")
async def get_status():
    """Get application status and statistics"""
    return {
        "status": "running",
        "uploaded_files": len(files_db),
        "indexed_documents": rag_engine.get_document_count(),
        "total_chunks": rag_engine.get_chunk_count(),
        "groq_available": groq_client.is_available()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000, reload=False)