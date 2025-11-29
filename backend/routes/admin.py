# backend/routes/admin.py

from fastapi import APIRouter, HTTPException, status, Depends, Query
from fastapi.responses import StreamingResponse
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from models import (
    UserCreate, UserResponse, UserUpdate, SOPTypeInfo, SOPActivityResponse,
    SOPDefinition, SOPDefinitionCreate, SOPDefinitionUpdate
)
from database import get_user_collection, get_sop_activity_collection, get_db, get_sop_definition_collection
from auth import require_admin, get_current_active_user
from bson import ObjectId
from zoneinfo import ZoneInfo
import logging
import io
import csv

from services.report_utils import generate_sop_backup_html_report ,  generate_us_position_html_report

logger = logging.getLogger(__name__)
admin_router = APIRouter()

@admin_router.post("/sop-definitions", response_model=SOPDefinition)
async def create_sop_definition(
    sop_data: SOPDefinitionCreate,
    current_user: dict = Depends(require_admin)
):
    """Create a new SOP definition (admin only)"""
    try:
        sop_definitions_collection = get_sop_definition_collection()
        
        if sop_definitions_collection.find_one({"sop_type": sop_data.sop_type}):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"SOP type '{sop_data.sop_type}' already exists."
            )
        
        new_sop = SOPDefinition(
            sop_type=sop_data.sop_type,
            name=sop_data.name,
            description=sop_data.description,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        result = sop_definitions_collection.insert_one(new_sop.model_dump(by_alias=True, exclude_none=True))
        created_sop = sop_definitions_collection.find_one({"_id": result.inserted_id})
        logger.info(f"SOP definition '{new_sop.sop_type}' created by {current_user['username']}")
        return SOPDefinition(**created_sop)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating SOP definition: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create SOP definition"
        )

@admin_router.put("/sop-definitions/{sop_id}", response_model=SOPDefinition)
async def update_sop_definition(
    sop_id: str,
    sop_data: SOPDefinitionUpdate,
    current_user: dict = Depends(require_admin)
):
    """Update an existing SOP definition (admin only)"""
    try:
        sop_definitions_collection = get_sop_definition_collection()
        
        existing_sop = sop_definitions_collection.find_one({"_id": sop_id}) 
        
        if not existing_sop:
            try:
                existing_sop = sop_definitions_collection.find_one({"_id": ObjectId(sop_id)})
            except Exception:
                pass
            
            if not existing_sop:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="SOP definition not found"
                )
        
        update_fields = sop_data.model_dump(exclude_unset=True, exclude_none=True)
        if not update_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        update_fields["updated_at"] = datetime.utcnow()
        
        sop_definitions_collection.update_one(
            {"_id": existing_sop["_id"]},
            {"$set": update_fields}
        )
        
        updated_sop = sop_definitions_collection.find_one({"_id": existing_sop["_id"]})
        logger.info(f"SOP definition '{existing_sop.get('sop_type')}' updated by {current_user['username']}")
        return SOPDefinition(**updated_sop)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating SOP definition {sop_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update SOP definition"
        )
@admin_router.get("/sop-definitions", response_model=List[SOPDefinition])
async def get_all_sop_definitions(current_user: dict = Depends(require_admin)):
    """Get all SOP definitions (admin only)"""
    try:
        sop_definitions_collection = get_sop_definition_collection()
        
        all_sop_definitions = list(sop_definitions_collection.find({}).sort("name", 1))
        
        return [SOPDefinition(**sop_def) for sop_def in all_sop_definitions]
        
    except Exception as e:
        logger.error(f"Get SOP definitions error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve SOP definitions"
        )

@admin_router.delete("/sop-definitions/{sop_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sop_definition(
    sop_id: str,
    current_user: dict = Depends(require_admin)
):
    """Delete an SOP definition (admin only)"""
    try:
        sop_definitions_collection = get_sop_definition_collection()
        
        result = sop_definitions_collection.delete_one({"_id": sop_id})
        
        if result.deleted_count == 0:
            try:
                result = sop_definitions_collection.delete_one({"_id": ObjectId(sop_id)})
            except Exception:
                pass
            
            if result.deleted_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="SOP definition not found"
                )
        
        logger.info(f"SOP definition {sop_id} deleted by {current_user['username']}")
        return
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting SOP definition {sop_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete SOP definition"
        )

@admin_router.get("/sop-types", response_model=List[SOPTypeInfo])
async def get_sop_types_with_activity(current_user: dict = Depends(require_admin)):
    """Get all SOP types from definitions, enriched with activity counts and last activity dates"""
    try:
        sop_definitions_collection = get_sop_definition_collection()
        sop_activity_collection = get_sop_activity_collection()
        
        all_sop_definitions = list(sop_definitions_collection.find({}).sort("name", 1))
        
        sop_types_info = []
        for sop_def in all_sop_definitions:
            sop_type_id = sop_def["sop_type"]
            
            activity_pipeline = [
                {"$match": {"sop_type": sop_type_id}},
                {"$group": {
                    "_id": "$sop_type",
                    "activity_count": {"$sum": 1},
                    "last_activity": {"$max": "$completed_at"}
                }}
            ]
            activity_result = list(sop_activity_collection.aggregate(activity_pipeline))
            
            activity_count = 0
            last_activity = None
            if activity_result:
                activity_count = activity_result[0]["activity_count"]
                last_activity = activity_result[0]["last_activity"]
            
            sop_types_info.append(SOPTypeInfo(
                id=str(sop_def["_id"]),
                sop_type=sop_type_id,
                name=sop_def["name"],
                description=sop_def.get("description"),
                activity_count=activity_count,
                last_activity=last_activity
            ))
        
        return sop_types_info
        
    except Exception as e:
        logger.error(f"Get SOP types error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve SOP types"
        )

@admin_router.get("/us-position-report")
async def download_us_position_report(
    report_date: Optional[str] = Query(None),
    current_user: dict = Depends(require_admin)
):
    """Download US Position data as an HTML report (admin only)"""
    try:
        db = get_db()
        us_position_collection = db["us_position_data"]
        
        if report_date:
            us_data = us_position_collection.find_one({"date": report_date})
        else:
            us_data = us_position_collection.find_one(sort=[("date", -1)])
        
        if not us_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No US Position data found for date: {report_date if report_date else 'latest'}"
            )
        
        html_content = generate_us_position_html_report(us_data, current_user["username"])
        
        filename = f"us_position_report_{us_data.get('date', datetime.now().strftime('%Y-%m-%d'))}.html"
        
        return StreamingResponse(
            io.StringIO(html_content),
            media_type="text/html",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download US Position report error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate US Position report"
        )

@admin_router.post("/reset-sop-type/{sop_type}")
async def reset_sop_type_with_backup(
    sop_type: str,
    current_user: dict = Depends(require_admin)
):
    """Reset specific SOP type with backup generation"""
    try:
        sop_collection = get_sop_activity_collection()
        
        activities = list(sop_collection.find({"sop_type": sop_type}).sort("completed_at", -1))
        
        logger.info(f"Found {len(activities)} activities for SOP type '{sop_type}' before generating backup report.")

        if not activities:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No activities found for SOP type: {sop_type} to backup."
            )
        
        html_content = generate_sop_backup_html_report(activities, sop_type, current_user["username"])
        
        delete_result = sop_collection.delete_many({"sop_type": sop_type})
        
        us_position_deleted = 0
        if sop_type == "us_position_sop":
            db = get_db()
            us_position_collection = db["us_position_data"]
            us_delete_result = us_position_collection.delete_many({})
            us_position_deleted = us_delete_result.deleted_count
        
        logger.info(f"SOP type {sop_type} reset by admin {current_user['username']}: {delete_result.deleted_count} activities deleted")
        
        filename = f"sop_backup_{sop_type}_{datetime.now().strftime('%Y_%m_%d_%H_%M')}.html"
        
        return StreamingResponse(
            io.StringIO(html_content),
            media_type="text/html",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reset SOP type error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset SOP type"
        )

@admin_router.get("/users", response_model=List[UserResponse])
async def get_all_users(current_user: dict = Depends(require_admin)):
    """Get all users (admin only)"""
    try:
        user_collection = get_user_collection()
        users = list(user_collection.find({}))
        
        return [
            UserResponse(
                id=str(user["_id"]),
                username=user["username"],
                name=user.get("name"),
                email=user["email"],
                role=user.get("role", "user"),
                is_active=user.get("is_active", True),
                shift=user.get("shift"),
                allowed_sops=user.get("allowed_sops", [])

            )
            for user in users
        ]
    except Exception as e:
        logger.error(f"Get users error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )

@admin_router.post("/users", response_model=dict)
async def create_user(
    user_data: UserCreate,
    current_user: dict = Depends(require_admin)
):
    """Create a new user (admin only)"""
    try:
        from auth import get_password_hash
        user_collection = get_user_collection()

        # Check if user already exists
        if user_collection.find_one({"$or": [{"email": user_data.email}, {"username": user_data.username}]}):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email or username already exists"
            )

        # Create new user
        new_user = {
            "username": user_data.username,
            "name": user_data.name,
            "email": user_data.email,
            "password": get_password_hash(user_data.password),
            "role": "user",
            "is_active": True,
            "shift": user_data.shift,
            "allowed_sops": user_data.allowed_sops or []

        }

        result = user_collection.insert_one(new_user)
        logger.info(f"User created: {user_data.username}")

        return {"message": "User created successfully", "user_id": str(result.inserted_id)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@admin_router.get("/users/by-shift")
async def get_users_by_shift(current_user: dict = Depends(get_current_active_user)):
    """Get all users grouped by shift"""
    try:
        user_collection = get_user_collection()
        users = list(user_collection.find({}))
        
        shifts = {
            "Morning": [],
            "Day": [],
            "Night": [],
            "Unassigned": []
        }
        
        for user in users:
            shift = user.get("shift", "Unassigned")
            if shift not in shifts:
                shifts[shift] = []
            
            shifts[shift].append({
                "id": str(user["_id"]),
                "username": user["username"],
                "name": user.get("name"),
                "email": user["email"],
                "shift": user.get("shift"),
                "shift_assigned_by": user.get("shift_assigned_by"),
                "shift_assigned_at": user.get("shift_assigned_at")
            })
        
        return shifts
        
    except Exception as e:
        logger.error(f"Get users by shift error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users by shift"
        )

@admin_router.get("/users/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: str,
    current_user: dict = Depends(require_admin)
):
    """Get user by ID (admin only)"""
    try:
        user_collection = get_user_collection()
        user = user_collection.find_one({"_id": ObjectId(user_id)})
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return UserResponse(
            id=str(user["_id"]),
            username=user["username"],
            name=user.get("name"),
            email=user["email"],
            role=user.get("role", "user"),
            is_active=user.get("is_active", True),
            shift=user.get("shift"),
            allowed_sops=user.get("allowed_sops", [])

        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user by ID error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user"
        )

@admin_router.put("/users/{user_id}", response_model=dict)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user: dict = Depends(require_admin)
):
    """Update user (admin only)"""
    try:
        from auth import get_password_hash
        user_collection = get_user_collection()
        
        user = user_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        update_data = {}
        if user_data.username is not None:
            update_data["username"] = user_data.username
        if user_data.name is not None:
            update_data["name"] = user_data.name
        if user_data.email is not None:
            update_data["email"] = user_data.email
        if user_data.password is not None:
            update_data["password"] = get_password_hash(user_data.password)
        if user_data.role is not None:
            update_data["role"] = user_data.role
        if user_data.is_active is not None:
            update_data["is_active"] = user_data.is_active
        if user_data.shift is not None:
            update_data["shift"] = user_data.shift
        if user_data.allowed_sops is not None:
            update_data["allowed_sops"] = user_data.allowed_sops
        if update_data:
            user_collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_data}
            )
            logger.info(f"User updated: {user_id}")

        return {"message": "User updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )

@admin_router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: dict = Depends(require_admin)
):
    """Delete user (admin only)"""
    try:
        user_collection = get_user_collection()
        
        user = user_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        user_collection.delete_one({"_id": ObjectId(user_id)})
        logger.info(f"User deleted: {user_id}")

        return {"message": "User deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )

@admin_router.post("/reset-all-sops")
async def reset_all_sops(current_user: dict = Depends(require_admin)):
    """Reset ALL SOP data (admin only)"""
    try:
        db = get_db()

        sop_result = db['sop_activities'].delete_many({})
        
        us_position_result = db['us_position_data'].delete_many({})
        
        total_deleted = sop_result.deleted_count + us_position_result.deleted_count

        logger.info(f"All SOP data reset manually by admin {current_user['username']}")
        return {
            "message": "All SOP data reset successfully", 
            "sop_activities_deleted": sop_result.deleted_count,
            "us_position_data_deleted": us_position_result.deleted_count,
            "total_deleted": total_deleted
        }
        
    except Exception as e:
        logger.error(f"Manual all SOP reset error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset all SOP data"
        )

@admin_router.delete("/sop/activities/{activity_id}")
async def delete_sop_activity(
    activity_id: str,
    current_user: dict = Depends(require_admin)
):
    """Delete specific SOP activity (admin only)"""
    try:
        sop_collection = get_sop_activity_collection()
        
        result = sop_collection.delete_one({"_id": ObjectId(activity_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SOP activity not found"
            )
        
        logger.info(f"SOP activity {activity_id} deleted by admin {current_user['username']}")
        return {"message": "SOP activity deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete SOP activity error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete SOP activity"
        )

@admin_router.get("/sop/activities", response_model=List[SOPActivityResponse])
async def get_all_sop_activities(
    sop_type: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    days: int = Query(30),
    current_user: dict = Depends(require_admin)
):
    """Get all SOP activities with filters (admin only)"""
    try:
        sop_collection = get_sop_activity_collection()
        
        query = {}
        
        if sop_type:
            query["sop_type"] = sop_type
            
        if user_id:
            query["user_id"] = ObjectId(user_id)
            
        if days > 0:
            cutoff_date = datetime.now() - timedelta(days=days)
            query["completed_at"] = {"$gte": cutoff_date}

        activities = list(sop_collection.find(query).sort("completed_at", -1))

        return [
            SOPActivityResponse(
                id=str(activity["_id"]),
                user_id=str(activity["user_id"]),
                username=activity["username"],
                sop_type=activity["sop_type"],
                task_id=activity["task_id"],
                task_description=activity["task_description"],
                completed_at=activity["completed_at"],
                ip_address=activity.get("ip_address"),
                user_agent=activity.get("user_agent")
            )
            for activity in activities
        ]

    except Exception as e:
        logger.error(f"Get SOP activities error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve SOP activities"
        )
 
@admin_router.post("/users/{user_id}/shift")
async def assign_user_shift(
    user_id: str,
    shift_data: dict,
    current_user: dict = Depends(require_admin)
):
    """Assign shift and exchange to user (admin only)"""
    try:
        user_collection = get_user_collection()
        
        user = user_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        update_data = {
            "shift": shift_data.get("shift"),
            "shift_assigned_by": current_user["username"],
            "shift_assigned_at": datetime.now()
        }

        user_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )
        
        logger.info(f"Shift assigned to user {user_id} by admin {current_user['username']}")
        return {"message": "Shift assigned successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Assign shift error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assign shift"
        )

@admin_router.get("/sop/report")
async def download_sop_report(
    sop_type: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    days: int = Query(30),
    format: str = Query("html"),
    current_user: dict = Depends(require_admin)
):
    """Download SOP report (admin only)"""
    try:
        sop_collection = get_sop_activity_collection()
        
        query = {}
        if sop_type:
            query["sop_type"] = sop_type
        if user_id:
            query["user_id"] = ObjectId(user_id)
        if days > 0:
            cutoff_date = datetime.now() - timedelta(days=days)
            query["completed_at"] = {"$gte": cutoff_date}

        activities = list(sop_collection.find(query).sort("completed_at", -1))

        if format == "csv":
            return _generate_csv_report(activities)
        else:
            return _generate_html_report(activities, sop_type, days)

    except Exception as e:
        logger.error(f"Download SOP report error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate report"
        )

@admin_router.get("/daily-report/check")
async def check_daily_report_availability(current_user: dict = Depends(require_admin)):
    """Check if daily report is available"""
    try:
        from services.daily_reset import daily_reset_service
        
        reset_completed = daily_reset_service.is_reset_completed_today()
        
        ist_tz = ZoneInfo("Asia/Kolkata")
        now_ist = datetime.now(ist_tz)
        
        today_3am = now_ist.replace(hour=3, minute=0, second=0, microsecond=0)
        is_after_3am = now_ist >= today_3am
        
        return {
            "available": reset_completed and is_after_3am,
            "reset_completed": reset_completed,
            "current_time": now_ist.isoformat(),
            "next_reset": today_3am.isoformat() if not is_after_3am else (today_3am + timedelta(days=1)).isoformat()
        }

    except Exception as e:
        logger.error(f"Check daily report availability error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check daily report availability"
        )

@admin_router.get("/daily-report/download")
async def download_daily_report(
    sop_type: Optional[str] = Query(None),
    current_user: dict = Depends(require_admin)
):
    """Download daily report"""
    try:
        from services.daily_reset import daily_reset_service
        
        report_data = await daily_reset_service.get_daily_report_data()
        
        if not report_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Daily report not available"
            )

        html_content = _generate_daily_html_report(report_data, sop_type)
        
        return StreamingResponse(
            io.StringIO(html_content),
            media_type="text/html",
            headers={"Content-Disposition": f"attachment; filename=daily_report_{datetime.now().strftime('%Y-%m-%d')}.html"}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download daily report error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download daily report"
        )
    
@admin_router.get("/us-position-activities", response_model=List[SOPActivityResponse])
async def get_us_position_activities_for_admin(
    days: int = Query(30),
    current_user: dict = Depends(require_admin)
):
    """Get US Position data formatted as SOP activities for admin view"""
    try:
        db = get_db()
        us_position_collection = db["us_position_data"]
        
        query = {}
        if days > 0:
            cutoff_date = datetime.now() - timedelta(days=days)
            query["last_updated_at"] = {"$gte": cutoff_date}
        
        us_data_docs = list(us_position_collection.find(query).sort("last_updated_at", -1))
        
        formatted_activities = []
        for doc in us_data_docs:
            for key, field_data in doc.get("form_data", {}).items():
                if key == "notes":
                    continue 
                
                task_id = f"us_snapshot_{field_data.get('time_slot', '').replace(' ', '_').replace(':', '')}_{field_data.get('section_type', '').replace(' ', '_')}_{field_data.get('field_type', '').replace(' ', '_')}".lower()
                task_description = f"{field_data.get('section_type')} {field_data.get('time_slot')} {field_data.get('field_type')}: {field_data.get('value')}"
                
                formatted_activities.append(SOPActivityResponse(
                    id=str(doc["_id"]) + "_" + key,
                    user_id=field_data.get("user_id", ""),
                    username=field_data.get("username", "N/A"),
                    sop_type="us_position_sop",
                    task_id=task_id,
                    task_description=task_description,
                    completed_at=datetime.fromisoformat(field_data["filled_at"]) if "filled_at" in field_data else datetime.utcnow(),
                    ip_address=None,
                    user_agent=None
                ))
        
        return formatted_activities
        
    except Exception as e:
        logger.error(f"Get US position activities for admin error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve US position activities"
        )

def _generate_csv_report(activities):
    """Generate CSV report"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        "Date", "Time", "Username", "SOP Type", "Task ID", "Task Description", "IP Address"
    ])
    
    for activity in activities:
        writer.writerow([
            activity["completed_at"].strftime("%Y-%m-%d"),
            activity["completed_at"].strftime("%H:%M:%S"),
            activity["username"],
            activity["sop_type"],
            activity["task_id"],
            activity["task_description"],
            activity.get("ip_address", "")
        ])
    
    output.seek(0)
    return StreamingResponse(
        io.StringIO(output.getvalue()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=sop_report.csv"}
    )

def _generate_html_report(activities, sop_type, days):
    """Generate HTML report"""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>SOP Report</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-50 p-8">
        <div class="max-w-6xl mx-auto">
            <h1 class="text-3xl font-bold text-blue-700 mb-6">SOP Activity Report</h1>
            <div class="bg-white rounded-lg shadow p-6 mb-6">
                <h2 class="text-xl font-semibold mb-4">Report Summary</h2>
                <div class="grid grid-cols-3 gap-4">
                    <div class="bg-blue-50 p-4 rounded">
                        <div class="text-2xl font-bold text-blue-600">{len(activities)}</div>
                        <div class="text-sm text-gray-600">Total Activities</div>
                    </div>
                    <div class="bg-green-50 p-4 rounded">
                        <div class="text-2xl font-bold text-green-600">{len(set(a['username'] for a in activities))}</div>
                        <div class="text-sm text-gray-600">Unique Users</div>
                    </div>
                    <div class="bg-purple-50 p-4 rounded">
                        <div class="text-2xl font-bold text-purple-600">{len(set(a['task_id'] for a in activities))}</div>
                        <div class="text-sm text-gray-600">Unique Tasks</div>
                    </div>
                </div>
            </div>
            <div class="bg-white rounded-lg shadow overflow-hidden">
                <table class="min-w-full">
                    <thead class="bg-gray-50">
                        <tr>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date/Time</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">User</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">SOP Type</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Task</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-200">
    """
    
    for activity in activities:
        html_content += f"""
                        <tr>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                {activity['completed_at'].strftime('%Y-%m-%d %H:%M:%S')}
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                {activity['username']}
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                {activity['sop_type']}
                            </td>
                            <td class="px-6 py-4 text-sm text-gray-900">
                                {activity['task_description']}
                            </td>
                        </tr>
        """
    
    html_content += """
                    </tbody>
                </table>
            </div>
        </div>
    </body>
    </html>
    """
    
    return StreamingResponse(
        io.StringIO(html_content),
        media_type="text/html",
        headers={"Content-Disposition": "attachment; filename=sop_report.html"}
    )

def _generate_daily_html_report(report_data, sop_type):
    """Generate daily HTML report"""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Daily SOP Report - {report_data['report_date']}</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-50 p-8">
        <div class="max-w-6xl mx-auto">
            <h1 class="text-3xl font-bold text-blue-700 mb-6">Daily SOP Report - {report_data['report_date']}</h1>
            <div class="bg-white rounded-lg shadow p-6 mb-6">
                <h2 class="text-xl font-semibold mb-4">Daily Summary</h2>
                <div class="grid grid-cols-4 gap-4">
                    <div class="bg-blue-50 p-4 rounded">
                        <div class="text-2xl font-bold text-blue-600">{report_data['activity_count']}</div>
                        <div class="text-sm text-gray-600">Total Activities</div>
                    </div>
                    <div class="bg-green-50 p-4 rounded">
                        <div class="text-2xl font-bold text-green-600">{report_data['unique_users']}</div>
                        <div class="text-sm text-gray-600">Active Users</div>
                    </div>
                    <div class="bg-purple-50 p-4 rounded">
                        <div class="text-2xl font-bold text-purple-600">{report_data['unique_tasks']}</div>
                        <div class="text-sm text-gray-600">Completed Tasks</div>
                    </div>
                    <div class="bg-yellow-50 p-4 rounded">
                        <div class="text-2xl font-bold text-yellow-600">{len(report_data['sop_breakdown'])}</div>
                        <div class="text-sm text-gray-600">SOP Types</div>
                    </div>
                </div>
            </div>
            <div class="bg-white rounded-lg shadow p-6">
                <h2 class="text-xl font-semibold mb-4">SOP Breakdown</h2>
                <div class="space-y-4">
    """
    
    for sop, data in report_data['sop_breakdown'].items():
        html_content += f"""
                    <div class="border rounded-lg p-4">
                        <h3 class="font-semibold text-lg">{sop.upper()}</h3>
                        <div class="grid grid-cols-3 gap-4 mt-2">
                            <div>Activities: <span class="font-bold">{data['count']}</span></div>
                            <div>Users: <span class="font-bold">{data['unique_users']}</span></div>
                            <div>Tasks: <span class="font-bold">{data['unique_tasks']}</span></div>
                        </div>
                    </div>
        """
    
    html_content += """
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_content
