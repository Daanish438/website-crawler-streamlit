import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin, urlparse
from datetime import datetime
from io import BytesIO

st.set_page_config(page_title="Website Navigation Crawler", page_icon="🌐", layout="centered")

st.title("🌐 Website Navigation Crawler")
st.write("Enter a website URL and get an Excel file of its navigation structure.")

base_url = st.text_input("Website URL (e.g. https://example.com)", "https://")
max_depth = st.number_input("Crawl Depth (e.g. 2 or 3)", min_value=1, max_value=5, value=2, step=1)
submit = st.button("Generate Sitemap")

visited = set()
results = []

def is_valid_page_link(href, base):
    """Exclude links to non-HTML resources and anchors."""
    if not href or href.startswith("#"):
        return False
    href = href.lower()
    excluded_exts = (".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp",
                     ".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx",
                     ".zip", ".rar", ".tar", ".mp4", ".mp3", ".avi", ".mov",
                     ".wmv", ".exe", ".dmg", ".iso", ".css", ".js")
    parsed = urlparse(href)
    return (
        href.startswith("/") or parsed.netloc == urlparse(base).netloc
    ) and not parsed.fragment and not href.endswith(excluded_exts)

def crawl(url, base_url, depth, max_depth):
    if url in visited or depth > max_depth:
        return
    try:
        response = requests.get(url, timeout=10)
        visited.add(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.title.string.strip() if soup.title and soup.title.string else 'No title'
        results.append({'Navigation': title, 'URL': url})
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(base_url, href)
            if is_valid_page_link(full_url, base_url):
                crawl(full_url, base_url, depth + 1, max_depth)
    except Exception as e:
        pass  # Suppress crawl errors silently

if submit and base_url.strip():
    parsed_url = urlparse(base_url)
    if not parsed_url.scheme:
        st.error("Please enter a valid URL with https://")
    else:
        visited.clear()
        results.clear()
        with st.status("🔄 Crawling in progress...", expanded=False):
            crawl(base_url.strip(), base_url.strip(), 0, max_depth)

        df = pd.DataFrame(results).drop_duplicates()
        domain = urlparse(base_url).netloc.replace("www.", "")
        filename = f"{domain}_structure_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        df.to_excel(filename, index=False)

        with open(filename, "rb") as f:
            st.download_button("⬇️ Download Excel", f, file_name=filename,
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
