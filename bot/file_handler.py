import requests
import os
from datetime import datetime
from database import Database
from config import BOT_TOKEN

class FileHandler:
    def __init__(self):
        self.db = Database()
    
    def shorten_url(self, original_url):
        """Shorten URL using ouo.io"""
        try:
            # ouo.io API integration
            api_url = f"http://ouo.io/api/qs/tmqxi7by?s={original_url}"
            response = requests.get(api_url)
            return response.url if response.status_code == 200 else original_url
        except Exception as e:
            print(f"URL shortening failed: {e}")
            return original_url
    
    def get_file_direct_link(self, file_id):
        """Get direct download link for Telegram file"""
        try:
            # First get file path from Telegram API
            file_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={file_id}"
            response = requests.get(file_url)
            
            if response.status_code == 200:
                file_path = response.json()['result']['file_path']
                direct_link = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
                return direct_link
            return None
        except Exception as e:
            print(f"Error getting file link: {e}")
            return None
    
    def process_files(self, files, channel_link):
        """Process multiple files and store in database"""
        processed_files = []
        
        for file in files:
            try:
                # Get file info
                file_name = file.file_name or f"file_{file.file_id}"
                direct_link = self.get_file_direct_link(file.file_id)
                shortened_link = self.shorten_url(direct_link) if direct_link else None
                
                file_data = {
                    "file_id": file.file_id,
                    "file_name": file_name,
                    "channel_link": channel_link,
                    "direct_link": direct_link,
                    "shortened_link": shortened_link,
                    "file_size": file.file_size,
                    "mime_type": file.mime_type,
                    "uploaded_at": datetime.now().isoformat()
                }
                
                # Store in database
                self.db.insert_file(file_data)
                processed_files.append(file_data)
                
            except Exception as e:
                print(f"Error processing file {file.file_id}: {e}")
                continue
        
        return processed_files
    
    def extract_drama_name(self, files):
        """Extract drama name from filenames using common patterns"""
        if not files or not files[0].file_name:
            return "New Drama Post"
        
        try:
            filename = files[0].file_name
            
            # Common drama filename patterns
            patterns_to_remove = [
                r'[Ee]p?\d+',  # Episode numbers: Ep01, ep1, Episode1
                r'[Ss]\d+',    # Season numbers: S01, s1
                r'\.mkv$|\.mp4$|\.avi$|\.mov$',  # File extensions
                r'\[.*?\]',    # Bracketed text [1080p]
                r'\(.*?\)',    # Parentheses text (subbed)
                r'[_-]',       # Separators - and _
            ]
            
            import re
            drama_name = filename
            
            # Remove common patterns
            for pattern in patterns_to_remove:
                drama_name = re.sub(pattern, ' ', drama_name)
            
            # Clean up extra spaces and title case
            drama_name = ' '.join(drama_name.split()).title()
            
            return drama_name if drama_name.strip() else "New Drama Post"
            
        except Exception as e:
            print(f"Error extracting drama name: {e}")
            return "New Drama Post"
