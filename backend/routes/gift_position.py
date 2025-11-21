from fastapi import APIRouter, Depends, HTTPException
from typing import List
from datetime import datetime, date
from ..models import GIFTPositionCheck, GIFTPositionCheckCreate, User
from ..auth import get_current_user
from ..database import get_database

router = APIRouter(prefix="/api/v1/gift-position", tags=["GIFT Position"])

@router.post("/checks", response_model=GIFTPositionCheck)
async def create_or_update_check(
    check_data: GIFTPositionCheckCreate,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Create or update a GIFT position check for a specific time slot"""
    today = date.today().isoformat()
    
    # Check if entry already exists
    existing = await db.gift_position_checks.find_one({
        "user_id": current_user.id,
        "date": today,
        "time": check_data.time
    })
    
    if existing:
        # Update existing entry
        update_data = {
            "turnover_report": check_data.turnover_report,
            "exit_portal": check_data.exit_portal,
            "matched": check_data.matched,
            "timestamp": datetime.utcnow()
        }
        
        await db.gift_position_checks.update_one(
            {"_id": existing["_id"]},
            {"$set": update_data}
        )
        
        updated = await db.gift_position_checks.find_one({"_id": existing["_id"]})
        updated["id"] = str(updated["_id"])
        return GIFTPositionCheck(**updated)
    else:
        # Create new entry
        check = {
            "user_id": current_user.id,
            "username": current_user.username,
            "date": today,
            "time": check_data.time,
            "turnover_report": check_data.turnover_report,
            "exit_portal": check_data.exit_portal,
            "matched": check_data.matched,
            "timestamp": datetime.utcnow()
        }
        
        result = await db.gift_position_checks.insert_one(check)
        check["_id"] = result.inserted_id
        check["id"] = str(result.inserted_id)
        return GIFTPositionCheck(**check)

@router.get("/checks/today", response_model=List[GIFTPositionCheck])
async def get_today_checks(
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get all checks for today for the current user"""
    today = date.today().isoformat()
    
    cursor = db.gift_position_checks.find({
        "user_id": current_user.id,
        "date": today
    }).sort("time", 1)
    
    checks = await cursor.to_list(length=100)
    for check in checks:
        check["id"] = str(check["_id"])
    
    return [GIFTPositionCheck(**check) for check in checks]

@router.get("/checks/date/{check_date}", response_model=List[GIFTPositionCheck])
async def get_checks_by_date(
    check_date: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get all checks for a specific date"""
    cursor = db.gift_position_checks.find({
        "user_id": current_user.id,
        "date": check_date
    }).sort("time", 1)
    
    checks = await cursor.to_list(length=100)
    for check in checks:
        check["id"] = str(check["_id"])
    
    return [GIFTPositionCheck(**check) for check in checks]

# Admin routes
@router.get("/admin/checks/all", response_model=List[GIFTPositionCheck])
async def get_all_checks(
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get all checks (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    cursor = db.gift_position_checks.find().sort("date", -1).sort("time", 1)
    checks = await cursor.to_list(length=1000)
    
    for check in checks:
        check["id"] = str(check["_id"])
    
    return [GIFTPositionCheck(**check) for check in checks]
