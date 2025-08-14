from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from typing import Optional, List
import os
import uuid
from datetime import datetime

from .database import get_database
from .models import ContractResponse, ContractStatus, ContractListResponse
from .contract_processor import ContractProcessor
from .config import settings

app = FastAPI(title="Contract Intelligence API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize contract processor
processor = ContractProcessor()

@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup"""
    await get_database()

@app.post("/contracts/upload", response_model=dict)
async def upload_contract(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """Upload and process a contract file"""
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    if file.size > 50 * 1024 * 1024:  # 50MB limit
        raise HTTPException(status_code=400, detail="File size exceeds 50MB limit")
    
    # Generate unique contract ID
    contract_id = str(uuid.uuid4())
    
    # Save uploaded file
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, f"{contract_id}.pdf")
    
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # Initialize contract record
    db = await get_database()
    await db.contracts.insert_one({
        "contract_id": contract_id,
        "filename": file.filename,
        "file_path": file_path,
        "status": "pending",
        "progress": 0,
        "uploaded_at": datetime.utcnow(),
        "processed_at": None,
        "extracted_data": None,
        "score": None,
        "gaps": []
    })
    
    # Start background processing
    background_tasks.add_task(processor.process_contract, contract_id, file_path)
    
    return {"contract_id": contract_id, "message": "Contract uploaded successfully"}

@app.get("/contracts/{contract_id}/status", response_model=ContractStatus)
async def get_contract_status(contract_id: str):
    """Get contract processing status"""
    db = await get_database()
    contract = await db.contracts.find_one({"contract_id": contract_id})
    
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    return ContractStatus(
        contract_id=contract_id,
        status=contract["status"],
        progress=contract["progress"],
        error=contract.get("error")
    )

@app.get("/contracts/{contract_id}", response_model=ContractResponse)
async def get_contract_data(contract_id: str):
    """Get processed contract data"""
    db = await get_database()
    contract = await db.contracts.find_one({"contract_id": contract_id})
    
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    if contract["status"] != "completed":
        raise HTTPException(status_code=400, detail="Contract processing not completed")
    
    return ContractResponse(
        contract_id=contract_id,
        filename=contract["filename"],
        status=contract["status"],
        extracted_data=contract["extracted_data"],
        score=contract["score"],
        gaps=contract["gaps"],
        processed_at=contract["processed_at"]
    )

@app.get("/contracts", response_model=ContractListResponse)
async def list_contracts(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    status: Optional[str] = None,
    min_score: Optional[float] = None
):
    """Get paginated list of contracts with optional filtering"""
    db = await get_database()
    
    # Build filter query
    filter_query = {}
    if status:
        filter_query["status"] = status
    if min_score is not None:
        filter_query["score"] = {"$gte": min_score}
    
    # Get total count
    total = await db.contracts.count_documents(filter_query)
    
    # Get paginated results
    skip = (page - 1) * limit
    cursor = db.contracts.find(filter_query).skip(skip).limit(limit).sort("uploaded_at", -1)
    contracts = await cursor.to_list(length=limit)
    
    # Format response
    contract_list = []
    for contract in contracts:
        contract_list.append({
            "contract_id": contract["contract_id"],
            "filename": contract["filename"],
            "status": contract["status"],
            "score": contract.get("score"),
            "uploaded_at": contract["uploaded_at"],
            "processed_at": contract.get("processed_at")
        })
    
    return ContractListResponse(
        contracts=contract_list,
        total=total,
        page=page,
        limit=limit,
        pages=(total + limit - 1) // limit
    )

@app.get("/contracts/{contract_id}/download")
async def download_contract(contract_id: str):
    """Download original contract file"""
    db = await get_database()
    contract = await db.contracts.find_one({"contract_id": contract_id})
    
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    file_path = contract["file_path"]
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Contract file not found")
    
    return FileResponse(
        path=file_path,
        filename=contract["filename"],
        media_type="application/pdf"
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
