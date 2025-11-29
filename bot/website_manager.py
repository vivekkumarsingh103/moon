def update_search_data(self):
    """Update search data from ALL current content"""
    search_data = []
    
    # From ongoing dramas
    for drama in self.data["ongoing_dramas"]:
        search_data.append({
            "title": drama.get("title", ""),
            "type": "Drama",
            "category": "ongoing"
        })
    
    # From all posts
    for post in self.data["all_posts"]:
        search_data.append({
            "title": post.get("title", ""),
            "type": "Drama", 
            "category": "all_posts"
        })
    
    # From blog posts
    for blog in self.data["blog_posts"]:
        search_data.append({
            "title": blog.get("title", ""),
            "type": "Article",
            "category": "blog"
        })
    
    # From home posts
    for post in self.data["home_posts"]:
        search_data.append({
            "title": post.get("title", ""),
            "type": "Drama",
            "category": "home"
        })
    
    self.data["search_data"] = search_data
    self.save_data()
