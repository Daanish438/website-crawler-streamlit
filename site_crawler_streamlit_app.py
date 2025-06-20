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

def is_valid_page_link(link, base_domain):
    parsed = urlparse(link)

    # Skip if fragment (#...) is present in path, params, or fragment
    if "#" in parsed.path or "#" in parsed.params or "#" in parsed.fragment or "#" in link:
        return False

    # Skip assets
    if any(link.lower().endswith(ext) for ext in [
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".pdf",
        ".doc", ".docx", ".ppt", ".pptx", ".mp4", ".mov", ".avi", ".zip", ".rar"
    ]):
        return False

    # Basic checks
    if parsed.scheme not in ["http", "https"]:
        return False
    if not parsed.netloc or base_domain not in parsed.netloc:
        return False

    return True

def crawl(url, base_url, depth=0, max_depth=2):
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
            if is_valid_page_link(full_url, urlparse(base_url).netloc):
                crawl(full_url, base_url, depth + 1, max_depth)
    except Exception:
        pass

if submit and base_url.strip():
    parsed_url = urlparse(base_url)
    if not parsed_url.scheme:
        st.error("Please enter a valid URL starting with https://")
    else:
        visited.clear()
        results.clear()
        with st.status("🔄 Crawling in progress...", expanded=False) as status:
            crawl(base_url.strip(), base_url.strip(), 0, max_depth)
            status.update(label="✅ Crawling complete!", state="complete", expanded=False)

        df = pd.DataFrame(results).drop_duplicates()
        domain = urlparse(base_url).netloc.replace("www.", "")
        filename = f"{domain}_structure_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        df.to_excel(filename, index=False)

        with open(filename, "rb") as f:
            st.download_button("📥 Download Excel", f, file_name=filename, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
