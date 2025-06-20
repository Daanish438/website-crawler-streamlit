import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin, urlparse
from datetime import datetime
from io import BytesIO

def is_valid_page_link(link, base_url):
    if not link:
        return False
    parsed = urlparse(link)
    ext = parsed.path.split(".")[-1].lower()
    invalid_exts = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp',
                    'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
                    'zip', 'rar', 'mp4', 'mp3', 'avi', 'mov', 'wmv']
    if ext in invalid_exts:
        return False
    if "#" in link:
        return False
    return urlparse(link).netloc == urlparse(base_url).netloc

def crawl(url, base_url, depth=0, max_depth=2, visited=set(), results=[]):
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
                crawl(full_url, base_url, depth + 1, max_depth, visited, results)
    except Exception as e:
        print(f"Failed to crawl {url}: {e}")

# ───────────────────────────────────────────────────────

st.set_page_config(page_title="Website Navigation Crawler", layout="centered")
st.title("🌐 Website Navigation Crawler")
st.write("Enter a website URL and get an Excel file of its navigation structure.")

base_url = st.text_input("Website URL (e.g. https://example.com)", "https://")
max_depth = st.number_input("Crawl Depth (e.g. 2 or 3)", min_value=1, max_value=5, value=2, step=1)
submit = st.button("Generate Sitemap")

if submit and base_url.strip():
    parsed_url = urlparse(base_url)
    if not parsed_url.scheme:
        st.error("Please enter a valid URL with https://")
    else:
        visited = set()
        results = []
        crawl(base_url.strip(), base_url.strip(), 0, max_depth, visited, results)

        df = pd.DataFrame(results).drop_duplicates()
        domain = urlparse(base_url).netloc.replace("www.", "")
        filename = f"{domain}_structure_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        buffer = BytesIO()
        df.to_excel(buffer, index=False)
        buffer.seek(0)

        st.success("✅ Sitemap crawl complete!")
        st.download_button("📥 Download Excel", buffer, file_name=filename, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
