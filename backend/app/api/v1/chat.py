# This file defines the /chat endpoint.
#
# Right now it is a SIMPLE version — no database, no RAG.
# Just: receive message → ask Groq → return reply
#
# We will upgrade it step by step to add:
# - customer history (database)
# - product knowledge (ChromaDB/RAG)
# - WhatsApp integration

from fastapi import APIRouter
from pydantic import BaseModel
from app.services.ai_service import generate_reply

# APIRouter is like a mini FastAPI app
# We group related endpoints together in routers
# then attach them to the main app
router = APIRouter()


# Pydantic models define what data the endpoint
# accepts and returns. FastAPI validates this automatically.
# If someone sends wrong data, FastAPI rejects it with a clear error.

class ChatRequest(BaseModel):
    """What the caller must send to this endpoint"""
    message: str                    # the customer's message
    business_name: str = "Our Shop" # which business the AI represents
    business_type: str = "shop"     # type of business
    ai_name: str = "Ama"            # AI assistant's name

class ChatResponse(BaseModel):
    """What this endpoint sends back"""
    reply: str      # the AI's reply
    ai_name: str    # which AI assistant replied


# This is the SYSTEM PROMPT.
# It is the set of instructions the AI reads BEFORE
# seeing the customer's message.
# Think of it as the AI's job description and briefing.
#
# The AI will always stay in character based on these instructions.
# This is called "prompt engineering" — crafting instructions
# that make the AI behave exactly how you want.

def build_system_prompt(
    business_name: str,
    business_type: str,
    ai_name: str
) -> str:
    return f"""You are {ai_name}, a friendly and helpful AI sales assistant for {business_name}, a {business_type}.

Your personality:
- Warm, friendly, and professional
- You speak like a real person on WhatsApp — not like a formal email
- You use short paragraphs (this is WhatsApp, not an essay)
- You occasionally use relevant emojis to be friendly (but not too many)
- You always try to be helpful and move the customer toward a purchase

Your job:
- Answer customer questions about the business
- Recommend products or services when relevant  
- Capture customer interest (ask for their name, what they need)
- If you don't know something, say so honestly
- Never make up prices or information you are not sure about

Important rules:
- Keep replies SHORT and conversational — this is WhatsApp
- Never write long paragraphs — use short sentences
- Always end with a question or next step to keep conversation going
- If customer seems interested in buying, ask how you can help them complete the purchase

You are representing {business_name}. Be their best employee."""


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Simple chat endpoint.
    
    Send a message, get an AI reply back.
    
    This is the foundation — we will build on top of this
    to add customer memory, product knowledge, and WhatsApp.
    """

    # Build the system prompt using the business details
    system_prompt = build_system_prompt(
        business_name=request.business_name,
        business_type=request.business_type,
        ai_name=request.ai_name
    )

    # Call the AI service — it handles Groq or Ollama
    reply = await generate_reply(
        system_prompt=system_prompt,
        user_message=request.message
    )

    return ChatResponse(
        reply=reply,
        ai_name=request.ai_name
    )
