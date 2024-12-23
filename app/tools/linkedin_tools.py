"""LinkedIn function tools for the chatbot."""

LINKEDIN_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "linkedin_highlight_and_extract",
            "description": "Extract and convert a LinkedIn profile to markdown and docx formats. Call this when the user wants to extract their LinkedIn profile.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {
                        "type": "string",
                        "description": "LinkedIn login email/username"
                    },
                    "password": {
                        "type": "string",
                        "description": "LinkedIn password (will be handled securely)"
                    },
                    "profile_url": {
                        "type": "string",
                        "description": "Full URL of the LinkedIn profile to extract (e.g., https://www.linkedin.com/in/username)"
                    }
                },
                "required": ["email", "password", "profile_url"],
                "additionalProperties": False
            },
            "strict": True  # Enable structured outputs for function arguments
        }
    }
] 