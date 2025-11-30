from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler
from datetime import datetime
import os
import logging
import signal
import sys
import asyncio
from config import BOT_TOKEN, ADMIN_IDS, SEARCH_TRIGGERS, WEBSITE_URL
from database import Database
from file_handler import FileHandler
from website_manager import WebsiteManager

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
(
    CHANNEL_LINK, IMAGE, FILES, 
    ONGOING_CHOICE, ONGOING_CHANNEL, ONGOING_FILES, ONGOING_COMPLETION,
    BLOG_IMAGE, BLOG_TEXT, BLOG_MORE_TEXT,
    BROADCAST_MESSAGE
) = range(11)

class DramawallahBot:
    def __init__(self):
        self.db = Database()
        self.file_handler = FileHandler()
        self.website = WebsiteManager()
        self.application = Application.builder().token(BOT_TOKEN).build()
        
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup all command and message handlers"""
        # /addpost conversation
        addpost_conv = ConversationHandler(
            entry_points=[CommandHandler('addpost', self.start_addpost)],
            states={
                CHANNEL_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_channel_link)],
                IMAGE: [MessageHandler(filters.PHOTO, self.get_image)],
                FILES: [
                    MessageHandler(filters.Document.ALL, self.get_files),
                    CallbackQueryHandler(self.handle_file_decision, pattern="^(more_files|finish_files)$")
                ],
            },
            fallbacks=[CommandHandler('cancel', self.cancel)]
        )
        
        # /ongoing conversation
        ongoing_conv = ConversationHandler(
            entry_points=[CommandHandler('ongoing', self.start_ongoing)],
            states={
                ONGOING_CHOICE: [CallbackQueryHandler(self.handle_ongoing_choice, pattern="^(add_ongoing|edit_ongoing)$")],
                ONGOING_CHANNEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_ongoing_channel)],
                ONGOING_FILES: [
                    MessageHandler(filters.Document.ALL, self.get_ongoing_files),
                    CallbackQueryHandler(self.handle_ongoing_files_decision, pattern="^(more_ongoing_files|finish_ongoing_files)$")
                ],
                ONGOING_COMPLETION: [CallbackQueryHandler(self.handle_ongoing_completion, pattern="^(yes_complete|no_complete)$")]
            },
            fallbacks=[CommandHandler('cancel', self.cancel)]
        )
        
        # /blog conversation
        blog_conv = ConversationHandler(
            entry_points=[CommandHandler('blog', self.start_blog)],
            states={
                BLOG_IMAGE: [MessageHandler(filters.PHOTO, self.get_blog_image)],
                BLOG_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_blog_text)],
                BLOG_MORE_TEXT: [CallbackQueryHandler(self.handle_blog_more_text, pattern="^(add_more_text|finish_blog)$")]
            },
            fallbacks=[CommandHandler('cancel', self.cancel)]
        )
        
        # /broadcast conversation
        broadcast_conv = ConversationHandler(
            entry_points=[CommandHandler('broadcast', self.start_broadcast)],
            states={
                BROADCAST_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.send_broadcast)]
            },
            fallbacks=[CommandHandler('cancel', self.cancel)]
        )
        
        # Add all handlers
        self.application.add_handler(addpost_conv)
        self.application.add_handler(ongoing_conv)
        self.application.add_handler(blog_conv)
        self.application.add_handler(broadcast_conv)
        self.application.add_handler(CommandHandler("search", self.search))
        self.application.add_handler(CommandHandler("info", self.info))
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help))
        
        # Message handler for group search and user registration
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_message))
        
        # Error handler
        self.application.add_error_handler(self.error_handler)
    
    # ==================== START & UTILITY FUNCTIONS ====================
    async def start(self, update: Update, context: CallbackContext):
        """Handle /start command"""
        user = update.effective_user
        user_data = {
            "user_id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name
        }
        self.db.add_user(user_data)
        
        welcome_text = (
            f"👋 Welcome {user.first_name} to **Dramawallah Bot**! 🎬\n\n"
            "**Available Commands:**\n"
            "• /addpost - Add new drama post with files\n"
            "• /ongoing - Manage ongoing dramas\n"
            "• /blog - Create blog posts\n"
            "• /search - Search for content\n"
            "• /info - Get bot statistics\n"
            "• /broadcast - Broadcast message (Admins)\n"
            "• /help - Show this help message\n\n"
            f"**🌐 Website:** {WEBSITE_URL}"
        )
        
        await update.message.reply_text(welcome_text)
    
    async def help(self, update: Update, context: CallbackContext):
        """Handle /help command"""
        help_text = (
            "🤖 **Dramawallah Bot Help**\n\n"
            "**Admin Commands:**\n"
            "• /addpost - Add new drama with files\n"
            "• /ongoing - Manage ongoing dramas\n"
            "• /blog - Create blog posts\n"
            "• /broadcast - Send message to all users\n"
            "• /info - View bot statistics\n\n"
            "**User Commands:**\n"
            "• /search - Search for dramas\n"
            "• /start - Welcome message\n\n"
            f"**Visit our website:** {WEBSITE_URL}"
        )
        await update.message.reply_text(help_text)
    
    async def cancel(self, update: Update, context: CallbackContext):
        """Cancel any conversation"""
        context.user_data.clear()
        await update.message.reply_text("❌ Operation cancelled.")
        return ConversationHandler.END
    
    async def error_handler(self, update: Update, context: CallbackContext):
        """Handle errors in the bot"""
        logger.error(f"Update {update} caused error {context.error}")
        
        try:
            if update and update.effective_message:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="❌ An error occurred. Please try again later."
                )
        except Exception as e:
            logger.error(f"Error in error handler: {e}")
    
    def is_admin(self, user_id):
        """Check if user is admin"""
        return user_id in ADMIN_IDS
    
    def get_current_drama_names(self):
        """Get current drama names from website data (always fresh)"""
        try:
            # Method 1: From website JSON (most current)
            website_data = self.website.data
            drama_names = []
            
            # Extract from all posts
            for section in ["home_posts", "ongoing_dramas", "all_posts"]:
                for post in website_data.get(section, []):
                    title = post.get('title', '').lower()
                    if title and title not in drama_names:
                        drama_names.append(title)
            
            # Method 2: From database (fallback)
            if not drama_names:
                posts = self.db.get_all_posts()
                drama_names = [post.get('title', '').lower() for post in posts if post.get('title')]
            
            return drama_names
            
        except Exception as e:
            logger.error(f"Error getting drama names: {e}")
            return []
    
    # ==================== /addpost FUNCTION ====================
    async def start_addpost(self, update: Update, context: CallbackContext):
        """Start /addpost conversation"""
        try:
            if not self.is_admin(update.effective_user.id):
                await update.message.reply_text("❌ This command is for admins only.")
                return ConversationHandler.END
                
            await update.message.reply_text(
                "📺 **Add New Kdrama Post**\n\n"
                "Send me the private channel link where files should be posted:"
            )
            return CHANNEL_LINK
        except Exception as e:
            logger.error(f"Error in start_addpost: {e}")
            await update.message.reply_text("❌ Error starting post creation. Please try again.")
            return ConversationHandler.END
    
    async def get_channel_link(self, update: Update, context: CallbackContext):
        """Store channel link and ask for image"""
        try:
            channel_link = update.message.text.strip()
            
            # Basic validation
            if not channel_link.startswith('@') and not 't.me/' in channel_link:
                await update.message.reply_text("❌ Please provide a valid channel link (e.g., @channel_name or t.me/...)")
                return CHANNEL_LINK
            
            context.user_data['channel_link'] = channel_link
            await update.message.reply_text("✅ Channel saved! Now send the image for website post:")
            return IMAGE
            
        except Exception as e:
            logger.error(f"Error in get_channel_link: {e}")
            await update.message.reply_text("❌ Error processing channel link. Please try again.")
            return ConversationHandler.END
    
    async def get_image(self, update: Update, context: CallbackContext):
        """Store image and ask for files"""
        try:
            # Get the highest quality photo
            photo_file = await update.message.photo[-1].get_file()
            context.user_data['image_file_id'] = photo_file.file_id
            context.user_data['image_path'] = photo_file.file_path
            
            await update.message.reply_text(
                "🖼️ Image saved! Now send all the episode files.\n\n"
                "You can send multiple files at once or one by one.\n"
                "When finished, click 'Finish & Create Post'"
            )
            
            # Initialize files list
            context.user_data['files'] = []
            
            return FILES
            
        except Exception as e:
            logger.error(f"Error in get_image: {e}")
            await update.message.reply_text("❌ Error processing image. Please try again.")
            return ConversationHandler.END
    
    async def get_files(self, update: Update, context: CallbackContext):
        """Process files with bulk support"""
        try:
            # Add current file to list
            if update.message.document:
                context.user_data['files'].append(update.message.document)
                file_count = len(context.user_data['files'])
                
                # Create inline keyboard
                keyboard = [
                    [InlineKeyboardButton("➕ Send More Files", callback_data="more_files")],
                    [InlineKeyboardButton("✅ Finish & Create Post", callback_data="finish_files")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    f"📁 Files received: {file_count}\n"
                    "Send more files or click finish to create post:",
                    reply_markup=reply_markup
                )
            else:
                await update.message.reply_text("❌ Please send valid files (documents/videos)")
            
            return FILES
            
        except Exception as e:
            logger.error(f"Error in get_files: {e}")
            await update.message.reply_text("❌ Error processing files. Please try again.")
            return FILES
    
    async def handle_file_decision(self, update: Update, context: CallbackContext):
        """Handle user decision to send more files or finish"""
        try:
            query = update.callback_query
            await query.answer()
            
            if query.data == "more_files":
                await query.edit_message_text("📤 Send more files...")
                return FILES
            else:
                # Finalize the post creation
                await query.edit_message_text("🚀 Processing files and creating post...")
                return await self.finalize_post(update, context)
                
        except Exception as e:
            logger.error(f"Error in handle_file_decision: {e}")
            await query.edit_message_text("❌ Error processing request. Please try /addpost again.")
            return ConversationHandler.END
    
    async def finalize_post(self, update: Update, context: CallbackContext):
        """Finalize the post creation process"""
        try:
            # Get data from context
            channel_link = context.user_data.get('channel_link')
            image_file_id = context.user_data.get('image_file_id')
            files = context.user_data.get('files', [])
            
            if not files:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="❌ No files received. Please start over with /addpost"
                )
                return ConversationHandler.END
            
            # Process files
            processed_files = self.file_handler.process_files(files, channel_link)
            
            if not processed_files:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="❌ Failed to process files. Please try again."
                )
                return ConversationHandler.END
            
            # Post files to channel
            await self.post_to_channel(processed_files, channel_link)
            
            # Create website post
            drama_name = self.file_handler.extract_drama_name(files)
            post_data = {
                "title": drama_name,
                "image": context.user_data.get('image_path'),
                "channel_link": channel_link,
                "files_count": len(processed_files),
                "file_names": [f["file_name"] for f in processed_files],
                "timestamp": datetime.now().isoformat(),
                "section": "all_posts"
            }
            
            # Add to website
            self.website.add_to_section("all_posts", post_data)
            
            # Save to database
            self.db.insert_post(post_data)
            
            # Update search data with new drama
            self.website.update_search_data()
            
            # Success message
            success_text = (
                f"✅ **Post Created Successfully!** 🎬\n\n"
                f"**📺 Drama:** {drama_name}\n"
                f"**📁 Files Uploaded:** {len(processed_files)}\n"
                f"**📢 Channel:** {channel_link}\n"
                f"**🌐 Website:** Added to 'All Posts' section\n\n"
                f"All files have been posted to the channel with download links."
            )
            
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=success_text
            )
            
            # Cleanup
            context.user_data.clear()
            
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"Error in finalize_post: {e}")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"❌ Error creating post: {str(e)}\nPlease try /addpost again."
            )
            return ConversationHandler.END
    
    # ==================== /ongoing FUNCTION ====================
    async def start_ongoing(self, update: Update, context: CallbackContext):
        """Start /ongoing command"""
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ This command is for admins only.")
            return ConversationHandler.END
            
        keyboard = [
            [InlineKeyboardButton("➕ Add New Ongoing", callback_data="add_ongoing")],
            [InlineKeyboardButton("✏️ Edit Existing", callback_data="edit_ongoing")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "📺 **Ongoing Dramas Management**\n\n"
            "Choose an option:",
            reply_markup=reply_markup
        )
        return ONGOING_CHOICE
    
    async def handle_ongoing_choice(self, update: Update, context: CallbackContext):
        """Handle ongoing add/edit choice"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "add_ongoing":
            await query.edit_message_text("📺 Let's add a new ongoing drama!\n\nSend me the channel link:")
            context.user_data['ongoing_action'] = 'add'
            return ONGOING_CHANNEL
        else:
            await query.edit_message_text("✏️ Send the channel link of the ongoing drama you want to edit:")
            context.user_data['ongoing_action'] = 'edit'
            return ONGOING_CHANNEL
    
    async def get_ongoing_channel(self, update: Update, context: CallbackContext):
        """Get channel link for ongoing drama"""
        try:
            channel_link = update.message.text.strip()
            context.user_data['channel_link'] = channel_link
            
            if context.user_data['ongoing_action'] == 'add':
                await update.message.reply_text("✅ Channel saved! Now send the image for website post:")
                return IMAGE  # Reuse the same IMAGE state from addpost
            else:
                await update.message.reply_text("✅ Channel found! Now send the new files to add:")
                context.user_data['files'] = []
                return ONGOING_FILES
                
        except Exception as e:
            logger.error(f"Error in get_ongoing_channel: {e}")
            await update.message.reply_text("❌ Error processing channel link. Please try again.")
            return ConversationHandler.END
    
    async def get_ongoing_files(self, update: Update, context: CallbackContext):
        """Process files for ongoing edit"""
        try:
            if update.message.document:
                context.user_data['files'].append(update.message.document)
                file_count = len(context.user_data['files'])
                
                keyboard = [
                    [InlineKeyboardButton("➕ Send More Files", callback_data="more_ongoing_files")],
                    [InlineKeyboardButton("✅ Finish Adding Files", callback_data="finish_ongoing_files")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    f"📁 Files received: {file_count}\nSend more or finish:",
                    reply_markup=reply_markup
                )
            
            return ONGOING_FILES
            
        except Exception as e:
            logger.error(f"Error in get_ongoing_files: {e}")
            await update.message.reply_text("❌ Error processing files. Please try again.")
            return ONGOING_FILES
    
    async def handle_ongoing_files_decision(self, update: Update, context: CallbackContext):
        """Handle ongoing files decision"""
        try:
            query = update.callback_query
            await query.answer()
            
            if query.data == "more_ongoing_files":
                await query.edit_message_text("📤 Send more files...")
                return ONGOING_FILES
            else:
                # Process the files for ongoing drama
                channel_link = context.user_data['channel_link']
                files = context.user_data['files']
                
                if files:
                    processed_files = self.file_handler.process_files(files, channel_link)
                    await self.post_to_channel(processed_files, channel_link)
                    
                    await query.edit_message_text(
                        f"✅ Added {len(processed_files)} files to {channel_link}\n\n"
                        "Is this drama completed?",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("✅ Yes, Move to All Posts", callback_data="yes_complete")],
                            [InlineKeyboardButton("❌ No, Keep in Ongoing", callback_data="no_complete")]
                        ])
                    )
                    return ONGOING_COMPLETION
                else:
                    await query.edit_message_text("❌ No files received. Use /ongoing to try again.")
                    return ConversationHandler.END
                    
        except Exception as e:
            logger.error(f"Error in handle_ongoing_files_decision: {e}")
            await query.edit_message_text("❌ Error processing files. Please try again.")
            return ConversationHandler.END
    
    async def handle_ongoing_completion(self, update: Update, context: CallbackContext):
        """Handle ongoing completion decision"""
        try:
            query = update.callback_query
            await query.answer()
            
            channel_link = context.user_data['channel_link']
            files = context.user_data.get('files', [])
            
            if query.data == "yes_complete":
                # Move from ongoing to all_posts
                drama_name = self.file_handler.extract_drama_name(files)
                
                # Update in database
                self.db.update_post_section(drama_name, "all_posts")
                
                # Update website JSON
                self.website.move_post("ongoing_dramas", "all_posts", drama_name)
                
                # Update search data
                self.website.update_search_data()
                
                await query.edit_message_text(
                    f"✅ **{drama_name}** moved from Ongoing to All Posts!\n"
                    f"The drama is now marked as completed."
                )
            else:
                await query.edit_message_text(
                    f"✅ Files added to {channel_link}\n"
                    f"The drama remains in Ongoing section."
                )
            
            context.user_data.clear()
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"Error in handle_ongoing_completion: {e}")
            await query.edit_message_text("❌ Error updating drama status. Please try again.")
            return ConversationHandler.END
    
    # ==================== /blog FUNCTION ====================
    async def start_blog(self, update: Update, context: CallbackContext):
        """Start blog creation"""
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ This command is for admins only.")
            return ConversationHandler.END
            
        await update.message.reply_text("📝 **Create New Blog Post**\n\nSend the blog image:")
        context.user_data['blog_text'] = ""  # Initialize blog text
        return BLOG_IMAGE
    
    async def get_blog_image(self, update: Update, context: CallbackContext):
        """Get blog image"""
        try:
            photo_file = await update.message.photo[-1].get_file()
            context.user_data['blog_image'] = photo_file.file_path
            context.user_data['blog_image_id'] = photo_file.file_id
            
            await update.message.reply_text("🖼️ Image saved! Now send the blog text/content:")
            return BLOG_TEXT
            
        except Exception as e:
            logger.error(f"Error in get_blog_image: {e}")
            await update.message.reply_text("❌ Error processing image. Please try again.")
            return ConversationHandler.END
    
    async def get_blog_text(self, update: Update, context: CallbackContext):
        """Get blog text and ask if user wants to add more"""
        try:
            new_text = update.message.text
            context.user_data['blog_text'] += new_text + "\n\n"
            
            keyboard = [
                [InlineKeyboardButton("➕ Add More Text", callback_data="add_more_text")],
                [InlineKeyboardButton("✅ Finish & Publish", callback_data="finish_blog")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            text_preview = context.user_data['blog_text'][:100] + "..." if len(context.user_data['blog_text']) > 100 else context.user_data['blog_text']
            
            await update.message.reply_text(
                f"📝 Current content preview:\n\n{text_preview}\n\n"
                "Do you want to add more text or publish now?",
                reply_markup=reply_markup
            )
            
            return BLOG_MORE_TEXT
            
        except Exception as e:
            logger.error(f"Error in get_blog_text: {e}")
            await update.message.reply_text("❌ Error processing text. Please try again.")
            return BLOG_MORE_TEXT
    
    async def handle_blog_more_text(self, update: Update, context: CallbackContext):
        """Handle blog text addition decision"""
        try:
            query = update.callback_query
            await query.answer()
            
            if query.data == "add_more_text":
                await query.edit_message_text("📝 Send more text:")
                return BLOG_TEXT
            else:
                # Finalize and publish blog
                blog_title = context.user_data['blog_text'].split('\n')[0][:100]  # First line as title
                blog_data = {
                    "title": blog_title,
                    "content": context.user_data['blog_text'],
                    "image": context.user_data['blog_image'],
                    "timestamp": datetime.now().isoformat(),
                    "preview": context.user_data['blog_text'][:200] + "..." if len(context.user_data['blog_text']) > 200 else context.user_data['blog_text']
                }
                
                # Save to database
                self.db.insert_blog(blog_data)
                
                # Update website
                self.website.add_to_section("blog_posts", blog_data)
                
                # Update search data
                self.website.update_search_data()
                
                await query.edit_message_text(
                    f"✅ **Blog Published Successfully!**\n\n"
                    f"**Title:** {blog_data['title']}\n"
                    f"**Length:** {len(context.user_data['blog_text'])} characters\n"
                    f"**Added to:** Website Blog Section"
                )
                
                context.user_data.clear()
                return ConversationHandler.END
                
        except Exception as e:
            logger.error(f"Error in handle_blog_more_text: {e}")
            await query.edit_message_text("❌ Error publishing blog. Please try again.")
            return ConversationHandler.END
    
    # ==================== /broadcast FUNCTION ====================
    async def start_broadcast(self, update: Update, context: CallbackContext):
        """Start broadcast command"""
        user_id = update.effective_user.id
        if not self.is_admin(user_id):
            await update.message.reply_text("❌ This command is for admins only.")
            return ConversationHandler.END
        
        await update.message.reply_text(
            "📢 **Broadcast Message**\n\n"
            "Send the message you want to broadcast to all users:"
        )
        return BROADCAST_MESSAGE
    
    async def send_broadcast(self, update: Update, context: CallbackContext):
        """Send broadcast to all users"""
        try:
            message = update.message.text
            users = self.db.get_all_users()
            
            if not users:
                await update.message.reply_text("❌ No users found to broadcast to.")
                return ConversationHandler.END
            
            success_count = 0
            fail_count = 0
            
            await update.message.reply_text(f"📤 Broadcasting to {len(users)} users...")
            
            for user in users:
                try:
                    await context.bot.send_message(
                        chat_id=user['user_id'],
                        text=f"📢 **Announcement from Dramawallah**\n\n{message}"
                    )
                    success_count += 1
                except Exception as e:
                    logger.error(f"Failed to send to user {user['user_id']}: {e}")
                    fail_count += 1
            
            await update.message.reply_text(
                f"✅ **Broadcast Complete**\n\n"
                f"✅ Successful: {success_count}\n"
                f"❌ Failed: {fail_count}\n"
                f"📊 Total: {len(users)} users"
            )
            
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"Error in send_broadcast: {e}")
            await update.message.reply_text("❌ Error sending broadcast. Please try again.")
            return ConversationHandler.END
    
    # ==================== /search FUNCTION ====================
    async def search(self, update: Update, context: CallbackContext):
        """Handle /search command in private chat"""
        if update.effective_chat.type != "private":
            await update.message.reply_text("🔍 Please use search in private chat with the bot.")
            return
        
        keyboard = [
            [InlineKeyboardButton("🔍 Search on Website", url=f"{WEBSITE_URL}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🔍 **Search Dramas**\n\n"
            f"Click the button below to search on our website:",
            reply_markup=reply_markup
        )
    
    # ==================== /info FUNCTION ====================
    async def info(self, update: Update, context: CallbackContext):
        """Handle /info command"""
        try:
            stats = self.db.get_stats()
            ongoing_posts = self.db.get_posts_by_section("ongoing")
            all_posts = self.db.get_posts_by_section("all_posts")
            
            # Format ongoing posts
            ongoing_list = ""
            for i, post in enumerate(ongoing_posts[:10], 1):
                title = post.get('title', 'Unknown Title')
                ongoing_list += f"{i}. {title}\n"
            
            # Format all posts
            all_posts_list = ""
            for i, post in enumerate(all_posts[:10], 1):
                title = post.get('title', 'Unknown Title')
                all_posts_list += f"{i}. {title}\n"
            
            info_text = (
                f"📊 **Dramawallah Bot Statistics**\n\n"
                f"**📈 Overview:**\n"
                f"• Total Posts: {stats['total_posts']}\n"
                f"• Ongoing Dramas: {stats['ongoing_posts']}\n"
                f"• Completed Dramas: {stats['all_posts']}\n"
                f"• Total Files: {stats['total_files']}\n"
                f"• Blog Posts: {stats['total_blogs']}\n"
                f"• Registered Users: {stats['total_users']}\n\n"
                f"**🌐 Website:** {WEBSITE_URL}\n\n"
            )
            
            if ongoing_posts:
                info_text += f"**📺 Ongoing Dramas ({len(ongoing_posts)}):**\n{ongoing_list}\n"
            
            if all_posts:
                info_text += f"**📁 All Posts ({len(all_posts)}):**\n{all_posts_list}"
            
            await update.message.reply_text(info_text)
            
        except Exception as e:
            logger.error(f"Error in info command: {e}")
            await update.message.reply_text("❌ Error retrieving information. Please try again.")
    
    # ==================== GROUP SEARCH FUNCTIONALITY ====================
    async def handle_text_message(self, update: Update, context: CallbackContext):
        """Handle text messages in groups for search functionality"""
        try:
            # Only process in groups, not private chats
            if update.effective_chat.type == "private":
                return
            
            message_text = update.message.text.lower()
            
            # Get CURRENT drama names from website (always fresh)
            current_dramas = self.get_current_drama_names()
            
            # Combine with general search triggers
            all_keywords = current_dramas + SEARCH_TRIGGERS
            
            # Check if message contains any relevant keywords
            found_keywords = []
            for keyword in all_keywords:
                if keyword in message_text:
                    found_keywords.append(keyword)
            
            if found_keywords:
                await self.provide_search_results(update, found_keywords)
            
        except Exception as e:
            logger.error(f"Error in group search: {e}")
    
    async def provide_search_results(self, update: Update, found_keywords):
        """Provide search results for found keywords"""
        try:
            # Get search data from website
            search_data = self.website.data.get("search_data", [])
            results = []
            
            # Find matching content
            for keyword in found_keywords:
                for item in search_data:
                    if (keyword in item.get('title', '').lower() or 
                        keyword in item.get('type', '').lower() or
                        keyword in item.get('category', '').lower()):
                        results.append(item)
            
            # Remove duplicates
            unique_results = []
            seen_titles = set()
            for result in results:
                if result['title'] not in seen_titles:
                    unique_results.append(result)
                    seen_titles.add(result['title'])
            
            if unique_results:
                await self.send_search_results(update, unique_results)
                
        except Exception as e:
            logger.error(f"Error providing search results: {e}")
    
    async def send_search_results(self, update: Update, results):
        """Send formatted search results to group"""
        try:
            keyboard = []
            for result in results[:3]:  # Max 3 results
                if result['category'] == 'ongoing':
                    url = f"{WEBSITE_URL}/#ongoing"
                elif result['category'] == 'blog':
                    url = f"{WEBSITE_URL}/#blog"
                elif result['category'] == 'home':
                    url = f"{WEBSITE_URL}/#home"
                else:
                    url = f"{WEBSITE_URL}/#bot-posts"
                
                keyboard.append([InlineKeyboardButton(
                    f"🎬 {result['title']}",
                    url=url
                )])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"🔍 @{update.effective_user.username} Here are the results you were searching for:",
                reply_markup=reply_markup,
                reply_to_message_id=update.message.message_id
            )
            
        except Exception as e:
            logger.error(f"Error sending search results: {e}")
    
    # ==================== UTILITY FUNCTIONS ====================
    async def post_to_channel(self, processed_files, channel_link):
        """Post files to specified channel with download buttons"""
        try:
            for file_data in processed_files:
                keyboard = [
                    [InlineKeyboardButton("📥 Download", url=file_data['shortened_link'])]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                # Send message to channel
                await self.application.bot.send_message(
                    chat_id=channel_link,
                    text=f"📄 **{file_data['file_name']}**",
                    reply_markup=reply_markup
                )
                
            logger.info(f"Posted {len(processed_files)} files to {channel_link}")
            
        except Exception as e:
            logger.error(f"Error posting to channel {channel_link}: {e}")
            raise
    
    def run(self):
        """Start the bot with Render compatibility"""
        logger.info("🚀 Starting Dramawallah Bot on Render...")
        print("🤖 Bot is starting...")
        print(f"🌐 Website: {WEBSITE_URL}")
        print("✅ Bot is ready and listening for messages...")
        
        # Start polling
        self.application.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )

def handle_shutdown(signum, frame):
    """Handle shutdown signals gracefully"""
    print("🛑 Received shutdown signal. Bot is stopping...")
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)

def main():
    """Main function with error handling for Render"""
    try:
        # Validate environment variables
        required_vars = ['BOT_TOKEN', 'MONGO_URI', 'ADMIN_IDS']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
            print("💡 Please set them in Render dashboard → Environment")
            sys.exit(1)
        
        print("✅ Environment variables validated")
        print("🔧 Initializing Dramawallah Bot...")
        
        # Create and run bot
        bot = DramawallahBot()
        bot.run()
        
    except Exception as e:
        print(f"💥 Bot crashed: {e}")
        logger.error(f"Bot crashed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
