import os
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Replace 'YOUR_BOT_TOKEN' with your actual bot token
BOT_TOKEN = 6994726052: AAGFDn_NBRaNtOIGgU6QcWuamU2aBI4EdAE


def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        'Hi! Send me a link to a web page and I will find and download all videos for you.')


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
    video_tags = soup.find_all('video')
    video_links = [video_tag['src']
                   for video_tag in video_tags if 'src' in video_tag.attrs]
    return video_links


def handle_message(update: Update, context: CallbackContext) -> None:
    page_url = update.message.text
    if 'http' in page_url:
        video_links = find_video_links(page_url)
        if not video_links:
            update.message.reply_text('No videos found on the page.')
            return

        update.message.reply_text(
            f'Found {len(video_links)} videos. Downloading...')
        for idx, video_link in enumerate(video_links):
            file_name = f"video_{idx}.mp4"
            downloaded_file = download_mp4(video_link, file_name)
            if downloaded_file:
                update.message.reply_video(video=open(downloaded_file, 'rb'))
                os.remove(downloaded_file)
            else:
                update.message.reply_text(
                    f'Failed to download video from {video_link}')
    else:
        update.message.reply_text('Please send a valid URL.')


def main() -> None:
    updater = Updater(BOT_TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(MessageHandler(
        Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
