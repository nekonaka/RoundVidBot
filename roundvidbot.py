import telebot
import os
import time
from moviepy.editor import VideoFileClip
from moviepy.editor import *

API_TOKEN = 'YOUR_TOKEN'
MAX_FILE_SIZE_MB = 20  # Set the maximum file size in MB
MAX_WIDTH = 480
NON_VIDEO_CONTENT_TYPES = ["text", "audio", "document", "photo", "sticker", "video_note", "voice", "location", "contact",
                 "new_chat_members", "left_chat_member", "new_chat_title", "new_chat_photo", "delete_chat_photo",
                 "group_chat_created", "supergroup_chat_created", "channel_chat_created", "migrate_to_chat_id",
                 "migrate_from_chat_id", "pinned_message"]

bot = telebot.TeleBot(API_TOKEN)

@bot.message_handler(content_types=['video'])
def handle_video(message):
    bot.send_message(message.chat.id, "OK! Now wait!")
    try:
        # Check file size before downloading
        if message.video.file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
            bot.send_message(message.chat.id, "The video file is too large. Please send a file smaller than 20 MB.")
            return

        video_info = bot.get_file(message.video.file_id)
        downloaded_file = bot.download_file(video_info.file_path)

        # Save the video temporarily
        video_path = "temp_video.mp4"
        with open(video_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        # Process the video
        output_path = "output_video.mp4"
        crop_video(video_path, output_path)

        # Send the video as a round video note
        with open(output_path, 'rb') as video:
            bot.send_video_note(message.chat.id, video)

    except telebot.apihelper.ApiException as e:
        if e.error_code == 404:  # Handle 404 errors (not found)
            bot.send_message(message.chat.id, "Sorry, I couldn't find the video.")
        elif e.error_code == 400:  # Handle 400 errors (bad request)
            bot.send_message(message.chat.id, "Sorry, I couldn't process the request.")
        elif e.error_code == 500:  # Handle 500 errors (internal server error)
            bot.send_message(message.chat.id, "Sorry, something went wrong on my side.")
        elif e.error_code == 502:  # Handle 502 errors (bad gateway)
            bot.send_message(message.chat.id, "Sorry, I'm having trouble connecting to Telegram.")
        elif e.error_code == 504:  # Handle 504 errors (gateway timeout)
            bot.send_message(message.chat.id, "Sorry, I'm experiencing a timeout. Please try again later.")
        else:
            bot.send_message(message.chat.id, f"An error occurred: {e}")
    except Exception as e:
        bot.send_message(message.chat.id, f"An error occurred while processing the video: {e}")

    finally:
        # Clean up temporary files
        cleanup(video_path, output_path)

def crop_video(input_path, output_path):
    try:
        # Load the video
        clip = VideoFileClip(input_path)

        # Check duration and apply subclip only if needed
        if clip.duration > 60:
            clip = clip.subclip(0, min(clip.duration, 60)) # Обрезаем с 0 до 60 секунд, если длительность больше 60 с


        width, height = clip.size
        max_dim = max(width, height)

        # Crop to 1:1 aspect ratio based on the larger dimension
        if width > height:
            x1 = (width - height) / 2
            x2 = (width + height) / 2
            y1 = 0
            y2 = height
        else:
            x1 = 0
            x2 = width
            y1 = (height - width) / 2
            y2 = (height + width) / 2

        clip = clip.crop(x1=x1, x2=x2, y1=y1, y2=y2)

        # Изменение размера видео, если ширина больше MAX_WIDTH
        if clip.size[0] > MAX_WIDTH:
            clip = clip.resize(width=MAX_WIDTH)

        # Write the video note
        clip.write_videofile(output_path, codec="libx264", fps=30)
    except Exception as e:
        print(f"Error during video processing: {e}")

def cleanup(video_path, output_path=None):
    if os.path.exists(video_path):
        os.remove(video_path)
    if output_path and os.path.exists(output_path):
        os.remove(output_path)

@bot.message_handler(content_types=NON_VIDEO_CONTENT_TYPES)
def handle_non_video(message):
    bot.send_message(message.chat.id, "Please send a video. And remember - no more than 20 MB and 1:00!")

while True:
    try:
        bot.polling(none_stop=True) 
    except Exception as e:
        print(f"An error occurred: {e}")
        time.sleep(5) # Wait for 5 seconds before retrying