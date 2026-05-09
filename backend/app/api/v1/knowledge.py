# This endpoint lets business owners upload their
# product catalog, FAQs, and any other knowledge
# they want Ama to know about.
#
# Two ways to upload:
# 1. Plain text — paste text directly
# 2. Google Sheets URL — system reads the sheet automatically

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.rag_service import rag_service
import httpx
import csv
import io

router = APIRouter()


class TextKnowledgeRequest(BaseModel):
    """Upload knowledge as plain text"""
    business_id: str        # which business this is for
    doc_id: str             # name for this document e.g. "products"
    doc_type: str = "general"  # "products", "faqs", "policies"
    content: str            # the actual text content


class SheetKnowledgeRequest(BaseModel):
    """Upload knowledge from a Google Sheet"""
    business_id: str
    doc_id: str
    doc_type: str = "products"
    sheet_url: str          # the Google Sheets URL


class KnowledgeResponse(BaseModel):
    success: bool
    message: str
    chunks_created: int


@router.post("/knowledge/text", response_model=KnowledgeResponse)
async def upload_text_knowledge(request: TextKnowledgeRequest):
    """
    Upload business knowledge as plain text.
    
    Example — a business owner can paste:
    
    "Samsung A54 - GHS 3,200
     Colors: Blue, Black
     Camera: 50MP front, 32MP back
     Battery: 5000mAh
     Warranty: 1 year local warranty
     
     iPhone 15 - GHS 9,500
     Colors: Black, White, Pink
     Camera: 48MP
     Storage: 128GB
     Warranty: 1 year Apple warranty"
    
    Ama will then know all of this and answer
    questions accurately.
    """

    if not request.content.strip():
        raise HTTPException(
            status_code=400,
            detail="Content cannot be empty"
        )

    chunks_created = rag_service.index_document(
        business_id=request.business_id,
        document_text=request.content,
        doc_id=request.doc_id,
        doc_type=request.doc_type
    )

    return KnowledgeResponse(
        success=True,
        message=f"Successfully indexed '{request.doc_id}' into knowledge base",
        chunks_created=chunks_created
    )


@router.post("/knowledge/sheet", response_model=KnowledgeResponse)
async def upload_sheet_knowledge(request: SheetKnowledgeRequest):
    """
    Read a Google Sheet and index its contents.
    
    The business owner:
    1. Creates a Google Sheet with their products/FAQs
    2. Makes it public (anyone with link can view)
    3. Pastes the link here
    
    We read the sheet and convert it to text automatically.
    """

    try:
        # Extract the sheet ID from the URL
        # URL looks like:
        # https://docs.google.com/spreadsheets/d/SHEET_ID/edit
        sheet_id = _extract_sheet_id(request.sheet_url)

        if not sheet_id:
            raise HTTPException(
                status_code=400,
                detail="Invalid Google Sheets URL"
            )

        # Build the CSV export URL
        # Google Sheets can export any sheet as CSV automatically
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"

        # Download the CSV
        async with httpx.AsyncClient() as client:
            response = await client.get(csv_url, timeout=15.0)

            if response.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail="Could not read Google Sheet. Make sure it is set to 'Anyone with link can view'"
                )

            csv_content = response.text

        # Convert CSV rows into readable text
        # Each row becomes: "Product Name: X | Price: Y | Description: Z"
        document_text = _csv_to_text(csv_content)

        if not document_text.strip():
            raise HTTPException(
                status_code=400,
                detail="Sheet appears to be empty"
            )

        # Index the text into ChromaDB
        chunks_created = rag_service.index_document(
            business_id=request.business_id,
            document_text=document_text,
            doc_id=request.doc_id,
            doc_type=request.doc_type
        )

        return KnowledgeResponse(
            success=True,
            message=f"Successfully read Google Sheet and indexed {chunks_created} chunks",
            chunks_created=chunks_created
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error reading sheet: {str(e)}"
        )


@router.get("/knowledge/{business_id}/stats")
async def get_knowledge_stats(business_id: str):
    """
    Returns how much knowledge a business has stored.
    Useful for showing in the dashboard.
    """
    stats = rag_service.get_knowledge_stats(business_id)
    return {
        "business_id": business_id,
        **stats
    }


@router.post("/knowledge/search")
async def search_knowledge(
    business_id: str,
    query: str,
    top_k: int = 4
):
    """
    Test endpoint — search the knowledge base directly.
    Useful for testing what Ama knows before connecting WhatsApp.
    """
    results = rag_service.search(
        business_id=business_id,
        query=query,
        top_k=top_k
    )

    return {
        "query": query,
        "results_found": len(results),
        "results": results
    }


def _extract_sheet_id(url: str) -> str:
    """
    Extracts the sheet ID from a Google Sheets URL.
    
    Input:  https://docs.google.com/spreadsheets/d/ABC123XYZ/edit
    Output: ABC123XYZ
    """
    try:
        parts = url.split("/")
        d_index = parts.index("d")
        return parts[d_index + 1]
    except (ValueError, IndexError):
        return ""


def _csv_to_text(csv_content: str) -> str:
    """
    Converts CSV rows into readable text paragraphs.
    
    Input CSV:
    Product,Price,Description
    Samsung A54,3200,50MP camera phone
    iPhone 15,9500,Premium Apple phone
    
    Output text:
    Product: Samsung A54 | Price: 3200 | Description: 50MP camera phone
    Product: iPhone 15 | Price: 9500 | Description: Premium Apple phone
    """
    reader = csv.DictReader(io.StringIO(csv_content))
    lines = []

    for row in reader:
        # Convert each row to "Key: Value | Key: Value" format
        parts = [f"{key}: {value}" for key, value in row.items() if value.strip()]
        if parts:
            lines.append(" | ".join(parts))

    return "\n".join(lines)
