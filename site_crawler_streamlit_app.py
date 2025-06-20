import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin, urlparse
from datetime import datetime
from io import BytesIO

def is_valid_page_link(href, base_url):
    # Filter out images, videos, docs, and hash links
    invalid_exts = (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg", ".mp4", ".avi", ".mov", ".pdf", ".doc", ".docx", ".xls", ".xlsx")
    parsed_href = urlparse(href)
    return (
        href.startswith(base_url)
        and not parsed_href.fragment
        and not any(href.lower().endswith(ext) for ext in invalid_exts)
    )

def crawl(url, base_url, depth=0, max_depth=3):
    if depth > max_depth or url in visited:
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
    except Exception:
        pass

st.set_page_config(page_title="Website Navigation Crawler", page_icon="🌐", layout="centered")
st.title("🌐 Website Navigation Crawler")
st.write("Enter a website URL and get an Excel file of its navigation structure.")

base_url = st.text_input("Website URL (e.g. https://example.com)", "https://")
max_depth = st.number_input("Crawl Depth (e.g. 2 or 3)", min_value=1, max_value=5, value=2, step=1)
submit = st.button("Generate Sitemap")

visited = set()
results = []

if submit and base_url.strip():
    parsed_url = urlparse(base_url)
    if not parsed_url.scheme:
        st.error("Please enter a valid URL with https://")
    else:
        with st.status("🔄 Crawling in progress...", expanded=False):
            visited.clear()
            results.clear()
            crawl(base_url.strip(), base_url.strip(), 0, max_depth)

        df = pd.DataFrame(results).drop_duplicates()
        domain = urlparse(base_url).netloc.replace("www.", "")
        filename = f"{domain}_structure_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        df.to_excel(filename, index=False)

        with open(filename, "rb") as f:
            st.download_button("📥 Download Excel", f, file_name=filename, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
