import asyncio
import os
import sys
import aiohttp
import aiofiles
from playwright.async_api import async_playwright
from PIL import Image
from pypdf import PdfWriter

# Allow Pillow to handle large images without raising a DecompressionBombError
Image.MAX_IMAGE_PIXELS = None

# --- Configuration ---
PARALLEL_JOBS = 4
QUALITY_MULTIPLIER = 2
CACHE_DIR = "script_cache"
VIEWPORT_HEIGHT = 1200
PIXEL_LIMIT_PER_STRIP = 65000 # A safe limit, slightly less than the theoretical max

# --- Dependencies to be cached locally ---
DEPENDENCIES = {
    "https://cdn.plot.ly/plotly-2.32.0.min.js": "plotly.js",
    "https://d3js.org/d3.v7.min.js": "d3.js",
    "https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js": "mathjax.js",
}


async def ensure_dependencies_cached():
    """Checks if JavaScript dependencies are cached and downloads them if not."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    async with aiohttp.ClientSession() as session:
        for url, filename in DEPENDENCIES.items():
            local_path = os.path.join(CACHE_DIR, filename)
            if not os.path.exists(local_path):
                print(f"'{filename}' not found. Downloading...")
                try:
                    async with session.get(url) as response:
                        response.raise_for_status()
                        content = await response.read()
                        async with aiofiles.open(local_path, 'wb') as f:
                            await f.write(content)
                        print(f"  ✅ Cached '{filename}'")
                except Exception as e:
                    print(f"  ❌ Failed to download '{filename}': {e}")
                    return False
    return True


async def process_single_file(index, total, semaphore, browser, html_file_path, output_directory, cached_urls):
    """
    Processes one HTML file: takes scrolling screenshots, stitches them into
    long strips (chunked to avoid image size limits), and merges them into a
    single, multi-page "long strip" PDF.
    """
    async with semaphore:
        base_filename = os.path.splitext(os.path.basename(html_file_path))[0]
        final_pdf_path = os.path.join(output_directory, f"{base_filename}.pdf")
        print(f"▶️ [{index}/{total}] Processing: {os.path.basename(html_file_path)}")

        image_paths = []
        temp_pdf_paths = []
        context = None
        page = None
        try:
            context = await browser.new_context(
                viewport={"width": 1280, "height": VIEWPORT_HEIGHT},
                device_scale_factor=QUALITY_MULTIPLIER
            )
            page = await context.new_page()

            async def handle_route(route):
                if route.request.url in cached_urls:
                    await route.fulfill(path=os.path.join(CACHE_DIR, DEPENDENCIES[route.request.url]))
                else:
                    await route.continue_()

            await page.route("**/*", handle_route)
            await page.goto(f'file://{html_file_path}', wait_until='networkidle', timeout=90000)

            total_height = await page.evaluate("() => document.body.scrollHeight")
            num_screenshots = (total_height + VIEWPORT_HEIGHT - 1) // VIEWPORT_HEIGHT

            for i in range(num_screenshots):
                offset = i * VIEWPORT_HEIGHT
                await page.evaluate(f"window.scrollTo(0, {offset})")
                await asyncio.sleep(0.1)
                temp_path = os.path.join(output_directory, f"{base_filename}_part{i}.png")
                await page.screenshot(path=temp_path)
                image_paths.append(temp_path)

            if image_paths:
                images = [Image.open(p) for p in image_paths]
                strip_width = images[0].width
                img_height = images[0].height
                imgs_per_strip = PIXEL_LIMIT_PER_STRIP // img_height
                image_chunks = [images[i:i + imgs_per_strip] for i in range(0, len(images), imgs_per_strip)]

                for i, chunk in enumerate(image_chunks):
                    chunk_height = sum(img.height for img in chunk)
                    long_strip = Image.new('RGB', (strip_width, chunk_height))
                    y_offset = 0
                    for img in chunk:
                        long_strip.paste(img, (0, y_offset))
                        y_offset += img.height
                    
                    temp_pdf_path = os.path.join(output_directory, f"{base_filename}_temp_strip_{i}.pdf")
                    long_strip.save(temp_pdf_path, "PDF", resolution=100.0)
                    temp_pdf_paths.append(temp_pdf_path)

                for img in images:
                    img.close()

                pdf_merger = PdfWriter()
                for path in temp_pdf_paths:
                    pdf_merger.append(path)
                with open(final_pdf_path, 'wb') as f:
                    pdf_merger.write(f)
                pdf_merger.close()
                print(f"  ✅ Created merged long-strip PDF: {os.path.basename(final_pdf_path)}")

        except Exception as e:
            print(f"  ❌ Error processing {base_filename}: {e}")
        finally:
            if page: await page.close()
            if context: await context.close()
            for path in image_paths + temp_pdf_paths:
                if os.path.exists(path):
                    os.remove(path)


async def main():
    """Main function to orchestrate the conversion process."""
    # --- MODIFIED: Read path from command-line argument ---
    if len(sys.argv) < 2:
        print("❌ Error: No folder path provided.")
        print("   Usage: python code(15).py \"C:\\path\\to\\your\\html_files\"")
        return

    directory_path = sys.argv[1]
    # --- END OF MODIFICATION ---

    if not os.path.isdir(directory_path):
        print(f"❌ Invalid path: '{directory_path}' is not a valid folder.")
        return

    if not await ensure_dependencies_cached():
        print("Could not retrieve all dependencies. Aborting.")
        return

    html_files = [os.path.join(directory_path, f) for f in os.listdir(directory_path) if f.lower().endswith('.html')]
    if not html_files:
        print(f"❌ No HTML files found in '{directory_path}'")
        return

    total = len(html_files)
    semaphore = asyncio.Semaphore(PARALLEL_JOBS)
    cached_urls = set(DEPENDENCIES.keys())
    print(f"\n🔄 Found {total} files. Converting with {PARALLEL_JOBS} parallel jobs...\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-gpu"])
        tasks = [process_single_file(i + 1, total, semaphore, browser, file_path, directory_path, cached_urls) for i, file_path in enumerate(html_files)]
        await asyncio.gather(*tasks)
        await browser.close()

    print("\n✅ All files converted successfully!")


if __name__ == '__main__':
    asyncio.run(main())
