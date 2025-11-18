#!/usr/bin/env python3
"""
Mock backend for testing frontend features
Provides sample data for Analytics, Search, Upload, and Tagging
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="Mock RAG Backend")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data storage
mock_documents = []
mock_tags = {}
mock_conversations = []

# Initialize some mock data
def init_mock_data():
    global mock_documents, mock_tags, mock_conversations

    # Mock documents
    for i in range(15):
        doc_id = f"doc_{i+1}"
        mock_documents.append({
            "doc_id": doc_id,
            "filename": f"sample_document_{i+1}.pdf",
            "upload_date": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat(),
            "file_size": random.randint(100000, 5000000),
            "status": "processed",
            "chunk_count": random.randint(10, 50)
        })

        # Add some tags
        tag_pool = ["technical", "financial", "marketing", "sales", "research", "legal", "hr", "product"]
        doc_tags = random.sample(tag_pool, random.randint(1, 3))
        mock_tags[doc_id] = doc_tags

    # Mock conversations
    for i in range(25):
        mock_conversations.append({
            "conversation_id": f"conv_{i+1}",
            "created_at": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
            "message_count": random.randint(1, 10),
            "last_message": f"Sample query {i+1}: How does the system work?",
            "user_id": "test_user"
        })

init_mock_data()

# Serve static files
app.mount("/static", StaticFiles(directory="."), name="static")

@app.get("/")
async def root():
    return FileResponse("admin.html")

@app.get("/admin.html")
async def admin():
    return FileResponse("admin.html")

# Analytics endpoints
@app.get("/api/analytics/overview")
async def analytics_overview():
    return JSONResponse(content={
        "total_queries": 1543,
        "total_cost": 45.67,
        "avg_response_time": 2.3,
        "success_rate": 94.5,
        "total_documents": len(mock_documents),
        "active_conversations": 12
    })

@app.get("/api/analytics/trends")
async def analytics_trends(days: int = 30):
    dates = []
    queries = []
    costs = []
    response_times = []
    success_rates = []
    rag_usage = []

    for i in range(days):
        date = datetime.now() - timedelta(days=days-i-1)
        dates.append(date.strftime("%Y-%m-%d"))
        queries.append(random.randint(30, 80))
        costs.append(round(random.uniform(0.5, 3.0), 2))
        response_times.append(round(random.uniform(1.5, 4.0), 2))
        success_rates.append(round(random.uniform(85, 98), 1))
        rag_usage.append(random.randint(20, 60))

    return JSONResponse(content={
        "dates": dates,
        "queries": queries,
        "costs": costs,
        "response_times": response_times,
        "success_rates": success_rates,
        "rag_usage": rag_usage
    })

# Document endpoints
@app.get("/api/documents")
async def list_documents():
    return JSONResponse(content={"documents": mock_documents})

@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    doc_id = f"doc_{len(mock_documents) + 1}"
    new_doc = {
        "doc_id": doc_id,
        "filename": file.filename,
        "upload_date": datetime.now().isoformat(),
        "file_size": 0,  # Mock size
        "status": "processing",
        "chunk_count": 0
    }
    mock_documents.append(new_doc)
    mock_tags[doc_id] = []

    return JSONResponse(content={
        "success": True,
        "doc_id": doc_id,
        "filename": file.filename,
        "status": "processing"
    })

@app.delete("/api/documents/{doc_id}")
async def delete_document(doc_id: str):
    global mock_documents
    mock_documents = [d for d in mock_documents if d["doc_id"] != doc_id]
    if doc_id in mock_tags:
        del mock_tags[doc_id]
    return JSONResponse(content={"success": True})

# Tag endpoints
@app.get("/api/documents/{doc_id}/tags")
async def get_document_tags(doc_id: str):
    tags = mock_tags.get(doc_id, [])
    return JSONResponse(content={"tags": tags})

@app.post("/api/documents/{doc_id}/tags")
async def add_document_tags(doc_id: str, tags: List[str]):
    if doc_id not in mock_tags:
        mock_tags[doc_id] = []

    for tag in tags:
        tag_lower = tag.lower().strip()
        if tag_lower not in mock_tags[doc_id]:
            mock_tags[doc_id].append(tag_lower)

    return JSONResponse(content={"success": True, "tags": mock_tags[doc_id]})

@app.delete("/api/documents/{doc_id}/tags/{tag}")
async def remove_document_tag(doc_id: str, tag: str):
    if doc_id in mock_tags and tag in mock_tags[doc_id]:
        mock_tags[doc_id].remove(tag)
    return JSONResponse(content={"success": True, "tags": mock_tags.get(doc_id, [])})

@app.get("/api/tags/autocomplete")
async def autocomplete_tags(prefix: str = "", limit: int = 10):
    # Get all unique tags
    all_tags = set()
    for tags in mock_tags.values():
        all_tags.update(tags)

    # Filter by prefix
    matching = [tag for tag in sorted(all_tags) if tag.startswith(prefix.lower())]
    return JSONResponse(content={"suggestions": matching[:limit]})

@app.get("/api/tags/search")
async def search_by_tags(tags: str, match_all: bool = False):
    tag_list = [t.strip().lower() for t in tags.split(',')]
    matching_docs = []

    for doc_id, doc_tags in mock_tags.items():
        if match_all:
            if all(tag in doc_tags for tag in tag_list):
                matching_docs.append(doc_id)
        else:
            if any(tag in doc_tags for tag in tag_list):
                matching_docs.append(doc_id)

    return JSONResponse(content={"matching_documents": matching_docs})

# Conversation endpoints
@app.get("/api/conversations")
async def list_conversations():
    return JSONResponse(content={"conversations": mock_conversations})

@app.get("/api/conversations/search")
async def search_conversations(
    search_query: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    filtered = mock_conversations.copy()

    # Filter by search query
    if search_query:
        filtered = [c for c in filtered if search_query.lower() in c["last_message"].lower()]

    # Filter by date range
    if start_date:
        start = datetime.fromisoformat(start_date)
        filtered = [c for c in filtered if datetime.fromisoformat(c["created_at"]) >= start]

    if end_date:
        end = datetime.fromisoformat(end_date)
        filtered = [c for c in filtered if datetime.fromisoformat(c["created_at"]) <= end]

    # Pagination
    total = len(filtered)
    paginated = filtered[offset:offset + limit]

    return JSONResponse(content={
        "conversations": paginated,
        "total": total,
        "limit": limit,
        "offset": offset
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
