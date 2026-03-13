from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware  # Standard FastAPI CORS
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime, timedelta
from bson import ObjectId
from passlib.context import CryptContext
from jose import JWTError, jwt
import secrets
import shortuuid

# Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).parent
# Safely load .env only if it exists (protects Vercel from crashing)
if (ROOT_DIR / '.env').exists():
    load_dotenv(ROOT_DIR / '.env')

# Safely get Environment Variables
MONGO_URL = os.getenv('MONGO_URL')
DB_NAME = os.getenv('DB_NAME', 'ready-research') # Added a default fallback

if not MONGO_URL:
    logger.error("🚨 MONGO_URL environment variable is missing!")

# MongoDB connection
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# JWT Settings
SECRET_KEY = os.getenv('JWT_SECRET_KEY', secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security
security = HTTPBearer()

# ==================== APP INITIALIZATION ====================

app = FastAPI()

# Create a router without an extra /api prefix.
api_router = APIRouter(prefix="")

# ==================== HELPERS ====================

def str_id() -> str:
    return str(ObjectId())

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = await db.users.find_one({"id": user_id})
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# ==================== MODELS ====================

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    phone: Optional[str] = Field(None, max_length=20)
    display_name: str = Field(..., min_length=2, max_length=50)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    phone: Optional[str]
    display_name: str
    created_at: datetime
    friends_count: int = 0
    posts_count: int = 0

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# ==================== ENDPOINTS ====================

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "textblurb-api"}

@api_router.post("/auth/register", response_model=TokenResponse)
async def register(user_input: UserRegister):
    existing_user = await db.users.find_one({"email": user_input.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = str_id()
    user_dict = {
        "id": user_id,
        "email": user_input.email,
        "password_hash": get_password_hash(user_input.password),
        "phone": user_input.phone,
        "display_name": user_input.display_name,
        "created_at": datetime.utcnow(),
        "friends": [],
        "blocked_users": [],
    }
    
    await db.users.insert_one(user_dict)
    access_token = create_access_token({"sub": user_id})
    
    return TokenResponse(
        access_token=access_token,
        user=UserResponse(
            id=user_id,
            email=user_input.email,
            phone=user_input.phone,
            display_name=user_input.display_name,
            created_at=user_dict["created_at"]
        )
    )

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(user_input: UserLogin):
    user = await db.users.find_one({"email": user_input.email})
    if not user or not verify_password(user_input.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    access_token = create_access_token({"sub": user["id"]})
    return TokenResponse(
        access_token=access_token,
        user=UserResponse(
            id=user["id"],
            email=user["email"],
            display_name=user["display_name"],
            created_at=user["created_at"]
        )
    )

# Include the router
app.include_router(api_router)

# CORS: local dev + explicit Vercel domain + fallback regex
_cors_origins = [
    "http://localhost:8081",
    "http://127.0.0.1:8081",
    "https://ready-research.vercel.app" # The crucial addition
]
if os.getenv("FRONTEND_URL"):
    _cors_origins.append(os.getenv("FRONTEND_URL").rstrip("/"))
if os.getenv("CORS_ORIGINS"):
    _cors_origins.extend(o.strip() for o in os.getenv("CORS_ORIGINS").split(",") if o.strip())

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_origin_regex=r"^https://[^/]+\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()