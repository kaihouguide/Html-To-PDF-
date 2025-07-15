
# HTML to Long-Strip PDF Converter

This script, `Convertor.py`, provides a powerful and automated solution for converting a directory of local HTML files, especially complex and interactive ones (like those containing Plotly.js or D3.js visualizations), into high-quality, multi-page "long-strip" PDFs.

Unlike standard "Print to PDF" functions that can struggle with dynamic content, this tool uses a headless browser to take full-page, scrolling screenshots and stitch them together, ensuring a perfect, continuous capture of the entire page.

## Features

-   **High-Fidelity Capture**: Uses a headless browser (Playwright) to render HTML files exactly as they appear on the web, including complex JavaScript visualizations.
-   **Parallel Processing**: Converts multiple files concurrently using `asyncio` to significantly speed up the process for large batches.
-   **Offline Caching**: Automatically downloads and caches external JavaScript libraries (`Plotly`, `D3.js`, `MathJax`) for faster subsequent runs and offline use.
-   **High-Quality Output**: Creates high-resolution screenshots by using a device scale factor multiplier, resulting in crisp and clear PDFs.
-   **Smart Image Handling**: Intelligently stitches screenshots into long vertical strips and chunks them to stay within image processing memory limits, preventing errors with very long pages.
-   **Simple Command-Line Interface**: Just point the script to a folder of HTML files and let it run.

## How It Works

The script automates the following workflow for each HTML file:
1.  **Launch Headless Browser**: A headless Chromium browser is launched using Playwright.
2.  **Intercept Dependencies**: The script intercepts network requests for common JS libraries and serves them from a local cache to speed up rendering and enable offline processing.
3.  **Scroll and Capture**: It calculates the total height of the HTML page, then programmatically scrolls down, taking screenshots of each viewport section.
4.  **Stitch Images**: The individual screenshots are stitched together vertically using the Pillow library to create long image "strips". To handle extremely long pages, it creates multiple strips to avoid hitting image size limits.
5.  **Create PDF**: Each long image strip is saved as a page in a temporary PDF. These are then merged into a final, multi-page "long-strip" PDF using `pypdf`.
6.  **Cleanup**: All temporary screenshot and PDF files are deleted, leaving only the final PDF output in the source directory.

## Requirements

-   Python 3.7+
-   Required Python libraries (see installation below).

### Python Dependencies
-   `playwright`
-   `aiohttp`
-   `aiofiles`
-   `Pillow`
-   `pypdf`

## Installation & Setup

1.  **Clone the Repository (or download `Convertor.py`):**
    ```bash
    git clone https://github.com/your-username/your-repo-name.git
    cd your-repo-name
    ```

2.  **Install Python Dependencies:**
    Install all the required libraries directly using pip in a single command:
    ```bash
    pip install playwright aiohttp aiofiles Pillow pypdf
    ```

3.  **Install Playwright Browser Binaries:**
    The first time you use Playwright, you need to install the necessary browser drivers. The script uses Chromium.
    ```bash
    playwright install chromium
    ```

## Usage

Run the script from your terminal, providing the path to the directory containing your HTML files as a command-line argument.

**Syntax:**
```bash
python Convertor.py "/path/to/your/html_files"
```

**Example:**
```bash
python Convertor.py "C:\Users\Admin\Documents\MyReports"
```

The script will create a `.pdf` file for each `.html` file it finds, saving it in the same directory. A cache folder named `script_cache` will also be created to store the downloaded JavaScript dependencies.

## Configuration

You can adjust the script's behavior by modifying the configuration variables at the top of the `Convertor.py` file:

-   `PARALLEL_JOBS`: The number of HTML files to process concurrently. Defaults to `4`. Increase this for better performance if your machine has more CPU cores, but be mindful of memory usage.
-   `QUALITY_MULTIPLIER`: The device scale factor for screenshots. `2` is equivalent to a "retina" display resolution. Increase for higher quality PDFs at the cost of larger file sizes. Defaults to `2`.
-   `CACHE_DIR`: The name of the directory where JavaScript dependencies are stored. Defaults to `"script_cache"`.
-   `VIEWPORT_HEIGHT`: The height of the viewport for each screenshot. Defaults to `1200`.
-   `DEPENDENCIES`: A dictionary of remote JavaScript library URLs and their local cache filenames. You can add other common libraries to this list to cache them locally.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
