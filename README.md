# 🦊 html_to_markdown 🦊

This is an HTML to Markdown converter.

This CLI tool, `html_to_md.py`, is a straightforward solution for turning web pages into clean Markdown. It's interactive and has some useful features.

## Features

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

## How to Use

1.  **Install:** Get the required libraries:
    ```bash
    pip install questionary requests html2text rich
    ```
2.  **Run:**
    ```bash
    python html_to_md.py
    ```
3.  **Follow Prompts:** The script will ask for a URL and settings.

## Example

```
Enter the URL to convert to Markdown (or press Enter to quit): https://example.com
```

The script will fetch the HTML, convert it, and save it in the `output` directory.

## Contributing

Feel free to fork and submit pull requests.

## License

This project is under the MIT License.

Enjoy! 🦊
