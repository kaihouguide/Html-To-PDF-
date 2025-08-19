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


def split_and_save_pdf(img_data, pdf_path):
    """Split one giant screenshot into multiple <=65k strips and save as multi-page PDF"""
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
    browser = await playwright.chromium.launch(headless=True)
    page = await browser.new_page()

    await page.goto(f"file:///{os.path.abspath(html_path)}")
    await page.wait_for_load_state("networkidle")

    print(f"  - Capturing {os.path.basename(html_path)} (full-page)")

    # 🚀 Single full-page screenshot
    data = await page.screenshot(full_page=True)

    split_and_save_pdf(data, pdf_path)
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
        print("Usage: python ai_studio_code.py <input_dir>")
        sys.exit(1)
    input_dir = sys.argv[1]
    asyncio.run(process_all(input_dir))
