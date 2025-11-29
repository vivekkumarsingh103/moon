import json
import requests

class WebsiteManager:
    def __init__(self):
        self.data_file = "website_data.json"
        self.load_data()
    
    def load_data(self):
        """Load website data from JSON"""
        try:
            with open(self.data_file, 'r') as f:
                self.data = json.load(f)
        except FileNotFoundError:
            self.data = {
                "home_posts": [],
                "ongoing_dramas": [],
                "blog_posts": [],
                "all_posts": [],
                "search_data": []
            }
            self.save_data()
    
    def save_data(self):
        """Save data to JSON file"""
        with open(self.data_file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def add_to_section(self, section, post_data):
        """Add post to specific website section"""
        if section in self.data:
            self.data[section].append(post_data)
            self.update_search_data()
            self.save_data()
            return True
        return False
    
    def move_post(self, from_section, to_section, post_title):
        """Move post between sections (ongoing → all_posts)"""
        # Implementation for moving posts
        pass
    
    def update_search_data(self):
        """Update search data from all sections"""
        search_data = []
        
        # Add ongoing dramas to search
        for drama in self.data["ongoing_dramas"]:
            search_data.append({
                "title": drama.get("title", ""),
                "type": "Drama",
                "category": "ongoing"
            })
        
        # Add blog posts to search
        for blog in self.data["blog_posts"]:
            search_data.append({
                "title": blog.get("title", ""),
                "type": "Article", 
                "category": "blog"
            })
        
        self.data["search_data"] = search_data
