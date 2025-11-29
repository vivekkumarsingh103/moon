import json
import os
from datetime import datetime
from config import WEBSITE_DATA_FILE

class WebsiteManager:
    def __init__(self):
        self.data_file = WEBSITE_DATA_FILE
        self.load_data()
    
    def load_data(self):
        """Load website data from JSON"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            logger.info(f"✅ Website data loaded from {self.data_file}")
        except FileNotFoundError:
            self.data = {
                "home_posts": [],
                "ongoing_dramas": [],
                "blog_posts": [],
                "all_posts": [],
                "search_data": []
            }
            self.save_data()
            logger.info(f"📁 Created new website data file: {self.data_file}")
        except Exception as e:
            logger.error(f"❌ Error loading website data: {e}")
            self.data = {
                "home_posts": [],
                "ongoing_dramas": [],
                "blog_posts": [],
                "all_posts": [],
                "search_data": []
            }
    
    def save_data(self):
        """Save data to JSON file"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            logger.info("💾 Website data saved successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Error saving website data: {e}")
            return False
    
    def add_to_section(self, section, post_data):
        """Add post to specific website section"""
        try:
            if section not in self.data:
                logger.error(f"❌ Invalid section: {section}")
                return False
            
            # Add timestamp if not present
            if 'timestamp' not in post_data:
                post_data['timestamp'] = datetime.now().isoformat()
            
            # Add to section
            self.data[section].insert(0, post_data)  # Add to beginning for latest first
            
            # Update search data
            self.update_search_data()
            
            # Save to file
            self.save_data()
            
            logger.info(f"✅ Added post to {section}: {post_data.get('title', 'Unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error adding to section {section}: {e}")
            return False
    
    def move_post(self, from_section, to_section, post_title):
        """Move post between sections (ongoing → all_posts)"""
        try:
            if from_section not in self.data or to_section not in self.data:
                logger.error(f"❌ Invalid sections: {from_section} -> {to_section}")
                return False
            
            # Find post in source section
            post_to_move = None
            post_index = -1
            
            for i, post in enumerate(self.data[from_section]):
                if post.get('title', '').lower() == post_title.lower():
                    post_to_move = post
                    post_index = i
                    break
            
            if not post_to_move:
                logger.error(f"❌ Post not found in {from_section}: {post_title}")
                return False
            
            # Remove from source section
            self.data[from_section].pop(post_index)
            
            # Update timestamp
            post_to_move['timestamp'] = datetime.now().isoformat()
            post_to_move['moved_from'] = from_section
            
            # Add to target section
            self.data[to_section].insert(0, post_to_move)
            
            # Update search data
            self.update_search_data()
            
            # Save to file
            self.save_data()
            
            logger.info(f"✅ Moved post from {from_section} to {to_section}: {post_title}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error moving post {post_title}: {e}")
            return False
    
    def update_search_data(self):
        """Update search data from ALL current content"""
        try:
            search_data = []
            
            # From ongoing dramas
            for drama in self.data["ongoing_dramas"]:
                search_data.append({
                    "title": drama.get("title", ""),
                    "type": "Drama",
                    "category": "ongoing",
                    "image": drama.get("image", ""),
                    "channel_link": drama.get("channel_link", ""),
                    "timestamp": drama.get("timestamp", "")
                })
            
            # From all posts
            for post in self.data["all_posts"]:
                search_data.append({
                    "title": post.get("title", ""),
                    "type": "Drama", 
                    "category": "all_posts",
                    "image": post.get("image", ""),
                    "channel_link": post.get("channel_link", ""),
                    "timestamp": post.get("timestamp", "")
                })
            
            # From blog posts
            for blog in self.data["blog_posts"]:
                search_data.append({
                    "title": blog.get("title", ""),
                    "type": "Article",
                    "category": "blog",
                    "image": blog.get("image", ""),
                    "preview": blog.get("preview", ""),
                    "timestamp": blog.get("timestamp", "")
                })
            
            # From home posts
            for post in self.data["home_posts"]:
                search_data.append({
                    "title": post.get("title", ""),
                    "type": "Drama",
                    "category": "home",
                    "image": post.get("image", ""),
                    "excerpt": post.get("excerpt", ""),
                    "timestamp": post.get("timestamp", "")
                })
            
            # Remove duplicates based on title
            unique_search_data = []
            seen_titles = set()
            
            for item in search_data:
                title = item.get("title", "").lower()
                if title and title not in seen_titles:
                    unique_search_data.append(item)
                    seen_titles.add(title)
            
            self.data["search_data"] = unique_search_data
            self.save_data()
            
            logger.info(f"✅ Search data updated: {len(unique_search_data)} items")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating search data: {e}")
            return False
    
    def get_drama_names(self):
        """Get all current drama names from website data"""
        try:
            drama_names = []
            
            # Extract from all drama sections
            for section in ["home_posts", "ongoing_dramas", "all_posts"]:
                for post in self.data.get(section, []):
                    title = post.get('title', '').lower().strip()
                    if title and title not in drama_names:
                        drama_names.append(title)
            
            logger.info(f"📊 Found {len(drama_names)} drama names")
            return drama_names
            
        except Exception as e:
            logger.error(f"❌ Error getting drama names: {e}")
            return []
    
    def search_content(self, query):
        """Search content across all sections"""
        try:
            query = query.lower().strip()
            results = []
            
            if not query:
                return results
            
            # Search in all sections
            for section in ["home_posts", "ongoing_dramas", "all_posts", "blog_posts"]:
                for item in self.data.get(section, []):
                    title = item.get('title', '').lower()
                    excerpt = item.get('excerpt', '').lower()
                    content = item.get('content', '').lower()
                    
                    if (query in title or 
                        query in excerpt or 
                        query in content):
                        results.append({
                            **item,
                            "category": section,
                            "match_score": self.calculate_match_score(query, title, excerpt, content)
                        })
            
            # Sort by match score (highest first)
            results.sort(key=lambda x: x.get('match_score', 0), reverse=True)
            
            logger.info(f"🔍 Search for '{query}': {len(results)} results")
            return results[:10]  # Return top 10 results
            
        except Exception as e:
            logger.error(f"❌ Error searching content: {e}")
            return []
    
    def calculate_match_score(self, query, title, excerpt, content):
        """Calculate how well the content matches the query"""
        score = 0
        
        # Title matches are most important
        if query in title:
            score += 10
        
        # Exact title match is even better
        if title == query:
            score += 5
        
        # Excerpt matches are moderately important
        if query in excerpt:
            score += 3
        
        # Content matches are least important
        if query in content:
            score += 1
        
        return score
    
    def get_section_stats(self):
        """Get statistics for each section"""
        try:
            stats = {}
            
            for section in ["home_posts", "ongoing_dramas", "blog_posts", "all_posts", "search_data"]:
                stats[section] = len(self.data.get(section, []))
            
            # Total dramas (excluding blogs)
            total_dramas = (stats["home_posts"] + 
                          stats["ongoing_dramas"] + 
                          stats["all_posts"])
            
            stats["total_dramas"] = total_dramas
            stats["last_updated"] = datetime.now().isoformat()
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Error getting section stats: {e}")
            return {}
    
    def cleanup_old_data(self, days_old=30):
        """Clean up data older than specified days (optional)"""
        try:
            cutoff_date = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
            cleaned_count = 0
            
            for section in ["home_posts", "ongoing_dramas", "blog_posts", "all_posts"]:
                original_count = len(self.data.get(section, []))
                
                # Filter out old posts
                self.data[section] = [
                    post for post in self.data.get(section, [])
                    if self.get_post_age(post) <= days_old
                ]
                
                cleaned_count += (original_count - len(self.data[section]))
            
            if cleaned_count > 0:
                self.update_search_data()
                self.save_data()
                logger.info(f"🧹 Cleaned up {cleaned_count} old posts")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"❌ Error cleaning up old data: {e}")
            return 0
    
    def get_post_age(self, post):
        """Calculate age of post in days"""
        try:
            timestamp = post.get('timestamp', '')
            if not timestamp:
                return 0
            
            # Parse timestamp
            if 'T' in timestamp:
                post_date = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            else:
                post_date = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
            
            current_date = datetime.now()
            age_days = (current_date - post_date).days
            
            return age_days
            
        except Exception as e:
            logger.error(f"❌ Error calculating post age: {e}")
            return 0
    
    def export_data(self, export_file="website_data_backup.json"):
        """Export website data to backup file"""
        try:
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 Data exported to {export_file}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error exporting data: {e}")
            return False
    
    def import_data(self, import_file="website_data_backup.json"):
        """Import website data from backup file"""
        try:
            with open(import_file, 'r', encoding='utf-8') as f:
                imported_data = json.load(f)
            
            self.data = imported_data
            self.save_data()
            
            logger.info(f"📥 Data imported from {import_file}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error importing data: {e}")
            return False

# Setup logging for this module
import logging
logger = logging.getLogger(__name__)

# Test the class
if __name__ == "__main__":
    print("🧪 Testing WebsiteManager...")
    
    manager = WebsiteManager()
    
    # Test stats
    stats = manager.get_section_stats()
    print(f"📊 Stats: {stats}")
    
    # Test drama names
    drama_names = manager.get_drama_names()
    print(f"🎬 Drama names: {drama_names}")
    
    # Test search data
    search_count = len(manager.data.get("search_data", []))
    print(f"🔍 Search items: {search_count}")
    
    print("✅ WebsiteManager test completed!")
