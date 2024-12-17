import streamlit as st
import sqlite3
import requests
from bs4 import BeautifulSoup
import re

# Function to fetch OpenGraph metadata
def fetch_opengraph_data(url):
    try:
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.text, "html.parser")

        def get_og_tag(prop):
            tag = soup.find("meta", property=prop) or soup.find("meta", attrs={"name": prop})
            return tag["content"] if tag and "content" in tag.attrs else None

        og_title = get_og_tag("og:title") or soup.title.string
        og_description = get_og_tag("og:description")
        og_image = get_og_tag("og:image") or "/default-placeholder.png"
        
        return {"title": og_title, "description": og_description, "image": og_image}
    except Exception as e:
        return {"title": "Failed to fetch data", "description": str(e), "image": None}

# Database initialization
def init_db():
    conn = sqlite3.connect("links.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS links (
            id INTEGER PRIMARY KEY,
            url TEXT UNIQUE,
            title TEXT,
            description TEXT,
            image TEXT
        )
    """)
    conn.commit()
    conn.close()

# Save link to the database
def save_link(url, title, description, image):
    conn = sqlite3.connect("links.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO links (url, title, description, image) VALUES (?, ?, ?, ?)",
                       (url, title, description, image))
        conn.commit()
    except sqlite3.IntegrityError:
        st.warning("This link is already saved!")
    finally:
        conn.close()

# Retrieve all links
def get_all_links():
    conn = sqlite3.connect("links.db")
    cursor = conn.cursor()
    cursor.execute("SELECT url, title, description, image FROM links")
    links = cursor.fetchall()
    conn.close()
    return links

# UI Components
st.set_page_config(page_title="Link Manager", layout="wide", initial_sidebar_state="expanded")

# Material Theme-like Styling
st.markdown("""
    <style>
        .card {
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            border-radius: 10px;
            padding: 15px;
            margin: 15px 0;
            background-color: #FFFFFF;
            transition: 0.3s;
        }
        .card:hover {
            box-shadow: 0 8px 16px rgba(0,0,0,0.3);
        }
        img.card-image {
            width: 100%;
            border-radius: 10px 10px 0 0;
        }
        .link-title {
            font-size: 1.2em;
            font-weight: bold;
        }
        .link-description {
            color: #555;
        }
    </style>
""", unsafe_allow_html=True)

# Initialize the database
init_db()

# Sidebar: Add Link
st.sidebar.header("Add New Link")
new_link = st.sidebar.text_input("Enter Link URL", placeholder="https://example.com")
if st.sidebar.button("Save Link"):
    if new_link:
        metadata = fetch_opengraph_data(new_link)
        save_link(new_link, metadata['title'], metadata['description'], metadata['image'])
        st.sidebar.success("Link saved successfully!")
    else:
        st.sidebar.error("Please enter a valid URL.")

# Main Section: Display Links
st.title("🔗 Link Manager")
st.write("Save, view, and manage your links with previews.")

links = get_all_links()

# Display each link as a card
if links:
    for url, title, description, image in links:
        st.markdown(f"""
        <div class="card">
            <img src="{image}" class="card-image" onerror="this.src='/default-placeholder.png'">
            <h4 class="link-title">{title}</h4>
            <p class="link-description">{description}</p>
            <a href="{url}" target="_blank">Visit Link</a>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("No links saved yet. Use the sidebar to add a new link.")
