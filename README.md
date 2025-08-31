
# HTML to PDF Converter

This script provides an efficient solution for converting a directory of local HTML files into multi-page PDFs. It is particularly useful for long web pages that need to be captured in their entirety.

The script uses a headless browser to ensure that all web content is fully rendered before being captured, providing a high-fidelity conversion of the source material.

## Features

-   **High-Fidelity Rendering**: Utilizes a headless Chromium browser via Playwright to accurately render HTML files, including content loaded with JavaScript.
-   **Handles Extremely Long Pages**: Captures a single, full-page screenshot and intelligently splits it across multiple PDF pages, bypassing image dimension limits found in standard libraries.
-   **Parallel Processing**: Converts multiple files concurrently using `asyncio` to significantly speed up the processing of large batches of files.
-   **Simple Command-Line Interface**: Easy to use—just point the script to a folder of HTML files and it will handle the rest.
-   **Error Handling**: Includes error handling to report issues with individual file conversions without stopping the entire batch.
-   **Skips Existing Files**: Automatically skips conversion if a PDF with the same name already exists in the directory, saving time on re-runs.

## How It Works

The script automates the following workflow for each HTML file in the target directory:

1.  **Launch Headless Browser**: A headless Chromium browser instance is launched using Playwright.
2.  **Load and Stabilize Page**: The script navigates to the local HTML file and waits for the page to become idle, ensuring all dynamic content has finished loading.
3.  **Capture Full Page**: It takes a single, high-resolution screenshot of the entire rendered page.
4.  **Split and Generate PDF**: The captured image is processed in memory using the Pillow library. It is vertically sliced into chunks that respect a maximum height limit. Each chunk is then saved as a separate page within a single, final PDF file using `pypdf`.
5.  **Save Output**: The resulting PDF is saved in the same directory as the source HTML file.

## Requirements

-   Python 3.7+
-   Required Python libraries (listed below).

### Python Dependencies
-   `playwright`
-   `Pillow`
-   `pypdf`

## Installation & Setup

1.  **Save the script:**
    Save the code as a Python file (e.g., `convertor.py`).

2.  **Install Python Dependencies:**
    Install all required libraries using pip:
    ```bash
    pip install playwright Pillow pypdf
    ```

3.  **Install Playwright Browser Binaries:**
    The first time you use Playwright, you must install the necessary browser drivers. This script is configured to use Chromium.
    ```bash
    playwright install chromium
    ```

## Usage

Run the script from your terminal, providing the path to the directory that contains your HTML files as an argument.

**Syntax:**
```bash
python convertor.py "/path/to/your/html_files"
```

**Example:**
```bash
python convertor.py "C:\Users\YourUser\Desktop\MyReports"
```

The script will generate a `.pdf` file for each `.html` file it finds, saving it in the same directory.

## Configuration

You can adjust the script's performance and behavior by modifying the configuration variables at the top of the file:

-   `PARALLEL_JOBS`: The number of HTML files to process concurrently. Increasing this on a machine with sufficient CPU cores and memory can improve performance.
-   `MAX_IMAGE_HEIGHT`: The maximum vertical pixel height for a single PDF page before the script creates a new page. This is used to prevent issues with the Pillow library's image processing limits.
