# backend/models.py
from pydantic import BaseModel, EmailStr, Field, field_validator 
from typing import Optional, Annotated, List
from bson import ObjectId
from datetime import datetime
from zoneinfo import ZoneInfo
import re

class SOPTypeInfo(BaseModel):
    id: str # ADD THIS LINE
    sop_type: str
    activity_count: int
    last_activity: Optional[datetime] = None
    display_name: str
    description: Optional[str] = None # Add description field

class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        from pydantic_core import core_schema
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema([
                core_schema.is_instance_schema(ObjectId),
                core_schema.chain_schema([
                    core_schema.str_schema(),
                    core_schema.no_info_plain_validator_function(cls.validate),
                ])
            ]),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x)
            ),
        )

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)


class SOPDefinition(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    sop_type: str = Field(..., min_length=1, max_length=50, description="Unique identifier for the SOP (e.g., 'gift_sop')")
    display_name: str = Field(..., min_length=1, max_length=100, description="User-friendly name for the SOP (e.g., 'GIFT SOP')")
    description: Optional[str] = Field(None, max_length=500, description="Detailed description of the SOP")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str, datetime: str}
    }

class SOPDefinitionCreate(BaseModel):
    sop_type: str = Field(..., min_length=1, max_length=50)
    display_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)

class SOPDefinitionUpdate(BaseModel):
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)

class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        from pydantic_core import core_schema
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema([
                core_schema.is_instance_schema(ObjectId),
                core_schema.chain_schema([
                    core_schema.str_schema(),
                    core_schema.no_info_plain_validator_function(cls.validate),
                ])
            ]),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x)
            ),
        )

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

class User(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    username: str = Field(..., min_length=3, max_length=50)
    name: Optional[str] = Field(None, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: str = Field(default="user")
    is_active: bool = Field(default=True)
    shift: Optional[str] = Field(None, description="User's assigned shift")
    allowed_sops: Optional[List[str]] = Field(default_factory=list, description="List of SOP types the user is allowed to access")

    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username can only contain letters, numbers, and underscores')
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str}
    }

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    name: Optional[str] = Field(None, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: str = Field(default="user")
    shift: Optional[str] = None
    allowed_sops: Optional[List[str]] = None


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6)
    role: Optional[str] = None
    is_active: Optional[bool] = None
    shift: Optional[str] = None
    allowed_sops: Optional[List[str]] = None


class UserResponse(BaseModel):
    id: str
    username: str
    name: Optional[str]
    email: str
    role: str
    is_active: bool
    shift: Optional[str] = None
    allowed_sops: Optional[List[str]] = None


class LoginUser(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class SOPActivity(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    username: str
    sop_type: str = Field(..., description="Type of SOP (e.g., 'gift_sop')")
    task_id: str = Field(..., description="Unique identifier for the task")
    task_description: str = Field(..., description="Description of the completed task")
    completed_at: datetime = Field(default_factory=lambda: datetime.now(ZoneInfo("Asia/Kolkata")))
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str, datetime: str}
    }

class SOPActivityCreate(BaseModel):
    sop_type: str
    task_id: str
    task_description: str

class SOPActivityResponse(BaseModel):
    id: str
    user_id: str
    username: str
    sop_type: str
    task_id: str
    task_description: str
    completed_at: datetime
    ip_address: Optional[str]
    user_agent: Optional[str]

class SOPProgress(BaseModel):
    sop_type: str
    completed_tasks: List[str]
    user_id: Optional[str] = None

class DailyReport(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    report_date: str
    generated_at: datetime
    activity_count: int
    unique_users: int
    unique_tasks: int
    sop_breakdown: dict
    shift_breakdown: Optional[dict] = None
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str, datetime: str}
    }

class MarkedDate(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: PyObjectId
    username: str
    marked_date: str = Field(..., description="Date in YYYY-MM-DD format")
    description: Optional[str] = Field(None, max_length=200, description="Optional description for the marked date")
    marked_at: datetime = Field(default_factory=lambda: datetime.now(ZoneInfo("Asia/Kolkata")))
    
    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str, datetime: str}
    }

class MarkedDateCreate(BaseModel):
    marked_date: str = Field(..., description="Date in YYYY-MM-DD format")
    description: Optional[str] = Field(None, max_length=200)

class MarkedDateResponse(BaseModel):
    id: str
    user_id: str
    username: str
    marked_date: str
    description: Optional[str]
    marked_at: datetime
