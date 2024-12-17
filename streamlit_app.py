import streamlit as st
import requests
from bs4 import BeautifulSoup
import urllib.parse
import sqlite3
from datetime import datetime
import validators

class LinkManager:
    def __init__(self):
        # Initialize SQLite database
        self.conn = sqlite3.connect('links.db', check_same_thread=False)
        self.create_table()

    def create_table(self):
        """Create links table if not exists"""
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE,
                title TEXT,
                description TEXT,
                image_url TEXT,
                added_at DATETIME
            )
        ''')
        self.conn.commit()

    def extract_metadata(self, url):
        """Extract Open Graph and basic metadata from URL"""
        try:
            # Validate URL first
            if not validators.url(url):
                return None

            # Fetch webpage
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract Open Graph metadata
            og_title = soup.find('meta', property='og:title')
            og_description = soup.find('meta', property='og:description')
            og_image = soup.find('meta', property='og:image')
            
            # Fallback to HTML meta tags
            title = (og_title and og_title.get('content')) or soup.title.string if soup.title else url
            description = (og_description and og_description.get('content')) or ''
            image_url = (og_image and og_image.get('content')) or ''
            
            # Ensure absolute image URL
            if image_url and not image_url.startswith(('http://', 'https://')):
                image_url = urllib.parse.urljoin(url, image_url)
            
            return {
                'title': title,
                'description': description,
                'image_url': image_url
            }
        
        except Exception as e:
            st.error(f"Error extracting metadata: {e}")
            return None

    def save_link(self, url):
        """Save link to database"""
        metadata = self.extract_metadata(url)
        if metadata:
            cursor = self.conn.cursor()
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO links 
                    (url, title, description, image_url, added_at) 
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    url, 
                    metadata['title'], 
                    metadata['description'], 
                    metadata['image_url'], 
                    datetime.now()
                ))
                self.conn.commit()
                st.success("Link saved successfully!")
                return True
            except sqlite3.IntegrityError:
                st.warning("This link already exists.")
                return False
        return False

    def get_all_links(self):
        """Retrieve all saved links"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM links ORDER BY added_at DESC')
        return cursor.fetchall()

def main():
    st.set_page_config(
        page_title="Link Manager", 
        page_icon="🔗", 
        layout="wide"
    )

    # Dark Mode Material Design CSS
    st.markdown("""
    <style>
    /* Dark Mode Base Styles */
    .stApp {
        background-color: #121212;
        color: #E0E0E0;
        font-family: 'Roboto', sans-serif;
    }

    /* Dark Mode Input Styles */
    .stTextInput > div > div > input {
        background-color: #1E1E1E;
        color: #E0E0E0;
        border-radius: 8px;
        border: 1px solid #333;
        padding: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }

    /* Dark Mode Button Styles */
    .stButton > button {
        background-color: #BB86FC;
        color: #000;
        border-radius: 8px;
        border: none;
        padding: 10px 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.4);
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background-color: #9767E6;
        box-shadow: 0 4px 6px rgba(0,0,0,0.5);
    }

    /* Link Card Styles */
    .link-card {
        background-color: #1E1E1E;
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        border: 1px solid #333;
        transition: transform 0.3s ease;
    }
    .link-card:hover {
        transform: scale(1.02);
        border-color: #BB86FC;
    }

    /* Typography */
    h1, h2, h3 {
        color: #BB86FC;
    }
    p {
        color: #E0E0E0;
    }

    /* Custom Link Button */
    .custom-link-button {
        width: 100%;
        background-color: #BB86FC !important;
        color: #000 !important;
        border: none;
        border-radius: 8px;
        padding: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

    # Initialize Link Manager
    link_manager = LinkManager()

    # App Title
    st.title("🔗 Link Manager")

    # Link Input Section
    with st.form("link_form", clear_on_submit=True):
        url = st.text_input("Enter URL to Save")
        submit_button = st.form_submit_button("Save Link")
        
        if submit_button and url:
            link_manager.save_link(url)

    # Display Saved Links
    st.header("Saved Links")
    
    # Fetch and display links
    saved_links = link_manager.get_all_links()
    
    # Create columns for grid layout
    cols = st.columns(3)
    
    for i, link in enumerate(saved_links):
        col = cols[i % 3]
        with col:
            # Custom card design with dark mode
            st.markdown(f"""
            <div class="link-card">
                {'<img src="' + (link[4] or 'https://via.placeholder.com/300x200?text=No+Preview') + '" style="width:100%;border-radius:8px;margin-bottom:10px;object-fit:cover;max-height:200px;">' if link[4] else ''}
                <h3 style="color:#BB86FC;">{link[2] or 'Untitled Link'}</h3>
                <p>{link[3][:100] + '...' if link[3] else 'No description'}</p>
                <a href="{link[1]}" target="_blank" style="text-decoration:none;">
                    <button class="custom-link-button">Open Link</button>
                </a>
            </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
