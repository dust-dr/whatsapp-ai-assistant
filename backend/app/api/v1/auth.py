from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.business import Business
from app.schemas.auth import (
    BusinessRegisterRequest,
    BusinessLoginRequest,
    TokenResponse,
    BusinessResponse,
    MessageResponse
)
from app.core.security import hash_password, verify_password, create_access_token
from app.core.dependencies import get_current_business

router = APIRouter()


@router.post("/auth/register", response_model=TokenResponse)
def register(request: BusinessRegisterRequest, db: Session = Depends(get_db)):
    existing_email = db.query(Business).filter(
        Business.email == request.email
    ).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists."
        )

    existing_phone = db.query(Business).filter(
        Business.phone_number == request.phone_number
    ).first()
    if existing_phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this phone number already exists."
        )

    business = Business(
        name=request.name,
        email=request.email,
        hashed_password=hash_password(request.password),
        phone_number=request.phone_number,
        business_type=request.business_type,
        description=request.description,
        ai_persona_name=request.ai_persona_name or "Ama"
    )
    db.add(business)
    db.commit()
    db.refresh(business)

    token = create_access_token(str(business.id))

    return TokenResponse(
        access_token=token,
        business=BusinessResponse(
            id=str(business.id),
            name=business.name,
            email=business.email,
            phone_number=business.phone_number,
            business_type=business.business_type,
            ai_persona_name=business.ai_persona_name,
            is_active=business.is_active,
            whatsapp_connected=business.whatsapp_connected
        )
    )


@router.post("/auth/login", response_model=TokenResponse)
def login(request: BusinessLoginRequest, db: Session = Depends(get_db)):
    business = db.query(Business).filter(
        Business.email == request.email
    ).first()

    if not business or not verify_password(request.password, business.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password."
        )

    if not business.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated."
        )

    token = create_access_token(str(business.id))

    return TokenResponse(
        access_token=token,
        business=BusinessResponse(
            id=str(business.id),
            name=business.name,
            email=business.email,
            phone_number=business.phone_number,
            business_type=business.business_type,
            ai_persona_name=business.ai_persona_name,
            is_active=business.is_active,
            whatsapp_connected=business.whatsapp_connected
        )
    )


@router.get("/auth/me", response_model=BusinessResponse)
def get_me(business: Business = Depends(get_current_business)):
    return BusinessResponse(
        id=str(business.id),
        name=business.name,
        email=business.email,
        phone_number=business.phone_number,
        business_type=business.business_type,
        ai_persona_name=business.ai_persona_name,
        is_active=business.is_active,
        whatsapp_connected=business.whatsapp_connected
    )
