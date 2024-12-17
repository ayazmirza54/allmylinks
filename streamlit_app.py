import streamlit as st
from streamlit_card import card
import requests
from bs4 import BeautifulSoup
import re
from tinydb import TinyDB, Query
from opengraph import OpenGraph
import os
from urllib.parse import urljoin

st.set_page_config(page_title="Link Manager", page_icon="🔗", layout="wide")

# Initialize TinyDB
DB_FILE = "links.json"
db = TinyDB(DB_FILE)
links_table = db.table("links")
Link = Query()

DEFAULT_IMAGE = "https://via.placeholder.com/150"

def get_opengraph_data(url):
    """Fetches OpenGraph data (title, description, image) from a URL using opengraph library."""
    try:
        og = OpenGraph(url,timeout=5)
        og_data = {}
        og_data['title'] = og.get('title', 'No Title')
        og_data['description'] = og.get('description', '')
        og_data['image'] = og.get('image', '')

        if og_data['image'] and not og_data['image'].startswith(("http://", "https://")):
          og_data['image'] = urljoin(url,og_data['image'])

        return og_data
    except Exception as e:
        st.error(f"Error fetching URL: {e}")
        return {'title': 'Error fetching title', 'description': 'Error fetching description', 'image':''}


def is_valid_url(url):
    """Checks if the URL is valid using a regular expression."""
    regex = re.compile(
        r'^(?:http|ftp)s?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url) is not None

def main():
    st.title("🔗 Link Manager")

    # Input form
    with st.form(key="link_form"):
      url_input = st.text_input("Enter URL:", placeholder="https://example.com")
      submit_button = st.form_submit_button("Add Link")
    
    if submit_button:
      if not url_input:
        st.warning("Please enter a link.")
      elif not is_valid_url(url_input):
        st.error("Please enter a valid URL.")
      else:
          og_data = get_opengraph_data(url_input)
          links_table.insert({"url": url_input, "og_data": og_data})
          st.success("Link Added Successfully!")

    # Fetch links from TinyDB
    links = links_table.all()
    # Display links in cards using Material-style UI
    if links:
      st.markdown("---")
      for i, link in enumerate(links):
          col1, col2 = st.columns([1,3])
          with col1:
              image_url = link["og_data"].get("image","")
              if image_url:
                 st.image(image_url, use_column_width=True, width=100)
              else:
                st.image(DEFAULT_IMAGE, use_column_width=True, width=100)
          with col2:
            with st.expander(link["og_data"].get("title","No Title"), expanded=True):
                st.markdown(f"**URL:** [{link['url']}]({link['url']})")
                description = link["og_data"].get("description","")
                if description:
                    st.markdown(f"**Description:** {description}")
    else:
      st.info("No links saved yet")

if __name__ == "__main__":
    main()
