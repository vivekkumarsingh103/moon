import os
import logging

# =============================================
# 🔐 SECURE CONFIGURATION - SAFE FOR PUBLIC REPO
# =============================================

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# =============================================
# 🤖 BOT CONFIGURATION
# =============================================
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN environment variable is not set")
    raise ValueError(
        "BOT_TOKEN environment variable is required.\n"
        "Get it from @BotFather and set it as environment variable."
    )

# =============================================
# 🗄️ DATABASE CONFIGURATION
# =============================================
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    logger.error("❌ MONGO_URI environment variable is not set")
    raise ValueError(
        "MONGO_URI environment variable is required.\n"
        "Set your MongoDB connection string."
    )

DATABASE_NAME = "dramawallah_bot"
POSTS_COLLECTION = "posts"
FILES_COLLECTION = "files"
USERS_COLLECTION = "users"
BLOG_COLLECTION = "blogs"

# =============================================
# 👑 ADMIN CONFIGURATION
# =============================================
admin_ids_str = os.getenv("ADMIN_IDS", "")
if not admin_ids_str:
    logger.error("❌ ADMIN_IDS environment variable is not set")
    raise ValueError(
        "ADMIN_IDS environment variable is required.\n"
        "Set your Telegram user ID(s).\n"
        "Example: ADMIN_IDS=123456789 or ADMIN_IDS=123456789,987654321"
    )

try:
    ADMIN_IDS = [int(id.strip()) for id in admin_ids_str.split(",") if id.strip()]
    if not ADMIN_IDS:
        raise ValueError("No valid admin IDs found")
except ValueError as e:
    logger.error(f"❌ Invalid ADMIN_IDS format: {e}")
    raise ValueError(
        "ADMIN_IDS must be comma-separated numbers.\n"
        "Example: ADMIN_IDS=123456789,987654321"
    )

# =============================================
# 🌐 WEBSITE CONFIGURATION - UPDATED URL
# =============================================
WEBSITE_DATA_FILE = "website_data.json"
WEBSITE_URL = "https://dramawallah.vercel.app"  # 🆕 UPDATED URL

# Website section URLs for search results
SECTION_URLS = {
    "home": f"{WEBSITE_URL}/#home",
    "ongoing": f"{WEBSITE_URL}/#ongoing", 
    "blog": f"{WEBSITE_URL}/#blog",
    "all_posts": f"{WEBSITE_URL}/#bot-posts"
}

# =============================================
# 🔍 SMART SEARCH CONFIGURATION
# =============================================
# General search triggers
SEARCH_TRIGGERS = [
    'kdrama', 'k-drama', 'drama', 'episode', 'season', 
    'latest episode', 'new episode', 'download', 'watch',
    'where can i', 'anyone seen', 'recommend', 'suggest',
    'anyone watch', 'looking for', 'where to watch',
    'best drama', 'good drama', 'new drama'
]

# =============================================
# 📁 FILE HANDLING CONFIGURATION
# =============================================
MAX_FILES_PER_UPLOAD = 100
MAX_FILE_SIZE_MB = 2000

# Supported file types
SUPPORTED_FILE_TYPES = [
    'video/mp4', 'video/mkv', 'video/avi', 'video/mov', 'video/x-matroska',
    'application/zip', 'application/x-rar-compressed', 'application/x-7z-compressed'
]

# =============================================
# ⚙️ BOT BEHAVIOR CONFIGURATION
# =============================================
ENABLE_GROUP_SEARCH = True
MAX_SEARCH_RESULTS = 3

# =============================================
# 🔗 URL SHORTENER CONFIGURATION
# =============================================
OUO_API_KEY = "tmqxi7by"
URL_SHORTENER_ENABLED = True

def validate_config():
    """Validate that all required configuration is present and valid"""
    errors = []
    
    if not BOT_TOKEN:
        errors.append("BOT_TOKEN is not set")
    
    if not MONGO_URI:
        errors.append("MONGO_URI is not set")
    
    if not ADMIN_IDS:
        errors.append("ADMIN_IDS is not set or invalid")
    
    if errors:
        error_msg = "❌ Configuration validation failed:\n" + "\n".join(f"• {error}" for error in errors)
        logger.error(error_msg)
        return False
    
    logger.info("✅ Configuration validated successfully")
    return True

# Auto-validate when imported
if __name__ != "__main__":
    validate_config()
