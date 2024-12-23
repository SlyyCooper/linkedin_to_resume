# 🦊 html_to_markdown & linkedin_to_markdown 🦊

This repository contains tools for converting HTML and LinkedIn profiles to Markdown format.

## HTML to Markdown Converter

The `html_to_md.py` CLI tool converts web pages into clean Markdown. It's interactive and has useful features.

### Features

-   **CLI Interface:** Uses a command-line interface with `questionary`.
-   **URL Input:** Converts web pages from a given URL.
-   **Conversion Settings:** Options to:
    -   Keep or remove images.
    -   Keep or remove links.
    -   Keep or ignore text emphasis (bold/italic).
    -   Generate a table of contents.
    -   Save raw HTML.
    -   Use a custom output filename.
    -   Handle existing files (overwrite or append).
-   **Progress Display:** Shows conversion progress with a bar and spinner.
-   **Console Output:** Uses `rich` for console display.
-   **Error Handling:** Handles URL and network errors.
-   **Filename Generation:** Files are named automatically or can be custom named.

### How to Use HTML to MD

1.  **Install:** Get the required libraries:
    ```bash
    pip install questionary requests html2text rich
    ```
2.  **Run:**
    ```bash
    python html_to_md.py
    ```
3.  **Follow Prompts:** The script will ask for a URL and settings.

## LinkedIn to Markdown Converter

The `linkedin_to_markdown.py` script extracts LinkedIn profiles and converts them to Markdown format.

### Features

- **Automated Login:** Securely logs into LinkedIn with provided credentials
- **Profile Extraction:** Navigates to specified profile URL and extracts content
- **Content Expansion:** Automatically expands "see more" sections
- **Raw Text Export:** Saves extracted profile text to .marathon file
- **Selenium-based:** Uses Selenium WebDriver for reliable automation

### How to Use LinkedIn to MD

1. **Install:** Get the required libraries:
    ```bash
    pip install selenium
    ```
2. **Run:**
    ```bash
    python linkedin_to_markdown.py
    ```
3. **Follow Prompts:** Enter LinkedIn credentials and profile URL

## Example
