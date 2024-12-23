from fastapi import APIRouter, WebSocket, HTTPException, status
from fastapi.responses import FileResponse
from app.models.chat import ChatRequest, ChatResponse, ChatMessage, ToolCall
from app.services.openai_service import (
    get_chat_completion,
    ChatError,
    ModelNotAvailableError,
    APIConnectionError,
    RateLimitExceededError
)
from app.services.linkedin_service import (
    linkedin_highlight_and_extract,
    LinkedInProfile,
    structure_profile_data,
    save_structured_profile
)
from app.core.config import get_settings
import json
import os
from typing import Dict, Any
import datetime

router = APIRouter()

def handle_chat_error(e: Exception) -> Dict[str, Any]:
    """Handle different types of chat errors and return appropriate status codes and messages"""
    if isinstance(e, ModelNotAvailableError):
        return {
            "status_code": status.HTTP_503_SERVICE_UNAVAILABLE,
            "detail": str(e)
        }
    elif isinstance(e, APIConnectionError):
        return {
            "status_code": status.HTTP_503_SERVICE_UNAVAILABLE,
            "detail": "Service temporarily unavailable. Please try again later."
        }
    elif isinstance(e, RateLimitExceededError):
        return {
            "status_code": status.HTTP_429_TOO_MANY_REQUESTS,
            "detail": "Rate limit exceeded. Please try again later."
        }
    elif isinstance(e, ChatError):
        return {
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "detail": str(e)
        }
    else:
        return {
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "detail": "An unexpected error occurred"
        }

async def execute_tool_call(tool_call: ToolCall) -> Dict[str, Any]:
    """Execute a tool call and return the result"""
    try:
        if tool_call.function["name"] == "linkedin_highlight_and_extract":
            args = json.loads(tool_call.function["arguments"])
            profile = linkedin_highlight_and_extract(
                email=args["email"],
                password=args["password"],
                profile_url=args["profile_url"]
            )
            # Convert Pydantic model to dict for JSON serialization
            return {
                "success": True,
                "data": profile.dict() if profile else None
            }
        return {
            "success": False,
            "error": f"Unknown tool: {tool_call.function['name']}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Handle chat requests with function calling support."""
    try:
        # Get initial response from OpenAI
        response = await get_chat_completion(request.messages)
        
        # If no tool calls, return the response directly
        if not response.message.tool_calls:
            return response
            
        # Initialize messages with the original messages and the assistant's response
        messages = list(request.messages)
        messages.append(response.message)  # Assistant message with tool_calls
        
        # Process each tool call
        for tool_call in response.message.tool_calls:
            # Execute the tool call
            result = await execute_tool_call(tool_call)
            if not result["success"]:
                raise ChatError(f"Tool call failed: {result['error']}")
            
            # Add the tool response message with proper formatting
            tool_response = ChatMessage(
                role="tool",
                content=json.dumps(result["data"]) if result["data"] else "",
                tool_call_id=tool_call.id,
                name=tool_call.function["name"]
            )
            messages.append(tool_response)
            
            print(f"Tool response added: {tool_response}")  # Debug logging
        
        # Get final response after all tool calls are processed
        print("Getting final response with messages:", json.dumps(messages, default=str))  # Debug logging
        final_response = await get_chat_completion(messages)
        
        if not final_response.message.content:
            # If no content in response, add a default message
            final_response.message.content = "I've processed your request. Is there anything specific you'd like to know about the extracted profile?"
            
        return final_response
        
    except Exception as e:
        print(f"Chat error: {str(e)}")
        error_info = handle_chat_error(e)
        raise HTTPException(
            status_code=error_info["status_code"],
            detail=error_info["detail"]
        )

@router.post("/test_completion")
async def test_completion():
    """Test endpoint to verify OpenAI chat completion is working."""
    try:
        # Create a simple test message
        test_messages = [
            ChatMessage(
                role="developer",
                content="You are a helpful assistant."
            ),
            ChatMessage(
                role="user",
                content="Say 'Hello, testing!' if you can hear me."
            )
        ]
        
        # Print debug info before making the request
        print("Testing OpenAI connection...")
        print(f"Using model: {get_settings().OPENAI_MODEL}")
        
        # Get completion without any tools to keep it simple
        response = await get_chat_completion(test_messages)
        
        return {
            "status": "success",
            "model": get_settings().OPENAI_MODEL,
            "response": response.message.content,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"Test completion error: {str(e)}")
        error_info = handle_chat_error(e)
        return {
            "status": "error",
            "error": error_info["detail"],
            "timestamp": datetime.datetime.now().isoformat()
        }

@router.get("/health")
async def health_check():
    """Simple health check endpoint."""
    try:
        settings = get_settings()
        api_key_configured = bool(settings.OPENAI_API_KEY)
        
        return {
            "status": "healthy",
            "api_key_configured": api_key_configured,
            "model": settings.OPENAI_MODEL,
            "timestamp": datetime.datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.datetime.now().isoformat()
        }

@router.get("/profile")
async def get_profile():
    """Get the latest generated profile content."""
    try:
        html_path = os.path.join("output", "structured_profile.html")
        print(f"Attempting to read profile from: {html_path}")
        
        if not os.path.exists(html_path):
            print(f"Profile file not found at: {html_path}")
            raise HTTPException(status_code=404, detail="No profile has been generated yet")
            
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        print(f"Successfully read profile content (length: {len(content)})")
        return {"content": content}
    except Exception as e:
        print(f"Error reading profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/profile/download")
async def download_profile():
    """Download the generated DOCX file."""
    docx_path = os.path.join("output", "structured_profile.docx")
    if not os.path.exists(docx_path):
        raise HTTPException(status_code=404, detail="No profile document has been generated yet")
        
    return FileResponse(
        docx_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename="profile.docx"
    ) 