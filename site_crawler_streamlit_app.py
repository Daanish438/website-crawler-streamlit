
import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from io import BytesIO

visited = set()
results = []

def crawl(url, base_url, depth=0, max_depth=2):
    if depth > max_depth or url in visited:
        return
    try:
        visited.add(url)
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.title.string.strip() if soup.title else 'No title'
        results.append({'Page Title': title, 'URL': url})
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(base_url, href)
            if urlparse(full_url).netloc == urlparse(base_url).netloc and full_url not in visited:
                # Only crawl .html, no extension, or ending with '/'
                path = urlparse(full_url).path
                if (
                    path.endswith('/') or
                    path.endswith('.html') or
                    '.' not in Path(path).name
                ):
                    crawl(full_url, base_url, depth + 1, max_depth)
    except Exception:
        pass

# Streamlit UI
st.set_page_config(page_title="Website Navigation Crawler", layout="centered")
st.title("🌐 Website Navigation Crawler")
st.write("Enter a website URL and get an Excel file of its navigation structure.")

url = st.text_input("Website URL (e.g. https://example.com)")
depth_input = st.number_input("Crawl Depth (e.g. 2 or 3)", min_value=1, max_value=5, value=2)

if st.button("Generate Sitemap"):
    if not url:
        st.warning("Please enter a valid URL.")
    else:
        visited.clear()
        results.clear()
        with st.spinner("Crawling website..."):
            crawl(url, url, depth=0, max_depth=depth_input)
            df = pd.DataFrame(results).drop_duplicates()
            excel_buffer = BytesIO()
            domain = urlparse(url).netloc.replace('.', '_')
            filename = f"{domain}_structure.xlsx"
            df.to_excel(excel_buffer, index=False, engine='openpyxl')
            st.success("✅ Crawl complete!")
            st.download_button(
                label="📥 Download Excel File",
                data=excel_buffer.getvalue(),
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
