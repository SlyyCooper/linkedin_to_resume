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

def linkedin_highlight_and_extract(
    email: str,
    password: str,
    profile_url: str,
    output_dir="output"
):
    """
    Logs into LinkedIn with the provided credentials,
    navigates to the user-provided profile URL,
    expands hidden sections by clicking "see more" buttons,
    highlights everything on the page, then extracts all the text
    and saves it to 'profile.marathon' in the specified output directory.
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

    finally:
        # Close the browser session
        driver.quit()


def main():
    print("LinkedIn Highlight & Extract")
    print("-------------------------------------")
    email = input("LinkedIn Email/Username: ").strip()
    password = getpass.getpass("LinkedIn Password: ")
    profile_url = input("LinkedIn Profile URL (e.g., https://www.linkedin.com/in/username/): ").strip()

    linkedin_highlight_and_extract(email, password, profile_url)


if __name__ == "__main__":
    main()
