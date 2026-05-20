from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/profile")
async def get_profile():
    return None

@router.patch("/profile")
async def update_profile():
    return None
