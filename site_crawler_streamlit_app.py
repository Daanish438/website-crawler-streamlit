
import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin, urlparse
from io import BytesIO

st.set_page_config(page_title="Site Structure Crawler", layout="centered")

st.title("🌐 Website Navigation Crawler")
st.write("Enter a website URL and get an Excel file of its navigation structure.")

url = st.text_input("Website URL (e.g. https://example.com)")
depth_input = st.number_input("Crawl Depth (e.g. 2 or 3)", min_value=1, max_value=5, value=2)

if st.button("Generate Sitemap"):
    if not url:
        st.warning("Please enter a valid URL.")
    else:
        visited = set()
        structured_rows = []

        def generate_label(soup, depth):
            title = soup.title.string.strip() if soup.title else 'No title'
            if '|' in title:
                title = title.split('|')[0]
            elif '-' in title:
                title = title.split('-')[0]
            return title.strip() if depth > 0 else "Homepage"

        def crawl(link, base_url, depth=0, max_depth=2):
            if depth > max_depth or link in visited:
                return
            try:
                visited.add(link)
                headers = {
                    'User-Agent': 'Mozilla/5.0'
                }
                res = requests.get(link, headers=headers, timeout=10)
                soup = BeautifulSoup(res.text, 'html.parser')

                label = generate_label(soup, depth)
                structured_rows.append({'Navigation': label, 'URL': link})

                for a_tag in soup.find_all('a', href=True):
                    full_url = urljoin(base_url, a_tag['href'])
                    if urlparse(full_url).netloc == urlparse(base_url).netloc:
                        crawl(full_url, base_url, depth + 1, max_depth)
            except:
                pass

        with st.spinner("Crawling in progress..."):
            crawl(url, url, max_depth=depth_input)
            df = pd.DataFrame(structured_rows).drop_duplicates()

            output = BytesIO()
            df.to_excel(output, index=False, engine='openpyxl')
            output.seek(0)

            st.success("✅ Done! Download your Excel file below.")
            st.download_button(
                label="📥 Download Excel",
                data=output,
                file_name=f"{urlparse(url).netloc}_structure.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
