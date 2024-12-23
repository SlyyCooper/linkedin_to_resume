#!/usr/bin/env python3
"""
LinkedIn Profile "Highlight & Copy" Extractor
--------------------------------------------
This script uses Selenium (Python) to:
1. Prompt for LinkedIn credentials (username/email & password).
2. Prompt for the LinkedIn profile URL.
3. Log in via LinkedIn's login page.
4. Navigate to the specified profile URL.
5. Locate & click "see more" buttons to expand hidden sections.
6. Programmatically "highlight everything" on the page (simulating Ctrl + A).
7. Extract all visible text from the entire page post-expansion.
8. Save it into an 'output/profile.marathon' file
   so that you have a direct, raw copy of the entire expanded profile.

DISCLAIMER:
- This script is a proof-of-concept and may violate LinkedIn's User Agreement
  if used in production. Use responsibly and lawfully.
- LinkedIn may change its HTML structure, so selectors may need to be updated.
"""

import os
import time
import getpass
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from openai import OpenAI
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from dotenv import load_dotenv
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE

load_dotenv()

class Experience(BaseModel):
    title: str
    company: str
    duration: str
    description: Optional[str] = None

class Education(BaseModel):
    school: str
    degree: str
    field: Optional[str] = None
    years: Optional[str] = None

class Certification(BaseModel):
    name: str
    issuer: str
    date: Optional[str] = None

class Volunteer(BaseModel):
    organization: str
    role: str
    duration: Optional[str] = None

class Recommendation(BaseModel):
    author: str
    relationship: str
    text: str

class LinkedInProfile(BaseModel):
    name: str
    headline: str
    location: str
    about: str
    experience: List[Experience]
    education: List[Education]
    skills: List[str]
    certifications: Optional[List[Certification]] = None
    languages: Optional[List[str]] = None
    volunteer: Optional[List[Volunteer]] = None
    recommendations: Optional[List[Recommendation]] = None

class ResumeStyle(BaseModel):
    """Defines the styling options for the DOCX resume"""
    font_name: str = "Calibri"
    name_size: int = 18
    heading_size: int = 14
    normal_size: int = 11
    heading_color: tuple = (0, 0, 0)  # RGB
    text_color: tuple = (0, 0, 0)     # RGB
    margins: float = 1.0              # inches
    line_spacing: float = 1.15

def structure_profile_data(raw_text: str) -> LinkedInProfile:
    """
    Uses GPT-4o to structure the raw LinkedIn profile text.
    """
    # Initialize client without any arguments - it will use the OPENAI_API_KEY from .env
    client = OpenAI()
    
    completion = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "Extract the LinkedIn profile information into a structured format."
            },
            {
                "role": "user",
                "content": raw_text
            }
        ],
        response_format=LinkedInProfile,
    )

    return completion.choices[0].message.parsed

def markdown_to_docx(markdown_file: str, output_file: str) -> str:
    """
    Converts the markdown resume to a simple DOCX file.
    """
    # Create new document
    doc = Document()
    
    # Read markdown content
    with open(markdown_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split content into lines
    lines = content.split('\n')
    
    # Process each line
    for line in lines:
        if line.startswith('# '):  # Name
            doc.add_heading(line[2:], 0)
        elif line.startswith('## '):  # Headline
            doc.add_heading(line[3:], 1)
        elif line.startswith('### '):  # Section headers
            doc.add_heading(line[4:], 2)
        elif line.startswith('#### '):  # Subsections
            doc.add_heading(line[5:], 3)
        elif line.startswith('- '):  # List items
            doc.add_paragraph(line[2:], style='List Bullet')
        elif line.startswith('*') and line.endswith('*'):  # Italic text
            p = doc.add_paragraph()
            p.add_run(line.strip('*')).italic = True
        elif line.startswith('**') and line.endswith('**'):  # Bold text
            p = doc.add_paragraph()
            p.add_run(line.strip('**')).bold = True
        elif '**' in line:  # Handle inline bold text (like "**Location:**")
            p = doc.add_paragraph()
            parts = line.split('**')
            for i, part in enumerate(parts):
                if part:  # Skip empty parts
                    run = p.add_run(part)
                    run.bold = (i % 2 == 1)  # Bold for odd-indexed parts
        elif line.strip():  # Normal text
            doc.add_paragraph(line)
    
    # Save the document
    doc.save(output_file)
    return output_file

def save_structured_profile(profile: LinkedInProfile, output_dir: str):
    """
    Saves the structured profile as a clean markdown file and a simple DOCX.
    """
    # Generate markdown content
    markdown = f"""# {profile.name}

## {profile.headline}
**Location:** {profile.location}

### About
{profile.about}

### Experience
"""
    
    for exp in profile.experience:
        markdown += f"""
#### {exp.title} at {exp.company}
*{exp.duration}*

{exp.description if exp.description else ''}
"""

    markdown += "\n### Education\n"
    for edu in profile.education:
        markdown += f"""
#### {edu.school}
{edu.degree}{f' in {edu.field}' if edu.field else ''}
{f'*{edu.years}*' if edu.years else ''}
"""

    if profile.skills:
        markdown += "\n### Skills\n"
        for skill in profile.skills:
            markdown += f"- {skill}\n"

    if profile.certifications:
        markdown += "\n### Certifications\n"
        for cert in profile.certifications:
            markdown += f"""
#### {cert.name}
Issued by {cert.issuer}{f' ({cert.date})' if cert.date else ''}
"""

    if profile.languages:
        markdown += "\n### Languages\n"
        for lang in profile.languages:
            markdown += f"- {lang}\n"

    if profile.recommendations:
        markdown += "\n### Recommendations\n"
        for rec in profile.recommendations:
            markdown += f"""
#### From {rec.author} ({rec.relationship})
{rec.text}
"""
    
    # Save markdown
    markdown_file = os.path.join(output_dir, "structured_profile.md")
    with open(markdown_file, "w", encoding="utf-8") as f:
        f.write(markdown)
    
    # Save DOCX
    docx_file = os.path.join(output_dir, "structured_profile.docx")
    markdown_to_docx(markdown_file, docx_file)
    
    return markdown_file, docx_file

def linkedin_highlight_and_extract(
    email: str,
    password: str,
    profile_url: str,
    output_dir="output"
):
    """
    Modified version of the original function that includes structured data extraction.
    """

    # ------------------------------
    # 1. Configure Selenium Options
    # ------------------------------
    chrome_options = Options()
    # (Optional) Uncomment to run headless if you don't need to see the browser:
    # chrome_options.add_argument('--headless')

    # Instantiate the WebDriver (adjust if using another browser)
    driver = webdriver.Chrome(options=chrome_options)

    try:
        # --------------------
        # 2. Log Into LinkedIn
        # --------------------
        driver.get("https://www.linkedin.com/login")

        # Wait for login form to appear
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "username"))
        )

        # Fill out username/email
        email_input = driver.find_element(By.ID, "username")
        email_input.clear()
        email_input.send_keys(email)

        # Fill out password
        password_input = driver.find_element(By.ID, "password")
        password_input.clear()
        password_input.send_keys(password)

        # Submit form
        driver.find_element(By.XPATH, '//button[@type="submit"]').click()

        # ------------------------------------------------
        # 3. Navigate to the user-specified profile URL
        # ------------------------------------------------
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Give some time for login to complete
        time.sleep(5)

        driver.get(profile_url)
        # Wait for the profile page to load
        time.sleep(5)  # Adjust as needed

        # -------------------------------------------------------
        # 4. Locate & Click "see more" Buttons to Expand Sections
        # -------------------------------------------------------
        # Typically, these "see more" buttons share certain classes or text.
        # We'll look for commonly used classes:
        see_more_selectors = [
            ".inline-show-more-text__button.inline-show-more-text__button--light.link"
        ]

        for selector in see_more_selectors:
            buttons = driver.find_elements(By.CSS_SELECTOR, selector)
            for btn in buttons:
                try:
                    driver.execute_script("arguments[0].click();", btn)
                    time.sleep(1)  # short pause for content to expand
                except Exception as e:
                    print(f"Warning: Could not click a 'see more' button: {e}")

        # -------------------------
        # 5. "Highlight Everything"
        # -------------------------
        # This simulates selecting the entire DOM (like Ctrl + A).
        # Note: This doesn't actually place text on your OS clipboard,
        # but it visually selects all on the page. For extraction in
        # Python, we will use .text or JavaScript to retrieve it below.
        driver.execute_script("window.getSelection().removeAllRanges();")
        driver.execute_script("const range = document.createRange(); range.selectNode(document.body); window.getSelection().addRange(range);")

        # -------------------------------
        # 6. Extract All Visible Text
        # -------------------------------
        # The simplest approach is to get everything from document.body.innerText
        page_text = driver.execute_script("return document.body.innerText")

        # ---------------------------------
        # 7. Save the text into .marathon
        # ---------------------------------
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        marathon_file = os.path.join(output_dir, "profile.marathon")

        with open(marathon_file, "w", encoding="utf-8") as f:
            f.write(page_text)

        print(f"Entire expanded profile text saved to: {marathon_file}")

        # After extracting the raw text:
        try:
            structured_profile = structure_profile_data(page_text)
            
            # Save both raw and structured versions
            raw_file = os.path.join(output_dir, "profile.marathon")
            with open(raw_file, "w", encoding="utf-8") as f:
                f.write(page_text)
            
            structured_file = save_structured_profile(structured_profile, output_dir)
            
            print(f"Raw profile text saved to: {raw_file}")
            print(f"Structured profile saved to: {structured_file}")
            
            return structured_profile
            
        finally:
            driver.quit()

    except Exception as e:
        print(f"Error: {e}")
        driver.quit()


def main():
    print("LinkedIn Highlight & Extract")
    print("-------------------------------------")
    email = input("LinkedIn Email/Username: ").strip()
    password = getpass.getpass("LinkedIn Password: ")
    profile_url = input("LinkedIn Profile URL (e.g., https://www.linkedin.com/in/username/): ").strip()

    profile = linkedin_highlight_and_extract(email, password, profile_url)
    
    if profile:
        print("\nProfile extracted successfully!")
        print("You can find your files in the output directory:")
        print("1. structured_profile.md - Markdown version")
        print("2. structured_profile.docx - Word document version")
        print("\nTo customize the DOCX styling, you can use the ResumeStyle class.")


if __name__ == "__main__":
    main()
