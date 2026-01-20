# VASP Wiki RAG Agent

A fullstack RAG (Retrieval-Augmented Generation) agent for querying the VASP Wiki using Google's Gemini 2.5 Flash API.

## Demo

![Application Demo](./Application_Demo_frontend.gif)

## Features

### Backend
- **Wiki Scraper & Processor**: Automatically crawls and indexes documentation from the VASP Wiki, handling HTML cleaning and content structuring.
- **RAG Pipeline**: Implements a robust Retrieval-Augmented Generation flow using custom chunking strategies.
- **Semantic Search**: Powered by FAISS (Facebook AI Similarity Search) for fast and accurate document retrieval.
- **Gemini Integration**: Leverages Google's Gemini 2.5 Flash API for advanced natural language reasoning and synthesis.
- **FastAPI Framework**: High-performance RESTful API with asynchronous support for efficient query handling.

### Frontend
- **React + Vite**: A modern, fast, and responsive user interface.
- **Interactive Query Interface**: Clean search experience for asking complex VASP-related questions.
- **Smart Citations**: Automatically attributes information to original VASP Wiki pages, providing direct links for verification.
- **Rich Text Rendering**: Full support for Markdown and code blocks to display technical documentation clearly.

## Setup

### 1. Create Virtual Environment

**Option A: Using the setup script (recommended)**
```bash
python scripts/setup_venv.py
```

**Option B: Manual setup**
```bash
python -m venv venv

# Activate virtual environment:
# On Windows (PowerShell):
venv\Scripts\activate
# On Windows (Git Bash) or Linux/Mac:
source venv/bin/activate
```

### 2. Install Dependencies

If using manual setup:
```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 3. Configure Environment

Copy `env.template` to `.env` and fill in your Gemini API key:

```bash
# On Windows (Git Bash) or Linux/Mac:
cp env.template .env

# On Windows (PowerShell):
# Copy-Item env.template .env

# Edit .env and add your GEMINI_API_KEY
```

### 4. Download Wiki and Build Index

```bash
python scripts/download_wiki.py
python scripts/build_index.py
```

### 5. Start Backend Server

```bash
uvicorn backend.main:app --reload --host localhost --port 8000
```

### 6. Start Frontend (in another terminal)

```bash
cd frontend
npm install
npm run dev
```

## Usage

1. Open the frontend in your browser (typically http://localhost:5173)
2. Enter your question about VASP
3. View the answer with citations to source wiki pages

## Project Structure

- `backend/` - FastAPI backend with RAG agent
- `frontend/` - React frontend application
- `scripts/` - Utility scripts for data processing
- `data/` - Scraped wiki data (not in git)
- `embeddings/` - FAISS vector store (not in git)

## License

This project is for educational purposes. Please respect VASP Wiki's terms of use.
