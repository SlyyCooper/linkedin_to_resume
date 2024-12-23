from typing import Dict, Any
import re
import html
from bs4 import BeautifulSoup

class ResponseFormatter:
    """Formats chat responses from markdown to clean HTML."""
    
    @staticmethod
    def format_response(content: str) -> str:
        """
        Convert markdown-formatted text to clean, styled HTML.
        """
        try:
            # First, escape any HTML to prevent XSS
            content = html.escape(content)
            
            # Format sections (###)
            content = re.sub(r'###\s*(.*?)\s*(?=###|$)', r'<h3 class="section-title">\1</h3>', content)
            
            # Format subsections (**)
            content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
            
            # Format lists
            content = re.sub(r'^\s*-\s*(.*?)$', r'<li>\1</li>', content, flags=re.MULTILINE)
            content = re.sub(r'(<li>.*?</li>\s*)+', r'<ul class="info-list">\g<0></ul>', content)
            
            # Format line breaks
            content = content.replace('\n', '<br>')
            
            # Wrap the content in a styled div
            formatted_content = f"""
            <div class="chat-response">
                {content}
            </div>
            <style>
                .chat-response {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    line-height: 1.5;
                    color: #2c3e50;
                }}
                .chat-response .section-title {{
                    font-size: 1.1em;
                    font-weight: 600;
                    color: #1a1a1a;
                    margin: 1em 0 0.5em;
                }}
                .chat-response strong {{
                    color: #1a1a1a;
                    font-weight: 600;
                }}
                .chat-response .info-list {{
                    margin: 0.5em 0;
                    padding-left: 1.5em;
                }}
                .chat-response .info-list li {{
                    margin-bottom: 0.3em;
                }}
                .chat-response br {{
                    margin-bottom: 0.5em;
                }}
            </style>
            """
            
            # Clean up any double line breaks or spaces
            soup = BeautifulSoup(formatted_content, 'html.parser')
            formatted_content = str(soup.prettify())
            
            return formatted_content
            
        except Exception as e:
            print(f"Error formatting response: {str(e)}")
            return content  # Return original content if formatting fails
    
    @staticmethod
    def format_profile_summary(profile_data: Dict[str, Any]) -> str:
        """
        Format a profile summary into a clean, structured response.
        """
        try:
            sections = []
            
            # Basic Information
            if any(key in profile_data for key in ['name', 'headline', 'location']):
                basic_info = []
                if 'name' in profile_data:
                    basic_info.append(f"**Name:** {profile_data['name']}")
                if 'headline' in profile_data:
                    basic_info.append(f"**Headline:** {profile_data['headline']}")
                if 'location' in profile_data:
                    basic_info.append(f"**Location:** {profile_data['location']}")
                sections.append("### Basic Information\n" + "\n".join(basic_info))
            
            # About
            if 'about' in profile_data and profile_data['about']:
                sections.append(f"### About\n{profile_data['about']}")
            
            # Experience
            if 'experience' in profile_data and profile_data['experience']:
                exp_items = []
                for exp in profile_data['experience']:
                    exp_items.append(f"- **{exp['title']}** at {exp['company']}")
                    if 'duration' in exp:
                        exp_items.append(f"  {exp['duration']}")
                sections.append("### Experience\n" + "\n".join(exp_items))
            
            # Education
            if 'education' in profile_data and profile_data['education']:
                edu_items = []
                for edu in profile_data['education']:
                    edu_items.append(f"- **{edu['degree']}** from {edu['school']}")
                    if 'years' in edu:
                        edu_items.append(f"  {edu['years']}")
                sections.append("### Education\n" + "\n".join(edu_items))
            
            # Skills
            if 'skills' in profile_data and profile_data['skills']:
                sections.append("### Skills\n" + "\n".join(f"- {skill}" for skill in profile_data['skills']))
            
            # Format the entire response
            formatted_text = "\n\n".join(sections)
            return ResponseFormatter.format_response(formatted_text)
            
        except Exception as e:
            print(f"Error formatting profile summary: {str(e)}")
            return str(profile_data)  # Return raw data if formatting fails 