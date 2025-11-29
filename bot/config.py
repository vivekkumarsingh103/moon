import os
import logging

# =============================================
# 🔐 SECURE CONFIGURATION - SAFE FOR PUBLIC REPO
# =============================================
# All sensitive data comes from environment variables
# NEVER hardcode credentials in this file!
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
# 🌐 WEBSITE CONFIGURATION
# =============================================
WEBSITE_DATA_FILE = "data.json"
WEBSITE_URL = "https://dramawallah.netlify.app"

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
# Drama names are automatically extracted from website posts
# No need to hardcode them!

# General search triggers (these stay constant)
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
MAX_FILE_SIZE_MB = 2000  # 2GB max file size

# Supported file types for drama uploads
SUPPORTED_FILE_TYPES = [
    'video/mp4', 'video/mkv', 'video/avi', 'video/mov', 'video/x-matroska',
    'application/zip', 'application/x-rar-compressed', 'application/x-7z-compressed',
    'application/x-zip-compressed'
]

# File type extensions for validation
SUPPORTED_EXTENSIONS = [
    '.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv',
    '.zip', '.rar', '.7z'
]

# =============================================
# ⚙️ BOT BEHAVIOR CONFIGURATION
# =============================================
# Group search settings
ENABLE_GROUP_SEARCH = True
MAX_SEARCH_RESULTS = 3
SEARCH_COOLDOWN_SECONDS = 30  # Prevent spam in groups

# Broadcast settings
BROADCAST_BATCH_SIZE = 30  # Users per batch to avoid rate limits
BROADCAST_DELAY_SECONDS = 1  # Delay between batches

# Conversation timeouts (in seconds)
CONVERSATION_TIMEOUT = 300  # 5 minutes

# =============================================
# 🔗 URL SHORTENER CONFIGURATION
# =============================================
OUO_API_KEY = "tmqxi7by"  # This is public from your example
URL_SHORTENER_ENABLED = True

# =============================================
# 🎯 LOGGING CONFIGURATION
# =============================================
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# =============================================
# 🔧 VALIDATION & UTILITIES
# =============================================
def validate_config():
    """Validate that all required configuration is present and valid"""
    errors = []
    
    # Check required environment variables
    if not BOT_TOKEN:
        errors.append("BOT_TOKEN is not set")
    elif not BOT_TOKEN.startswith('') and ':' not in BOT_TOKEN:
        errors.append("BOT_TOKEN appears to be invalid")
    
    if not MONGO_URI:
        errors.append("MONGO_URI is not set")
    elif not MONGO_URI.startswith(('mongodb://', 'mongodb+srv://')):
        errors.append("MONGO_URI appears to be invalid")
    
    if not ADMIN_IDS:
        errors.append("ADMIN_IDS is not set or invalid")
    
    # Check website data file accessibility
    try:
        with open(WEBSITE_DATA_FILE, 'a') as f:
            pass
    except Exception as e:
        errors.append(f"Cannot access website data file: {e}")
    
    if errors:
        error_msg = "❌ Configuration validation failed:\n" + "\n".join(f"• {error}" for error in errors)
        logger.error(error_msg)
        return False
    
    logger.info("✅ Configuration validated successfully")
    return True

def get_config_summary():
    """Get a safe configuration summary (without sensitive data)"""
    return {
        "database_name": DATABASE_NAME,
        "admin_count": len(ADMIN_IDS),
        "website_url": WEBSITE_URL,
        "max_files_per_upload": MAX_FILES_PER_UPLOAD,
        "search_triggers_count": len(SEARCH_TRIGGERS),
        "supported_file_types_count": len(SUPPORTED_FILE_TYPES),
        "group_search_enabled": ENABLE_GROUP_SEARCH
    }

# Auto-validate when imported
if __name__ != "__main__":
    validate_config()

# =============================================
# 🧪 TEST FUNCTION
# =============================================
if __name__ == "__main__":
    print("🧪 Testing Configuration...")
    print("=" * 50)
    
    try:
        if validate_config():
            print("✅ Configuration is valid!")
            
            summary = get_config_summary()
            print("\n📊 Configuration Summary:")
            for key, value in summary.items():
                print(f"  {key.replace('_', ' ').title()}: {value}")
            
            print(f"\n🤖 Bot Token: {'*' * 20}{BOT_TOKEN[-5:] if BOT_TOKEN else 'NOT SET'}")
            print(f"🗄️  MongoDB: {'Configured' if MONGO_URI else 'NOT SET'}")
            print(f"👑 Admins: {ADMIN_IDS}")
            print(f"🌐 Website: {WEBSITE_URL}")
            print(f"📁 Data File: {WEBSITE_DATA_FILE}")
            
        else:
            print("❌ Configuration validation failed!")
            print("\n💡 Setup Instructions:")
            print("1. For local development:")
            print("   export BOT_TOKEN='your_bot_token_here'")
            print("   export MONGO_URI='your_mongodb_uri_here'")
            print("   export ADMIN_IDS='your_telegram_id_here'")
            print("2. For Koyeb: Set as environment variables in dashboard")
            print("3. Get BOT_TOKEN from @BotFather on Telegram")
            
    except Exception as e:
        print(f"💥 Configuration test failed: {e}")
        print("\n🔧 Please check your environment variables:")
        print(f"   BOT_TOKEN: {'Set' if os.getenv('BOT_TOKEN') else 'NOT SET'}")
        print(f"   MONGO_URI: {'Set' if os.getenv('MONGO_URI') else 'NOT SET'}")
        print(f"   ADMIN_IDS: {'Set' if os.getenv('ADMIN_IDS') else 'NOT SET'}")
