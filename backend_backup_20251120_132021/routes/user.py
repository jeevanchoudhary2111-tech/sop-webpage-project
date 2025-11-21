# Adding US Position data endpoints to the user router.
from fastapi import APIRouter, HTTPException, status, Depends, Form , Request
from datetime import timedelta , datetime
from models import (
    UserCreate, UserResponse, LoginUser, LoginResponse, Token,
    SOPActivityCreate, SOPActivityResponse,
    MarkedDateCreate, MarkedDateResponse , SOPDefinition
)
from database import get_user_collection, get_sop_activity_collection, get_marked_dates_collection , get_sop_definition_collection
from auth import (
    verify_password, 
    get_password_hash, 
    create_access_token,
    get_current_active_user
)
from config import settings
from bson import ObjectId
from typing import Optional, Annotated, List
import logging
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)
user_router = APIRouter()

@user_router.post("/register", response_model=dict)
async def register_user(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    name: str = Form(None)
):
    """Register a new user"""
    try:
        user_collection = get_user_collection()

        # Check if user already exists
        if user_collection.find_one({"$or": [{"email": email}, {"username": username}]}):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email or username already exists"
            )

        # Create new user
        user_data = {
            "username": username,
            "email": email,
            "name": name,
            "password": get_password_hash(password),
            "role": "user",
            "is_active": True
        }

        result = user_collection.insert_one(user_data)
        logger.info(f"User registered: {username}")

        return {"message": "User registered successfully", "user_id": str(result.inserted_id)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@user_router.post("/login", response_model=LoginResponse)
async def login(user_data: LoginUser):
    """Authenticate user and return JWT token"""
    try:
        logger.info(f"Login attempt for user: {user_data.username}")
        user_collection = get_user_collection()
        user = user_collection.find_one({"username": user_data.username})

        if not user or not verify_password(user_data.password, user["password"]):
            logger.warning(f"Failed login attempt for user: {user_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )

        if not user.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User account is disabled"
            )

        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user["username"]}, 
            expires_delta=access_token_expires
        )

        user_response = UserResponse(
            id=str(user["_id"]),
            username=user["username"],
            name=user.get("name"),
            email=user["email"],
            role=user.get("role", "user"),
            is_active=user.get("is_active", True),
            allowed_sops=user.get("allowed_sops", [])

        )

        logger.info(f"User logged in: {user['username']}")

        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user=user_response
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@user_router.get("/profile", response_model=UserResponse)
async def get_profile(current_user: dict = Depends(get_current_active_user)):
    """Get current user profile"""
    return UserResponse(
        id=str(current_user["_id"]),
        username=current_user["username"],
        name=current_user.get("name"),
        email=current_user["email"],
        role=current_user.get("role", "user"),
        is_active=current_user.get("is_active", True),
        allowed_sops=current_user.get("allowed_sops", [])

    )

@user_router.get("/sop-definitions", response_model=List[SOPDefinition])
async def get_user_sop_definitions(current_user: dict = Depends(get_current_active_user)):
    """Get SOP definitions accessible by the current user"""
    try:
        sop_definitions_collection = get_sop_definition_collection()
        
        if current_user.get("role") == "admin":
            # Admins can see all SOP definitions
            definitions = list(sop_definitions_collection.find({}).sort("_name", 1))
        else:
            # Regular users see only allowed SOPs
            allowed_sops = current_user.get("allowed_sops", [])
            definitions = list(sop_definitions_collection.find({"sop_type": {"$in": allowed_sops}}).sort("name", 1))
        
        return [SOPDefinition(**d) for d in definitions]
    except Exception as e:
        logger.error(f"Error getting user SOP definitions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve SOP definitions"
        )


@user_router.put("/profile", response_model=dict)
async def update_profile(
    name: str = Form(None),
    email: str = Form(None),
    current_user: dict = Depends(get_current_active_user)
):
    """Update current user profile"""
    try:
        user_collection = get_user_collection()
        update_data = {}

        if name is not None:
            update_data["name"] = name
        if email is not None:
            # Check if email is already taken by another user
            existing_user = user_collection.find_one({
                "email": email,
                "_id": {"$ne": current_user["_id"]}
            })
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already taken"
                )
            update_data["email"] = email

        if update_data:
            user_collection.update_one(
                {"_id": current_user["_id"]},
                {"$set": update_data}
            )
            logger.info(f"Profile updated: {current_user['username']}")

        return {"message": "Profile updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed")

@user_router.post("/sop/activity", response_model=dict)
async def log_sop_activity(
    activity_data: SOPActivityCreate,
    request: Request,
    current_user: dict = Depends(get_current_active_user)
):
    """Log SOP activity completion with task locking"""
    try:
        # Check for admin override header (for admin creating entries for other users)
        admin_user_id = request.headers.get("X-Admin-User-Id")
        if admin_user_id and current_user.get("role") == "admin":
            # Admin is creating entry for another user
            user_collection = get_user_collection()
            target_user = user_collection.find_one({"_id": ObjectId(admin_user_id)})
            if not target_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Target user not found"
                )
            # Use target user for the activity
            activity_user = target_user
        else:
            activity_user = current_user
        
        sop_collection = get_sop_activity_collection()

        # Check if this task was already completed by ANY user (task locking)
        existing_task = sop_collection.find_one({
            "sop_type": activity_data.sop_type,
            "task_id": activity_data.task_id
        })

        if existing_task and existing_task["user_id"] != activity_user["_id"]:
            # Task is locked by another user
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Task already completed by {existing_task['username']}"
            )

        # Check if this task was already completed by this user
        existing_activity = sop_collection.find_one({
            "user_id": activity_user["_id"],
            "sop_type": activity_data.sop_type,
            "task_id": activity_data.task_id
        })

        if existing_activity:
            # Update existing activity with new timestamp
            sop_collection.update_one(
                {"_id": existing_activity["_id"]},
                {
                    "$set": {
                        "completed_at": datetime.now(ZoneInfo("Asia/Kolkata")),
                        "ip_address": request.client.host,
                        "user_agent": request.headers.get("user-agent")
                    }
                }
            )
            logger.info(f"Updated SOP activity: {activity_data.task_id} for user: {activity_user['username']}")
        else:
            # Create new activity record
            activity_record = {
                "user_id": activity_user["_id"],
                "username": activity_user["username"],
                "sop_type": activity_data.sop_type,
                "task_id": activity_data.task_id,
                "task_description": activity_data.task_description,
                "completed_at": datetime.now(ZoneInfo("Asia/Kolkata")),
                "ip_address": request.client.host,
                "user_agent": request.headers.get("user-agent"),
                "session_id": request.headers.get("x-session-id")
            }

            result = sop_collection.insert_one(activity_record)
            logger.info(f"Logged SOP activity: {activity_data.task_id} for user: {activity_user['username']}")

        return {"message": "SOP activity logged successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SOP activity logging error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to log SOP activity"
        )

@user_router.post("/reset-password", response_model=dict)
async def reset_password(
    old_password: str = Form(...),
    new_password: str = Form(...),
    current_user: dict = Depends(get_current_active_user)
):
    """Reset user's own password with old password verification"""
    try:
        from auth import verify_password, get_password_hash
        
        # Verify old password
        if not verify_password(old_password, current_user["password"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Validate new password
        if len(new_password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be at least 6 characters long"
            )
        
        # Update password
        user_collection = get_user_collection()
        user_collection.update_one(
            {"_id": current_user["_id"]},
            {"$set": {"password": get_password_hash(new_password)}}
        )
        
        logger.info(f"Password reset by user: {current_user['username']}")
        return {"message": "Password reset successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password"
        )

@user_router.get("/sop/activities", response_model=List[SOPActivityResponse])
async def get_user_sop_activities(
    sop_type: str = None,
    current_user: dict = Depends(get_current_active_user)
):
    """Get current user's SOP activities"""
    try:
        sop_collection = get_sop_activity_collection()

        query = {"user_id": current_user["_id"]}
        if sop_type:
            query["sop_type"] = sop_type

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

@user_router.get("/sop/activities/today", response_model=List[SOPActivityResponse])
async def get_today_sop_activities(
    sop_type: str = None,
    current_user: dict = Depends(get_current_active_user)
):
    """Get today's SOP activities for all users"""
    try:
        sop_collection = get_sop_activity_collection()

        # Get today's date in IST
        ist_tz = ZoneInfo("Asia/Kolkata")
        now_ist = datetime.now(ist_tz)
        start_of_day = now_ist.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        # Convert to UTC for database query
        start_utc = start_of_day.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
        end_utc = end_of_day.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)

        query = {
            "completed_at": {
                "$gte": start_utc,
                "$lt": end_utc
            }
        }
        if sop_type:
            query["sop_type"] = sop_type

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
        logger.error(f"Get today SOP activities error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve today's SOP activities"
        )

@user_router.get("/sop/progress")
async def get_sop_progress(
    sop_type: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Get SOP progress and locked tasks"""
    try:
        sop_collection = get_sop_activity_collection()

        # Get all activities for this SOP type
        all_activities = list(sop_collection.find({"sop_type": sop_type}))

        # Get user's completed tasks
        user_activities = [a for a in all_activities if a["user_id"] == current_user["_id"]]
        user_completed = [a["task_id"] for a in user_activities]

        # Get locked tasks (completed by other users) - each task can only be completed once
        locked_tasks = []
        task_owners = {}

        for activity in all_activities:
            task_id = activity["task_id"]
            if task_id not in task_owners:
                task_owners[task_id] = activity["user_id"]

            # If task is owned by someone else, it's locked for current user
            if task_owners[task_id] != current_user["_id"]:
                locked_tasks.append(task_id)

        locked_tasks = list(set(locked_tasks))

        return {
            "user_completed": user_completed,
            "locked_tasks": locked_tasks,
            "total_activities": len(all_activities),
            "task_owners": {task_id: str(owner_id) for task_id, owner_id in task_owners.items()}
        }

    except Exception as e:
        logger.error(f"Get SOP progress error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve SOP progress"
        )

@user_router.post("/sop/progress")
async def save_sop_progress(
    sop_type: str = Form(...),
    completed_tasks: str = Form(...),  # JSON string of task IDs
    current_user: dict = Depends(get_current_active_user)
):
    """Save SOP progress"""
    try:
        import json
        task_ids = json.loads(completed_tasks)

        sop_collection = get_sop_activity_collection()

        # Save each completed task
        for task_id in task_ids:
            existing = sop_collection.find_one({
                "user_id": current_user["_id"],
                "sop_type": sop_type,
                "task_id": task_id
            })

            if not existing:
                activity_record = {
                    "user_id": current_user["_id"],
                    "username": current_user["username"],
                    "sop_type": sop_type,
                    "task_id": task_id,
                    "task_description": f"Task {task_id} completed",
                    "completed_at": datetime.now(ZoneInfo("Asia/Kolkata")),
                    "ip_address": "system",
                    "user_agent": "sop_progress_save"
                }
                sop_collection.insert_one(activity_record)

        return {"message": "Progress saved successfully"}

    except Exception as e:
        logger.error(f"Save SOP progress error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save SOP progress"
        )

@user_router.get("/sop/today-activities/{sop_type}")
async def get_today_sop_activities(
    sop_type: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Get today's SOP activities for a specific SOP type (to show completion info)"""
    try:
        sop_collection = get_sop_activity_collection()

        # Get today's date range in IST
        ist_tz = ZoneInfo("Asia/Kolkata")
        now_ist = datetime.now(ist_tz)

        # If it's before 3 AM IST, consider it as previous day
        if now_ist.hour < 3:
            today = now_ist.date() - timedelta(days=1)
        else:
            today = now_ist.date()

        start_of_day = datetime.combine(today, datetime.min.time())
        end_of_day = start_of_day + timedelta(days=1)

        activities = list(sop_collection.find({
            "sop_type": sop_type,
            "completed_at": {
                "$gte": start_of_day,
                "$lt": end_of_day
            }
        }).sort("completed_at", -1))

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
        logger.error(f"Get today SOP activities error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve today's SOP activities"
        )

@user_router.post("/sop/us-position-data")
async def save_us_position_data(
    data: dict,
    current_user: dict = Depends(get_current_active_user)
):
    """Save US Position form data"""
    try:
        from database import get_db
        db = get_db()
        us_position_collection = db["us_position_data"]

        # Get existing data to preserve other users' entries
        today = data.get("date", datetime.now().date().isoformat())
        existing_doc = us_position_collection.find_one({"date": today})
        
        if existing_doc:
            # Merge form data, preserving existing entries from other users
            merged_form_data = existing_doc.get("form_data", {})
            
            # Update only the fields that this user is submitting
            for field_key, field_data in data.get("form_data", {}).items():
                # Only update if the field actually has a value
                if field_data.get("value") and str(field_data.get("value")).strip():
                    # Check if this field already exists and was filled by another user
                    existing_field = merged_form_data.get(field_key)
                    if existing_field and existing_field.get("username") != current_user["username"]:
                        # Only update the value and timestamp, preserve original user info if value hasn't changed
                        if str(existing_field.get("value", "")).strip() != str(field_data.get("value")).strip():
                            # Value has changed, update with current user's info
                            merged_form_data[field_key] = {
                                "value": field_data.get("value"),
                                "timestamp": field_data.get("timestamp", datetime.now().isoformat()),
                                "time_slot": field_data.get("time_slot"),
                                "section_type": field_data.get("section_type"),
                                "field_type": field_data.get("field_type"),
                                "row_index": field_data.get("row_index"),
                                "cell_index": field_data.get("cell_index"),
                                "input_index": field_data.get("input_index"),
                                "user_id": str(current_user["_id"]),
                                "username": current_user["username"],
                                "filled_at": datetime.now().isoformat()
                            }
                        # If value hasn't changed, don't update at all to preserve original user info
                    else:
                        # New field or field owned by current user, update normally
                        merged_form_data[field_key] = {
                            "value": field_data.get("value"),
                            "timestamp": field_data.get("timestamp", datetime.now().isoformat()),
                            "time_slot": field_data.get("time_slot"),
                            "section_type": field_data.get("section_type"),
                            "field_type": field_data.get("field_type"),
                            "row_index": field_data.get("row_index"),
                            "cell_index": field_data.get("cell_index"),
                            "input_index": field_data.get("input_index"),
                            "user_id": str(current_user["_id"]),
                            "username": current_user["username"],
                            "filled_at": datetime.now().isoformat()
                        }
            
            # Update the document
            us_position_collection.update_one(
                {"date": today},
                {
                    "$set": {
                        "form_data": merged_form_data,
                        "last_updated_at": datetime.now(),
                        "last_updated_by": current_user["username"]
                    }
                }
            )
        else:
            # Create new document
            form_data_with_user = {}
            for field_key, field_data in data.get("form_data", {}).items():
                # Only include fields that actually have values
                if field_data.get("value") and str(field_data.get("value")).strip():
                    form_data_with_user[field_key] = {
                        **field_data,
                        "user_id": str(current_user["_id"]),
                        "username": current_user["username"],
                        "filled_at": datetime.now().isoformat()
                    }
            
            document = {
                "date": today,
                "form_data": form_data_with_user,
                "created_at": datetime.now(),
                "created_by": current_user["username"],
                "last_updated_at": datetime.now(),
                "last_updated_by": current_user["username"]
            }
            
            us_position_collection.insert_one(document)

        return {"message": "US Position data saved successfully"}

    except Exception as e:
        logger.error(f"Save US Position data error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save US Position data"
        )

@user_router.get("/sop/us-position-data")
async def get_us_position_data(current_user: dict = Depends(get_current_active_user)):
    """Get US Position form data for today"""
    try:
        from database import get_db
        db = get_db()
        us_position_collection = db["us_position_data"]

        # Get today's data - don't filter by user_id since we want to see all users' data
        today = datetime.now().date().isoformat()

        data = us_position_collection.find_one({"date": today})

        if data:
            return {
                "date": data["date"],
                "form_data": data.get("form_data", {}),
                "last_updated_at": data.get("last_updated_at"),
                "last_updated_by": data.get("last_updated_by")
            }
        else:
            return {"form_data": {}}

    except Exception as e:
        logger.error(f"Get US Position data error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve US Position data"
        )
    
@user_router.get("/users/by-shift")
async def get_users_by_shift(current_user: dict = Depends(get_current_active_user)):
    """Get all users grouped by shift"""
    try:
        user_collection = get_user_collection()
        users = list(user_collection.find({}))
        
        # Group users by shift
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

@user_router.post("/marked-dates", response_model=dict)
async def mark_date(
    date_data: MarkedDateCreate,
    current_user: dict = Depends(get_current_active_user)
):
    """Mark a date on the shared calendar"""
    try:
        marked_dates_collection = get_marked_dates_collection()
        
        # Check if user already marked this date
        existing_mark = marked_dates_collection.find_one({
            "user_id": current_user["_id"],
            "marked_date": date_data.marked_date
        })
        
        if existing_mark:
            # Update existing mark
            marked_dates_collection.update_one(
                {"_id": existing_mark["_id"]},
                {
                    "$set": {
                        "description": date_data.description,
                        "marked_at": datetime.now(ZoneInfo("Asia/Kolkata"))
                    }
                }
            )
            logger.info(f"Updated marked date {date_data.marked_date} for user {current_user['username']}")
            return {"message": "Date marking updated successfully"}
        else:
            # Create new mark
            marked_date_record = {
                "user_id": current_user["_id"],
                "username": current_user["username"],
                "marked_date": date_data.marked_date,
                "description": date_data.description,
                "marked_at": datetime.now(ZoneInfo("Asia/Kolkata"))
            }
            
            result = marked_dates_collection.insert_one(marked_date_record)
            logger.info(f"Marked date {date_data.marked_date} for user {current_user['username']}")
            return {"message": "Date marked successfully", "id": str(result.inserted_id)}
            
    except Exception as e:
        logger.error(f"Mark date error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark date"
        )

@user_router.get("/marked-dates", response_model=List[MarkedDateResponse])
async def get_marked_dates(current_user: dict = Depends(get_current_active_user)):
    """Get all marked dates from all users"""
    try:
        marked_dates_collection = get_marked_dates_collection()
        
        # Get all marked dates, sorted by date
        marked_dates = list(marked_dates_collection.find({}).sort("marked_date", 1))
        
        return [
            MarkedDateResponse(
                id=str(date["_id"]),
                user_id=str(date["user_id"]),
                username=date["username"],
                marked_date=date["marked_date"],
                description=date.get("description"),
                marked_at=date["marked_at"]
            )
            for date in marked_dates
        ]
        
    except Exception as e:
        logger.error(f"Get marked dates error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve marked dates"
        )

@user_router.delete("/marked-dates/{date}")
async def unmark_date(
    date: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Remove a marked date (only user's own marks)"""
    try:
        marked_dates_collection = get_marked_dates_collection()
        
        result = marked_dates_collection.delete_one({
            "user_id": current_user["_id"],
            "marked_date": date
        })
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Marked date not found or not owned by user"
            )
        
        logger.info(f"Unmarked date {date} for user {current_user['username']}")
        return {"message": "Date unmarked successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unmark date error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unmark date"
        )
