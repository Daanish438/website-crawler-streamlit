import streamlit as st
import pandas as pd
from urllib.parse import urljoin, urlparse
from io import BytesIO
from datetime import datetime
from playwright.sync_api import sync_playwright

st.set_page_config(page_title="Website Navigation Crawler", page_icon="🌐", layout="centered")

st.title("🌐 Website Navigation Crawler")
st.write("Enter a website URL and get an Excel file of its navigation structure.")

base_url = st.text_input("Website URL (e.g. https://example.com)", "https://")
max_depth = st.number_input("Crawl Depth (e.g. 2 or 3)", min_value=1, max_value=5, value=2, step=1)
submit = st.button("Generate Sitemap")

visited = set()
results = []

def is_valid_page_link(href, base_url):
    if not href or href.startswith(("mailto:", "tel:", "javascript:", "#")):
        return False
    parsed_href = urlparse(href)
    if any(parsed_href.path.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".mp4", ".avi", ".mov", ".wmv", ".zip", ".rar", ".exe"]):
        return False
    full_url = urljoin(base_url, href)
    parsed_base = urlparse(base_url)
    parsed_full = urlparse(full_url)
    return parsed_base.netloc == parsed_full.netloc

def crawl(page, url, base_url, depth, max_depth):
    if depth > max_depth or url in visited:
        return
    try:
        page.goto(url)
        st.session_state['status'] = f"Crawling: {url}"
        visited.add(url)
        title = page.title()
        results.append({'Navigation': title.strip() if title else 'No title', 'URL': url})
        anchors = page.locator("a")
        hrefs = anchors.evaluate_all("nodes => nodes.map(n => n.href)")
        for href in hrefs:
            if is_valid_page_link(href, base_url):
                crawl(page, href, base_url, depth + 1, max_depth)
    except Exception as e:
        pass

if submit and base_url.strip():
    if not urlparse(base_url).scheme:
        st.error("Please enter a valid URL with https://")
    else:
        with st.spinner("Crawling in progress..."):
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context()
                page = context.new_page()
                visited.clear()
                results.clear()
                crawl(page, base_url.strip(), base_url.strip(), 0, max_depth)
                browser.close()

            df = pd.DataFrame(results).drop_duplicates()
            domain = urlparse(base_url).netloc.replace("www.", "")
            filename = f"{domain}_structure_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            df.to_excel(filename, index=False)
            with open(filename, "rb") as f:
                st.success("✅ Crawling complete!")
                st.download_button("📥 Download Excel", f, file_name=filename, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
