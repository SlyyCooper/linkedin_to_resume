from fastapi import APIRouter, WebSocket, HTTPException, status
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
import json
from typing import Dict, Any

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
            
        # Create new messages array with original messages and assistant's response
        messages = list(request.messages)
        messages.append(response.message)
        
        # Execute all tool calls and collect their results
        tool_results = []
        for tool_call in response.message.tool_calls:
            result = await execute_tool_call(tool_call)
            if not result["success"]:
                raise ChatError(f"Tool call failed: {result['error']}")
            
            # Add each tool result with its corresponding tool_call_id
            tool_results.append({
                "tool_call_id": tool_call.id,
                "data": result["data"]
            })
        
        # Add all tool results as tool messages
        for result in tool_results:
            messages.append(
                ChatMessage(
                    role="tool",
                    content=json.dumps(result["data"]),
                    tool_call_id=result["tool_call_id"]
                )
            )
        
        # Get final response with all tool results
        final_response = await get_chat_completion(messages)
        return final_response
        
    except Exception as e:
        error_info = handle_chat_error(e)
        raise HTTPException(
            status_code=error_info["status_code"],
            detail=error_info["detail"]
        )

@router.post("/test")
async def test_chat():
    """Test endpoint to verify the chatbot is working."""
    try:
        test_message = ChatMessage(
            role="user",
            content="Hi, can you help me with my LinkedIn profile?"
        )
        response = await get_chat_completion([test_message])
        return {"status": "success", "response": response.message.content}
    except Exception as e:
        error_info = handle_chat_error(e)
        raise HTTPException(
            status_code=error_info["status_code"],
            detail=error_info["detail"]
        ) 