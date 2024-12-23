from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Literal

class ToolCall(BaseModel):
    """Model for function/tool calls."""
    id: str
    type: str = "function"
    function: Dict[str, Any]

class ChatMessage(BaseModel):
    """Individual chat message model with support for developer role and tool calls."""
    role: Literal["user", "assistant", "developer", "system", "tool"]
    content: str
    tool_calls: Optional[List[ToolCall]] = None
    tool_call_id: Optional[str] = None  # For tool response messages
    name: Optional[str] = None  # For tool response messages, contains the function name

class ChatRequest(BaseModel):
    """Chat request model with support for message history and tool outputs."""
    messages: List[ChatMessage]  # Contains the full conversation history
    tool_outputs: Optional[List[Dict[str, Any]]] = None

class ChatResponse(BaseModel):
    """Chat response model with enhanced features."""
    message: ChatMessage
    profile_data: Optional[Dict[str, Any]] = None
    requires_tool: bool = False 