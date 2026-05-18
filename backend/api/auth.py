from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register")
async def register():
    return None

@router.post("/login")
async def login():
    return None

@router.post("/refresh")
async def refresh_token():
    return None

@router.get("/me")
async def get_me():
    return None
