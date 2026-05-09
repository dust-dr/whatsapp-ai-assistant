from fastapi import APIRouter
from pydantic import BaseModel
from app.services.ai_service import generate_reply
from app.services.rag_service import rag_service

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    business_id: str = ""           # if provided, Ama uses real knowledge
    business_name: str = "Our Shop"
    business_type: str = "shop"
    ai_name: str = "Ama"


class ChatResponse(BaseModel):
    reply: str
    ai_name: str
    knowledge_used: bool            # tells us if RAG found anything


def build_system_prompt(
    business_name: str,
    business_type: str,
    ai_name: str,
    knowledge_context: str
) -> str:
    """
    Builds the AI's instructions.
    
    If we have real knowledge from ChromaDB, we include it
    and tell Ama to ONLY use that knowledge.
    
    If we have no knowledge, Ama uses general knowledge
    but admits she doesn't have specific details.
    """

    if knowledge_context:
        knowledge_section = f"""
IMPORTANT: Use ONLY the information below to answer questions.
Do not make up prices, products, or details not listed here.
If the customer asks about something not in this list, 
say you will check and get back to them.

BUSINESS KNOWLEDGE:
{knowledge_context}
"""
    else:
        knowledge_section = """
You don't have specific product information yet.
Be helpful but honest — don't make up specific prices or products.
Encourage the customer to ask questions and tell them 
you'll connect them with the right person for details.
"""

    return f"""You are {ai_name}, a friendly AI sales assistant for {business_name}, a {business_type}.

{knowledge_section}

Your communication style:
- Warm, friendly, and professional
- Short messages — this is WhatsApp not email
- Use emojis naturally but not excessively
- Always end with a question or next step
- If customer wants to buy, help them take the next step

You represent {business_name}. Be their best employee."""


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint with RAG support.
    
    If business_id is provided, searches ChromaDB for
    relevant knowledge before generating a reply.
    
    If no business_id, works as a generic assistant.
    """

    knowledge_context = ""
    knowledge_used = False

    # If business_id is provided, search for relevant knowledge
    if request.business_id:
        relevant_chunks = rag_service.search(
            business_id=request.business_id,
            query=request.message,
            top_k=4
        )

        if relevant_chunks:
            # Join the chunks into one context block
            knowledge_context = "\n\n".join(relevant_chunks)
            knowledge_used = True

    # Build system prompt with or without knowledge
    system_prompt = build_system_prompt(
        business_name=request.business_name,
        business_type=request.business_type,
        ai_name=request.ai_name,
        knowledge_context=knowledge_context
    )

    # Generate reply
    reply = await generate_reply(
        system_prompt=system_prompt,
        user_message=request.message
    )

    return ChatResponse(
        reply=reply,
        ai_name=request.ai_name,
        knowledge_used=knowledge_used
    )
