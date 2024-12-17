import streamlit as st
import requests
from bs4 import BeautifulSoup
import urllib.parse
import sqlite3
from datetime import datetime
import validators
import logging

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
        """Enhanced metadata extraction with multiple fallback methods"""
        try:
            # Validate URL first
            if not validators.url(url):
                st.error("Invalid URL")
                return None

            # Fetch webpage
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()  # Raise an error for bad status codes
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Priority 1: Open Graph metadata
            og_title = soup.find('meta', property='og:title')
            og_description = soup.find('meta', property='og:description')
            og_image = soup.find('meta', property='og:image')
            
            # Priority 2: Twitter Card metadata
            twitter_title = soup.find('meta', property='twitter:title')
            twitter_description = soup.find('meta', property='twitter:description')
            twitter_image = soup.find('meta', property='twitter:image')
            
            # Fallback methods
            title = (
                (og_title and og_title.get('content')) or 
                (twitter_title and twitter_title.get('content')) or 
                (soup.title and soup.title.string) or 
                url
            )
            
            description = (
                (og_description and og_description.get('content')) or 
                (twitter_description and twitter_description.get('content')) or 
                ''
            )
            
            image_url = (
                (og_image and og_image.get('content')) or 
                (twitter_image and twitter_image.get('content')) or 
                ''
            )
            
            # Ensure absolute image URL
            if image_url and not image_url.startswith(('http://', 'https://')):
                image_url = urllib.parse.urljoin(url, image_url)
            
            # Truncate description
            description = description[:250] + '...' if len(description) > 250 else description
            
            return {
                'title': title or 'Untitled',
                'description': description or 'No description',
                'image_url': image_url or 'https://via.placeholder.com/300x200?text=No+Preview'
            }
        
        except Exception as e:
            logging.error(f"Metadata extraction error for {url}: {e}")
            return {
                'title': url,
                'description': 'Unable to fetch metadata',
                'image_url': 'https://via.placeholder.com/300x200?text=Preview+Unavailable'
            }

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
    /* Existing dark mode styles remain the same */
    .link-card img {
        width: 100%;
        height: 200px;
        object-fit: cover;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    .link-preview-text {
        display: -webkit-box;
        -webkit-line-clamp: 3;
        -webkit-box-orient: vertical;
        overflow: hidden;
        text-overflow: ellipsis;
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
            # Custom card design with improved preview
            st.markdown(f"""
            <div class="link-card">
                <img src="{link[4] or 'https://via.placeholder.com/300x200?text=No+Preview'}" alt="Link Preview" onerror="this.onerror=null; this.src='https://via.placeholder.com/300x200?text=Preview+Failed';">
                <h3 style="color:#BB86FC;">{link[2] or 'Untitled Link'}</h3>
                <p class="link-preview-text" style="color:#E0E0E0;">{link[3] or 'No description'}</p>
                <a href="{link[1]}" target="_blank" style="text-decoration:none;">
                    <button class="custom-link-button" style="width:100%; background-color:#BB86FC !important; color:#000 !important; border:none; border-radius:8px; padding:8px;">Open Link</button>
                </a>
            </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
