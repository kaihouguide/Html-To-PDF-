import asyncio
import os
import sys
from io import BytesIO
from PIL import Image
from pypdf import PdfWriter
from playwright.async_api import async_playwright

# ---- Config ----
PARALLEL_JOBS = 4
MAX_IMAGE_HEIGHT = 65000  # Pillow limit per page
# ----------------


def save_stitched_image_as_pdf(img_data, pdf_path):
    """Saves a potentially very tall image as a multi-page PDF, splitting it if necessary."""
    Image.MAX_IMAGE_PIXELS = None
    
    im = Image.open(BytesIO(img_data)).convert("RGB")
    width, height = im.size

    writer = PdfWriter()

    for top in range(0, height, MAX_IMAGE_HEIGHT):
        box = (0, top, width, min(top + MAX_IMAGE_HEIGHT, height))
        part = im.crop(box)

        buf = BytesIO()
        part.save(buf, "PDF")
        writer.append(BytesIO(buf.getvalue()))

    with open(pdf_path, "wb") as f:
        writer.write(f)
    writer.close()


async def capture_html_to_pdf(playwright, html_path, pdf_path):
    """Takes screenshots of smaller parts of a webpage and stitches them into a long page."""
    browser = await playwright.chromium.launch(headless=True)
    page = await browser.new_page()

    await page.goto(f"file:///{os.path.abspath(html_path)}")
    await page.wait_for_load_state("networkidle")

    print(f"  - Capturing {os.path.basename(html_path)} (by stitching parts)")

    # --- New logic for scrolling and taking multiple screenshots ---
    screenshot_parts = []
    total_height = await page.evaluate("document.body.scrollHeight")
    viewport_height = page.viewport_size['height']
    current_scroll = 0

    while current_scroll < total_height:
        screenshot = await page.screenshot()
        screenshot_parts.append(Image.open(BytesIO(screenshot)))
        current_scroll += viewport_height
        await page.mouse.wheel(0, viewport_height)
        # Give some time for lazy-loaded content to appear
        await page.wait_for_timeout(100)

    # Stitch the images together
    if screenshot_parts:
        first_image = screenshot_parts[0]
        width = first_image.width
        stitched_height = sum(img.height for img in screenshot_parts)
        
        stitched_image = Image.new('RGB', (width, stitched_height))
        y_offset = 0
        for img in screenshot_parts:
            stitched_image.paste(img, (0, y_offset))
            y_offset += img.height

        # Save the stitched image to a buffer
        stitched_image_data = BytesIO()
        stitched_image.save(stitched_image_data, format='PNG')
        stitched_image_data.seek(0)
        
        save_stitched_image_as_pdf(stitched_image_data.getvalue(), pdf_path)

    await browser.close()

    print(f"  ✅ Saved {os.path.basename(pdf_path)}")


async def process_all(input_dir):
    files = [f for f in os.listdir(input_dir) if f.endswith(".html")]
    print(f"🔄 Found {len(files)} files. Starting conversion...")

    sem = asyncio.Semaphore(PARALLEL_JOBS)

    async def worker(f):
        async with sem:
            name = os.path.splitext(f)[0]
            pdf_path = os.path.join(input_dir, name + ".pdf")
            if os.path.exists(pdf_path):
                print(f"⏭️  Skipping (exists): {os.path.basename(pdf_path)}")
                return
            print(f"▶️  Processing {f}")
            try:
                async with async_playwright() as p:
                    await capture_html_to_pdf(p, os.path.join(input_dir, f), pdf_path)
            except Exception as e:
                print(f"  ❌ Error in {f}: {e}")

    await asyncio.gather(*(worker(f) for f in files))

    print("✅ All done!")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python convertor.py <input_dir>")
        sys.exit(1)
    input_dir = sys.argv[1]
    asyncio.run(process_all(input_dir))