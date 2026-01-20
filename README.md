# VASP Wiki RAG Agent

A fullstack RAG (Retrieval-Augmented Generation) agent for querying the VASP Wiki using Google's Gemini 2.5 Flash API.

## Features

- Scrapes and indexes the VASP Wiki documentation
- Semantic search using FAISS vector store
- Query interface with Gemini 2.5 Flash API
- React frontend with citation support
- FastAPI backend

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
cd backend
uvicorn main:app --reload --host localhost --port 8000
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
