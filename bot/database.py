from pymongo import MongoClient
from config import MONGO_URI, DATABASE_NAME, POSTS_COLLECTION, FILES_COLLECTION, USERS_COLLECTION, BLOG_COLLECTION
from datetime import datetime

class Database:
    def __init__(self):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[DATABASE_NAME]
        self.posts = self.db[POSTS_COLLECTION]
        self.files = self.db[FILES_COLLECTION]
        self.users = self.db[USERS_COLLECTION]
        self.blogs = self.db[BLOG_COLLECTION]
    
    # File Operations
    def insert_file(self, file_data):
        file_data['created_at'] = datetime.now()
        return self.files.insert_one(file_data)
    
    def get_files_by_channel(self, channel_link):
        return list(self.files.find({"channel_link": channel_link}))
    
    def get_all_files(self):
        return list(self.files.find({}))
    
    # Post Operations
    def insert_post(self, post_data):
        post_data['created_at'] = datetime.now()
        return self.posts.insert_one(post_data)
    
    def get_post_by_title(self, title):
        return self.posts.find_one({"title": title})
    
    def get_posts_by_section(self, section):
        return list(self.posts.find({"section": section}).sort("created_at", -1))
    
    def update_post_section(self, post_title, new_section):
        return self.posts.update_one(
            {"title": post_title},
            {"$set": {"section": new_section, "updated_at": datetime.now()}}
        )
    
    def get_all_posts(self):
        return list(self.posts.find({}).sort("created_at", -1))
    
    # User Operations (for broadcast)
    def add_user(self, user_data):
        user_data['joined_at'] = datetime.now()
        return self.users.update_one(
            {"user_id": user_data['user_id']},
            {"$set": user_data},
            upsert=True
        )
    
    def get_all_users(self):
        return list(self.users.find({}))
    
    def get_user_count(self):
        return self.users.count_documents({})
    
    # Blog Operations
    def insert_blog(self, blog_data):
        blog_data['created_at'] = datetime.now()
        return self.blogs.insert_one(blog_data)
    
    def get_all_blogs(self):
        return list(self.blogs.find({}).sort("created_at", -1))
    
    def get_recent_blogs(self, limit=10):
        return list(self.blogs.find({}).sort("created_at", -1).limit(limit))
    
    # Statistics
    def get_stats(self):
        return {
            "total_posts": self.posts.count_documents({}),
            "ongoing_posts": self.posts.count_documents({"section": "ongoing"}),
            "all_posts": self.posts.count_documents({"section": "all_posts"}),
            "total_files": self.files.count_documents({}),
            "total_users": self.get_user_count(),
            "total_blogs": self.blogs.count_documents({})
        }
