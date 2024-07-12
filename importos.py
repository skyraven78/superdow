import os
import requests
from bs4 import BeautifulSoup
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, Dispatcher
from flask import Flask, request

# Get the bot token and app URL from the environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN')
APP_URL = os.getenv('APP_URL')  # The URL of your deployed app (e.g., https://your-app.onrender.com)

if not BOT_TOKEN:
    raise ValueError("No BOT_TOKEN provided. Set the BOT_TOKEN environment variable.")

if not APP_URL:
    raise ValueError("No APP_URL provided. Set the APP_URL environment variable.")

app = Flask(__name__)

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Hi! Send me a link to a web page and I will find and download all videos for you.')

def download_mp4(url: str, file_name: str) -> str:
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(file_name, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        return file_name
    else:
        return None

def find_video_links(page_url: str) -> list:
    response = requests.get(page_url)
    soup = BeautifulSoup(response.content, 'html.parser')

    video_links = []

    # Find videos in <video> tags
    for video_tag in soup.find_all('video'):
        if 'src' in video_tag.attrs:
            video_links.append(video_tag['src'])
        for source_tag in video_tag.find_all('source'):
            if 'src' in source_tag.attrs:
                video_links.append(source_tag['src'])

    # Find videos in <iframe> tags
    for iframe_tag in soup.find_all('iframe'):
        if 'src' in iframe_tag.attrs:
            video_links.append(iframe_tag['src'])

    # Deduplicate links
    video_links = list(set(video_links))

    return video_links

def handle_message(update: Update, context: CallbackContext) -> None:
    page_url = update.message.text
    if 'http' in page_url:
        video_links = find_video_links(page_url)
        if not video_links:
            update.message.reply_text('No videos found on the page.')
            return

        update.message.reply_text(f'Found {len(video_links)} videos. Downloading...')
        for idx, video_link in enumerate(video_links):
            file_name = f"video_{idx}.mp4"
            downloaded_file = download_mp4(video_link, file_name)
            if downloaded_file:
                update.message.reply_video(video=open(downloaded_file, 'rb'))
                os.remove(downloaded_file)
            else:
                update.message.reply_text(f'Failed to download video from {video_link}')
    else:
        update.message.reply_text('Please send a valid URL.')

@app.route(f"/{BOT_TOKEN}", methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

def main() -> None:
    global bot, dispatcher
    bot = Bot(token=BOT_TOKEN)
    dispatcher = Dispatcher(bot, None, workers=0)

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    bot.set_webhook(f"{APP_URL}/{BOT_TOKEN}")

if __name__ == '__main__':
    main()
    app.run(host='0.0.0.0', port=8443)

