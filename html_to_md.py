#!/usr/bin/env python3
"""
THE ULTIMATE HTML-TO-MARKDOWN CLI
--------------------------------
An extremely sophisticated, interactive Python script to convert
HTML from a user-supplied URL into Markdown, with advanced features.
"""

import os
import sys
import re
from datetime import datetime
from urllib.parse import urlparse

# --- External libraries ---
# Make sure to install these (if not already installed) by running:
#   pip install questionary requests html2text rich

import requests
import questionary
import html2text
from rich.console import Console
from rich.panel import Panel
from rich import print
from rich.progress import Progress
from rich.spinner import Spinner

# Create a global Rich console for pretty output
console = Console()

def print_banner():
    """
    Prints a fancy banner using Rich.
    """
    banner_text = r"""
 __  __ _____  _      _          __  __          _____
|  \/  |_   _|| |    | |   /\   |  \/  |   /\   |  __ \
| \  / | | |  | |    | |  /  \  | \  / |  /  \  | |__) |
| |\/| | | |  | |    | | / /\ \ | |\/| | / /\ \ |  ___/
| |  | |_| |_ | |____| |/ ____ \| |  | |/ ____ \| |
|_|  |_|_____|______|_/_/    \_\_|  |_/_/    \_\_|
    """
    console.print(banner_text, style="bold green")
    console.print(Panel.fit("The Ultimate HTML-to-Markdown CLI", style="bold magenta"))

def create_output_directory(output_dir="output"):
    """
    Creates the specified output directory if it doesn't exist.
    Returns the absolute path of the directory.
    """
    dir_path = os.path.join(os.getcwd(), output_dir)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    return dir_path

def is_valid_url(url):
    """
    Quick check to see if the user-supplied string looks like a valid URL.
    """
    parsed = urlparse(url)
    return bool(parsed.scheme) and bool(parsed.netloc)

def fetch_html(url):
    """
    Fetches HTML content from the specified URL.
    Raises an exception if it fails or if the URL is invalid.
    """
    if not is_valid_url(url):
        raise ValueError(f"Invalid URL: {url}")
    try:
        with Progress() as progress:
            task = progress.add_task("[green]Fetching HTML...", total=None)
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            progress.update(task, completed=100)
        return response.text
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Error fetching the URL: {e}")

def convert_html_to_markdown(html_content, keep_links=True, keep_images=True, keep_emphasis=True):
    """
    Converts HTML content into Markdown using html2text with user preferences.
    """
    converter = html2text.HTML2Text()
    converter.ignore_links = not keep_links
    converter.ignore_images = not keep_images
    converter.ignore_emphasis = not keep_emphasis
    # Feel free to tweak other converter settings as needed
    markdown_text = converter.handle(html_content)
    return markdown_text.strip()

def generate_filename_from_url(url):
    """
    Generates a filename based on the domain and current timestamp.
    Example: example.com-20241223-104512.md
    """
    parsed = urlparse(url)
    domain = parsed.netloc if parsed.netloc else "domain"
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"{domain}-{timestamp}.md"
    return filename

def prompt_advanced_settings():
    """
    Prompts user for advanced conversion settings and returns a dict.
    """
    keep_images = questionary.confirm(
        "Keep images in the Markdown output?",
        default=True
    ).ask()

    keep_links = questionary.confirm(
        "Keep links in the Markdown output?",
        default=True
    ).ask()

    keep_emphasis = questionary.confirm(
        "Preserve text emphasis (bold/italic)?",
        default=True
    ).ask()

    generate_toc = questionary.confirm(
        "Generate a table of contents from headings?",
        default=False
    ).ask()

    save_raw_html = questionary.confirm(
        "Also save a copy of the raw HTML?",
        default=False
    ).ask()

    custom_filename = questionary.confirm(
        "Do you want to specify your own output filename (instead of automatic naming)?",
        default=False
    ).ask()

    output_filename = None
    if custom_filename:
        output_filename = questionary.text(
            "Enter the desired output filename (e.g., my_file.md):"
        ).ask()

    overwrite_existing = questionary.select(
        "If a file with the same name exists, what should we do?",
        choices=[
            "Overwrite it",
            "Append a unique suffix"
        ],
        default="Append a unique suffix"
    ).ask()

    return {
        "keep_images": keep_images,
        "keep_links": keep_links,
        "keep_emphasis": keep_emphasis,
        "generate_toc": generate_toc,
        "save_raw_html": save_raw_html,
        "custom_filename": custom_filename,
        "output_filename": output_filename,
        "overwrite_existing": overwrite_existing
    }

def generate_table_of_contents(markdown_text):
    """
    Generate a table of contents for the given Markdown text by detecting headings.
    Returns the new Markdown with a TOC inserted after the first line.
    """
    # Find all headings of form: `#`, `##`, `###`, etc.
    # We create anchor links in standard GitHub Markdown format: [Title](#title)
    headings = re.findall(r'^(#+)\s+(.*)', markdown_text, flags=re.MULTILINE)

    if not headings:
        return markdown_text  # No headings to build a TOC

    toc_lines = []
    toc_lines.append("## Table of Contents\n")
    for heading in headings:
        level = len(heading[0])  # Number of '#' characters
        title = heading[1].strip()

        # Create a slug for the link (same style GitHub uses: lowercase, spaces->-, remove punctuation)
        anchor = re.sub(r'[^\w\s-]', '', title.lower()).replace(' ', '-')
        indent = "  " * (level - 1)
        toc_lines.append(f"{indent}- [{title}](#{anchor})")

    toc_string = "\n".join(toc_lines) + "\n\n"
    # Insert TOC near the top. Here we place it after the first line (if the first line is a title).
    # If you want it absolutely at the top, you can just do: return toc_string + markdown_text
    return toc_string + markdown_text

def handle_file_write(markdown_text, output_dir, settings, url):
    """
    Handles writing the markdown (and optional HTML) to the filesystem.
    Respects user overwriting preferences and custom filenames.
    """
    if settings["custom_filename"] and settings["output_filename"]:
        base_filename = settings["output_filename"]
    else:
        base_filename = generate_filename_from_url(url)

    # If the user wants to append a suffix instead of overwriting
    # and the file already exists, we find a unique name.
    output_path = os.path.join(output_dir, base_filename)

    if settings["overwrite_existing"] == "Append a unique suffix":
        # Keep adding a numeric suffix until we find a non-existing file
        file_root, file_ext = os.path.splitext(output_path)
        counter = 1
        while os.path.exists(output_path):
            output_path = f"{file_root}_{counter}{file_ext}"
            counter += 1
    else:
        # Overwrite existing
        pass

    # Write Markdown
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown_text)

    console.print(f"[bold green]Markdown saved to:[/bold green] {output_path}", style="bold green")

    # Optionally save raw HTML
    if settings["save_raw_html"]:
        html_filename = os.path.splitext(output_path)[0] + ".html"
        console.print(f"Saving raw HTML as: {html_filename}")
        return html_filename, output_path
    else:
        return None, output_path

def run_cli():
    """
    Main interactive loop. Asks for URL, advanced settings, performs
    conversion, and optionally repeats.
    """
    while True:
        # Prompt user for the URL
        url = questionary.text("Enter the URL to convert to Markdown (or press Enter to quit):").ask()

        # If user hits Enter without input, exit
        if not url:
            console.print("[yellow]No URL provided. Exiting...[/yellow]")
            sys.exit(0)

        # Prompt advanced settings
        console.print("\n[bold magenta]--- ADVANCED SETTINGS ---[/bold magenta]\n", style="bold magenta")
        settings = prompt_advanced_settings()

        # Create output directory
        output_directory = create_output_directory()

        # Fetch HTML with a spinner
        spinner = Spinner("dots", text="Fetching and converting...")
        with console.status(spinner):
            try:
                html_content = fetch_html(url)
            except (ValueError, RuntimeError) as e:
                console.print(f"[red]{e}[/red]")
                continue

            # Convert HTML to Markdown
            markdown_content = convert_html_to_markdown(
                html_content,
                keep_links=settings["keep_links"],
                keep_images=settings["keep_images"],
                keep_emphasis=settings["keep_emphasis"]
            )

            # Optionally generate a table of contents
            if settings["generate_toc"]:
                markdown_content = generate_table_of_contents(markdown_content)

        # Save to file
        html_filename, md_filename = handle_file_write(markdown_content, output_directory, settings, url)

        # If the user opted to save raw HTML, do so
        if settings["save_raw_html"] and html_filename:
            with open(html_filename, "w", encoding="utf-8") as f:
                f.write(html_content)

        # Ask if user wants to convert another
        more = questionary.select(
            "Do you want to process another URL?",
            choices=["Yes, let's do another", "No, exit the script"]
        ).ask()

        if more == "No, exit the script":
            console.print("[bold cyan]Goodbye![/bold cyan]")
            break

def main():
    print_banner()
    run_cli()

if __name__ == "__main__":
    main()
