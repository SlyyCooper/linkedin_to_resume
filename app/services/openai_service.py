from openai import OpenAI, OpenAIError, APIError, APIConnectionError, RateLimitError
from typing import List, Dict, Any
from app.models.chat import ChatMessage, ChatResponse, ToolCall
from app.core.config import get_settings
from app.tools.linkedin_tools import LINKEDIN_TOOLS
import json

settings = get_settings()
client = OpenAI(api_key=settings.OPENAI_API_KEY)

class ChatError(Exception):
    """Base class for chat-related errors"""
    pass

class ModelNotAvailableError(ChatError):
    """Raised when the specified model is not available"""
    pass

class APIConnectionError(ChatError):
    """Raised when there's an issue connecting to the API"""
    pass

class RateLimitExceededError(ChatError):
    """Raised when rate limit is exceeded"""
    pass

async def get_chat_completion(messages: List[ChatMessage]) -> ChatResponse:
    """
    Get a chat completion from OpenAI using the latest model and methods.
    Uses the new developer role and function calling features from December 2024.
    """
    try:
        # Convert messages to OpenAI format
        openai_messages = []
        
        # Add developer message first (new role type as of December 2024)
        openai_messages.append({
            "role": "developer",
            "content": """You are a helpful LinkedIn Profile Assistant that helps users extract and convert their LinkedIn profiles.

Your main capabilities:
1. Guide users through providing their LinkedIn credentials safely
2. Help them understand the extraction process
3. Extract and convert profiles to markdown/docx formats
4. Answer questions about the process

When users want to extract a profile, collect these details in order:
1. LinkedIn email/username
2. Password (remind them it's handled securely)
3. Profile URL (must be a valid LinkedIn profile URL)

Important security notes:
- Always handle credentials securely
- Verify the profile URL format
- Inform users about the extraction process
- Let them know their data is handled privately"""
        })
        
        # Add the rest of the messages
        for msg in messages:
            message_dict = {"role": msg.role, "content": msg.content}
            if msg.tool_call_id:  # For tool response messages
                message_dict["tool_call_id"] = msg.tool_call_id
            openai_messages.append(message_dict)
        
        try:
            # Call OpenAI with the latest model and features
            response = client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=openai_messages,
                tools=LINKEDIN_TOOLS,
                tool_choice="auto"  # Let the model decide when to use tools
            )
            
            # Extract the assistant's message
            assistant_message = response.choices[0].message
            
            # Convert tool calls to our ToolCall model if present
            tool_calls = None
            if hasattr(assistant_message, 'tool_calls') and assistant_message.tool_calls:
                tool_calls = [
                    ToolCall(
                        id=tool.id,
                        type=tool.type,
                        function={
                            "name": tool.function.name,
                            "arguments": tool.function.arguments
                        }
                    )
                    for tool in assistant_message.tool_calls
                ]
            
            # Create and return ChatResponse
            return ChatResponse(
                message=ChatMessage(
                    role="assistant",
                    content=assistant_message.content if assistant_message.content else "",
                    tool_calls=tool_calls
                )
            )
            
        except APIError as e:
            if "model not found" in str(e).lower():
                raise ModelNotAvailableError(f"Model {settings.OPENAI_MODEL} is not available. Error: {e}")
            raise ChatError(f"OpenAI API error: {e}")
            
        except APIConnectionError as e:
            raise APIConnectionError(f"Failed to connect to OpenAI API: {e}")
            
        except RateLimitError as e:
            raise RateLimitExceededError(f"Rate limit exceeded: {e}")
            
        except Exception as e:
            raise ChatError(f"Unexpected error during chat completion: {e}")
        
    except Exception as e:
        # Log the error in production
        raise ChatError(f"Chat service error: {str(e)}") 