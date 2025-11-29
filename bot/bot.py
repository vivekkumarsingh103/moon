from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler
from datetime import datetime
import os
import logging
from config import BOT_TOKEN
from database import Database
from file_handler import FileHandler
from website_manager import WebsiteManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Conversation states
CHANNEL_LINK, IMAGE, FILES, COMPLETION_CHECK = range(4)

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
        
        self.application.add_handler(addpost_conv)
        self.application.add_handler(CommandHandler("search", self.search))
        self.application.add_handler(CommandHandler("ongoing", self.ongoing))
        self.application.add_handler(CommandHandler("blog", self.blog))
        self.application.add_handler(CommandHandler("broadcast", self.broadcast))
        self.application.add_handler(CommandHandler("info", self.info))
        
        # Error handler
        self.application.add_error_handler(self.error_handler)
    
    async def start_addpost(self, update: Update, context: CallbackContext):
        """Start /addpost conversation"""
        try:
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
    
    async def cancel(self, update: Update, context: CallbackContext):
        """Cancel the conversation"""
        context.user_data.clear()
        await update.message.reply_text("❌ Operation cancelled.")
        return ConversationHandler.END
    
    async def error_handler(self, update: Update, context: CallbackContext):
        """Handle errors in the bot"""
        logger.error(f"Update {update} caused error {context.error}")
        
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id if update else None,
                text="❌ An error occurred. Please try again later."
            )
        except:
            pass

# Other command handlers will be implemented next
async def search(self, update: Update, context: CallbackContext):
    """Handle /search command"""
    await update.message.reply_text("🔍 Search functionality coming soon!")

async def ongoing(self, update: Update, context: CallbackContext):
    """Handle /ongoing command"""
    await update.message.reply_text("📺 Ongoing dramas management coming soon!")

async def blog(self, update: Update, context: CallbackContext):
    """Handle /blog command"""
    await update.message.reply_text("📝 Blog management coming soon!")

async def broadcast(self, update: Update, context: CallbackContext):
    """Handle /broadcast command"""
    await update.message.reply_text("📢 Broadcast functionality coming soon!")

async def info(self, update: Update, context: CallbackContext):
    """Handle /info command"""
    await update.message.reply_text("📊 Info and statistics coming soon!")

def main():
    bot = DramawallahBot()
    logger.info("Bot is starting...")
    bot.application.run_polling()

if __name__ == '__main__':
    main()
