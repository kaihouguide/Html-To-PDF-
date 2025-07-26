# HTML to PDF Converter

This script provides a powerful and robust solution for converting a directory of local HTML files into high-quality PDFs. It is specifically designed to handle complex, dynamic, and exceptionally long pages that often fail with standard "Print to PDF" functions, such as dashboards rich with Plotly.js or D3.js visualizations.

The script uses a headless browser to ensure all web content, including JavaScript-rendered elements, is fully loaded and captured with high fidelity.

## Features

-   **High-Fidelity Rendering**: Utilizes a headless Chromium browser via Playwright to render HTML files precisely as they appear online, capturing complex JavaScript, SVGs, and interactive charts.
-   **Robust Capture Strategy**: Implements a dual-strategy approach: it first attempts a fast, full-page screenshot and, if the page is too long for the browser's engine, automatically falls back to a more robust method of capturing and stitching viewport-sized chunks.
-   **Parallel Processing**: Converts multiple files concurrently using `asyncio` to dramatically reduce processing time for large batches of files.
-   **Offline Dependency Caching**: Automatically downloads and caches external JavaScript libraries (`Plotly`, `D3.js`, `MathJax`) on the first run. Subsequent runs use the local cache for faster performance and offline capability.
-   **High-Resolution Output**: Generates high-quality, crisp PDFs by rendering the page at a higher device scale factor (e.g., "retina" resolution).
-   **Efficient In-Memory Processing**: All image stitching and PDF creation is handled in-memory to maximize speed and avoid creating temporary files on disk.
-   **Simple Command-Line Interface**: Point the script to a folder of HTML files and let it run.

## How It Works

The script automates the following workflow for each HTML file:

1.  **Launch Headless Browser**: A headless Chromium browser instance is launched using Playwright.
2.  **Route Dependencies**: To accelerate rendering and enable offline use, the script intercepts network requests for specified JavaScript libraries and serves them directly from the local cache.
3.  **Load and Stabilize Page**: The script loads the HTML file and then employs a comprehensive waiting strategy. It scrolls through the entire page to trigger lazy-loaded elements and then waits for network activity, MathJax rendering, and Plotly charts to complete.
4.  **Attempt Full-Page Capture**: The primary strategy is to take a single, full-page screenshot. This is the fastest method and is used for most pages.
5.  **Fallback to Stitching**: If the full-page capture fails because the page's height exceeds the browser's maximum image dimensions, the script automatically switches to its fallback strategy. It programmatically scrolls down the page, taking screenshots of each viewport section.
6.  **Stitch and Generate PDF**:
    *   The captured image chunks are stitched together vertically using the Pillow library to create long image "strips." To avoid memory errors with extremely tall pages, it intelligently segments these strips into multiple pages within the final PDF.
    *   The final PDF is assembled in-memory and written directly to the output directory.

## Requirements

-   Python 3.7+
-   Required Python libraries (listed below).

### Python Dependencies
-   `playwright`
-   `aiohttp`
-   `aiofiles`
-   `Pillow`
-   `pypdf`

## Installation & Setup

1.  **Save the script:**
    Save the code as a Python file (e.g., `convert.py`).

2.  **Install Python Dependencies:**
    Install all required libraries using pip in a single command:
    ```bash
    pip install "playwright>=1.40" aiohttp aiofiles Pillow "pypdf>=4.0"
    ```

3.  **Install Playwright Browser Binaries:**
    The first time you use Playwright, you must install the necessary browser drivers. The script is configured to use Chromium.
    ```bash
    playwright install chromium
    ```

## Usage

Run the script from your terminal, providing the path to the directory containing your HTML files as a command-line argument.

**Syntax:**
```bash
python convert.py "/path/to/your/html_files"
```

**Example:**
```bash
python convert.py "C:\Users\Admin\Documents\Reports"
```

The script will create a `.pdf` file for each `.html` file it finds, saving it in the same source directory. A cache folder (default: `script_cache`) will be created in the same location as the script to store the downloaded JavaScript dependencies.

## Configuration

You can easily adjust the script's performance and output by modifying the configuration variables at the top of the file:

-   `Image.MAX_IMAGE_PIXELS`: Set to `None` to allow the Pillow library to handle very large images.
-   `PIXEL_LIMIT_PER_STRIP`: The maximum vertical pixel height for a single PDF page before the script creates a new page. Protects against image processing limits.
-   `PARALLEL_JOBS`: The number of HTML files to process concurrently. Increase for better performance if your machine has sufficient CPU cores and memory.
-   `QUALITY_MULTIPLIER`: The device scale factor for screenshots. `2` is equivalent to a "retina" display resolution. Increase for higher quality PDFs at the cost of larger file sizes and more memory usage.
-   `CACHE_DIR`: The name of the directory where JavaScript dependencies are stored.
-   `VIEWPORT_HEIGHT`: The height of the browser viewport used when scrolling and capturing page chunks in the fallback strategy.
-   `SCREENSHOT_TIMEOUT`: A generous timeout (in milliseconds) for the screenshot command, to accommodate very large or slow-rendering pages.
-   `DEPENDENCIES`: A dictionary of remote JavaScript library URLs and their local filenames. You can add other common libraries to this list to cache them locally.
