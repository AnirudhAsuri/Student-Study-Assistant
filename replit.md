# Overview

This is a modern web-based Student Study Assistant application that implements Retrieval-Augmented Generation (RAG) for educational purposes. The application features a beautiful drag-and-drop interface for uploading PDF and text documents, processes them locally without external APIs, and provides AI-powered Q&A and study material generation. It uses TF-IDF vectorization for document retrieval and the Groq API for natural language generation, offering contextually relevant answers and generating summaries, flashcards, and quizzes based on uploaded study content.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Web Application Architecture
The application follows a modern web-based RAG (Retrieval-Augmented Generation) architecture with clean separation of concerns:
- **Frontend**: Beautiful responsive web interface built with Tailwind CSS and vanilla JavaScript
- **Backend**: FastAPI web framework serving REST endpoints for file management, Q&A, and material generation
- **Services**: Modular service layer handling PDF processing, RAG engine, Groq integration, and study material generation

## Document Processing Pipeline
- **File Upload**: Drag-and-drop interface supporting PDF and TXT files with progress tracking
- **Local PDF Extraction**: Uses pdfminer.six for text extraction without external APIs
- **Text Chunking**: Documents are intelligently split into paragraphs and manageable chunks with length optimization
- **Vectorization**: Enhanced TF-IDF vectorization with bigrams, stop word filtering, and sublinear term frequency
- **Index Management**: Persistent storage with automatic rebuilding and caching for optimal performance

## Enhanced RAG System
- **Multi-Document Support**: Handles multiple uploaded documents with source attribution
- **Smart Retrieval**: Configurable top-K selection with similarity thresholds and source tracking
- **Context Aggregation**: Intelligent combination of relevant chunks with metadata preservation
- **Real-time Updates**: Dynamic index rebuilding when documents are added or removed

## Study Material Generation
- **Multiple Formats**: Generates summaries, flashcards, and quizzes from uploaded content
- **Topic-Specific Generation**: Optional topic focusing for targeted material creation
- **Structured Output**: Well-formatted study materials with consistent structure and educational value

## Web Interface Features
- **Drag-and-Drop Upload**: Modern file upload with visual feedback and progress tracking
- **Real-time Status**: Live application status with file counts and system health indicators
- **Interactive Q&A**: Instant question answering with source attribution and confidence scores
- **Material Generator**: One-click generation of various study materials with copy functionality

## API Architecture
- **RESTful Endpoints**: Clean API design with proper HTTP status codes and error handling
- **File Management**: Upload, list, and delete operations with metadata tracking
- **Async Processing**: Non-blocking operations for better performance and user experience
- **Error Handling**: Comprehensive error handling with user-friendly messages

# External Dependencies

## AI Service
- **Groq API**: Primary language model service for generating contextual responses and study materials

## Web Framework
- **FastAPI**: Modern, fast web framework for building the REST API
- **Uvicorn**: ASGI server for serving the web application
- **Jinja2**: Template engine for serving HTML pages

## Document Processing
- **pdfminer.six**: Local PDF text extraction without external API dependencies
- **python-multipart**: File upload handling for the web interface

## Machine Learning
- **scikit-learn**: Enhanced TF-IDF vectorization with advanced features and cosine similarity
- **numpy**: Numerical operations for vector processing and similarity calculations
- **scipy**: Sparse matrix operations for efficient similarity computations

## Frontend Technologies
- **Tailwind CSS**: Modern utility-first CSS framework via CDN for beautiful styling
- **Lucide Icons**: Icon library for consistent and attractive UI elements
- **Vanilla JavaScript**: Clean, dependency-free frontend logic for interactivity

## Data Storage
- **Local File System**: All uploaded documents stored in `uploads/` directory
- **Index Caching**: Persistent storage of TF-IDF indices in `data/` directory
- No external databases or cloud storage dependencies - all processing remains local for privacy and control