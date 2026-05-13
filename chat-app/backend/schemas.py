from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List


class UserBase(BaseModel):
    email: EmailStr
    display_name: str
    avatar_url: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None


class UserResponse(UserBase):
    id: str
    is_online: bool
    last_seen_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MessageBase(BaseModel):
    content: str
    message_type: str = "text"


class MessageCreate(MessageBase):
    conversation_id: str


class MessageResponse(MessageBase):
    id: str
    conversation_id: str
    sender_id: Optional[str]
    created_at: datetime
    sender: Optional[UserResponse] = None

    class Config:
        from_attributes = True


class ConversationBase(BaseModel):
    type: str = "direct"
    name: Optional[str] = None


class ConversationCreate(ConversationBase):
    participant_ids: List[str]


class ConversationResponse(ConversationBase):
    id: str
    created_at: datetime
    updated_at: datetime
    participants: List[UserResponse] = []
    last_message: Optional[MessageResponse] = None

    class Config:
        from_attributes = True


class GroupBase(BaseModel):
    name: str
    description: Optional[str] = None
    avatar_url: Optional[str] = None


class GroupCreate(GroupBase):
    member_ids: Optional[List[str]] = []


class GroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    avatar_url: Optional[str] = None


class GroupMemberResponse(BaseModel):
    id: str
    user_id: str
    role: str
    joined_at: datetime
    user: Optional[UserResponse] = None

    class Config:
        from_attributes = True


class GroupResponse(GroupBase):
    id: str
    owner_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    members: List[GroupMemberResponse] = []

    class Config:
        from_attributes = True


class PaginationMeta(BaseModel):
    total: int
    page: int
    page_size: int
    pages: int


class PaginatedResponse(BaseModel):
    items: List
    total: int
    page: int
    page_size: int
    pages: int


class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[dict] = None


class WebSocketMessage(BaseModel):
    type: str
    payload: dict


class AgentSessionCreate(BaseModel):
    conversation_id: Optional[str] = None
    title: Optional[str] = "New Agent Session"


class AgentMessageResponse(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    tool_calls: Optional[str] = None
    tool_results: Optional[str] = None
    metadata: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AgentSessionResponse(BaseModel):
    id: str
    user_id: str
    conversation_id: Optional[str] = None
    title: str
    status: str
    created_at: datetime
    updated_at: datetime
    messages: List[AgentMessageResponse] = []

    class Config:
        from_attributes = True


class AgentRunRequest(BaseModel):
    message: str


class AgentRunResponse(BaseModel):
    answer: str


class AgentSessionsListResponse(BaseModel):
    items: List[AgentSessionResponse]


class WorkspaceCreate(BaseModel):
    name: str
    description: Optional[str] = None


class WorkspaceMemberResponse(BaseModel):
    id: str
    workspace_id: str
    user_id: str
    role: str
    invited_by: Optional[str] = None
    created_at: datetime
    user: Optional[UserResponse] = None

    class Config:
        from_attributes = True


class WorkspaceResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    owner_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    members: List[WorkspaceMemberResponse] = []

    class Config:
        from_attributes = True


class WorkspaceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class WorkspaceInviteRequest(BaseModel):
    email: EmailStr
    role: str = "member"


class WorkspaceListResponse(BaseModel):
    items: List[WorkspaceResponse]


class FileRecordResponse(BaseModel):
    id: str
    filename: str
    stored_path: str
    file_size: int
    file_type: str
    uploader_id: str
    preview_data: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FileRecordListResponse(BaseModel):
    items: List[FileRecordResponse]
