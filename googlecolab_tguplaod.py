#@title 📤 Telegram File Uploader Setup
!pip install -q pyrogram tgcrypto aiohttp humanize nest-asyncio

import os
import time
import asyncio
import aiohttp
from pyrogram import Client
from urllib.parse import urlparse, unquote
from humanize import naturalsize
import nest_asyncio
from IPython.display import clear_output

# Enable nested event loops for Colab
nest_asyncio.apply()

#@markdown Enter your Telegram credentials:
API_ID = "api_id" #@param {type:"string"}
API_HASH = "api_hash" #@param {type:"string"}
BOT_TOKEN = "bot_token_here" #@param {type:"string"}
CHAT_ID = "chat_id_here" #@param {type:"string"}

class FileUploader:
    def __init__(self):
        self.app = Client(
            "file_uploader",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            in_memory=True
        )
        self.log_text = ""
        self.start_time = time.time()
        self.current_file = ""
        
    def format_size(self, size):
        return naturalsize(size, binary=True)

    def get_filename_from_url(self, url):
        parsed = urlparse(url)
        return unquote(os.path.basename(parsed.path))

    def update_progress(self, current, total, speed, filename):
        progress = current / total * 100 if total > 0 else 0
        self.log_text = f"""
Current File: {filename}
Downloaded: {self.format_size(current)}/{self.format_size(total)}
Progress: {progress:.1f}%
Speed: {self.format_size(speed)}/s
"""
        clear_output(wait=True)
        print(self.log_text)

    async def download_and_send(self, url):
        self.log_text += f"\n📥 Starting download: {url}\n"
        print(self.log_text)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        self.log_text += "❌ Download failed! Invalid URL or server error.\n"
                        print(self.log_text)
                        return

                    filename = self.get_filename_from_url(url) or "downloaded_file"
                    self.current_file = filename
                    total_size = int(response.headers.get('content-length', 0))
                    downloaded_size = 0
                    start_time = time.time()

                    with open(filename, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            
                            if time.time() - start_time > 1:
                                speed = downloaded_size / (time.time() - start_time)
                                self.update_progress(downloaded_size, total_size, speed, filename)
                                start_time = time.time()

            self.log_text += "\n📤 Uploading to Telegram...\n"
            print(self.log_text)

            # Start the client
            await self.app.start()
            
            # Convert CHAT_ID to integer if it's numeric
            try:
                chat_id = int(CHAT_ID)
            except ValueError:
                chat_id = CHAT_ID  # Keep as string if it's a username/channel name

            # Reset start_time for upload progress
            self.start_time = time.time()
            
            try:
                message = await self.app.send_document(
                    chat_id,
                    filename,
                    caption=f"📁 **File:** `{filename}`\n"
                            f"**Size:** {self.format_size(os.path.getsize(filename))}\n"
                            f"**Source:** `{url}`",
                    progress=self.upload_progress
                )
                
                self.log_text += f"✅ File sent successfully! Message ID: {message.id}\n"
                print(self.log_text)
            
            finally:
                # Stop the client
                await self.app.stop()

            os.remove(filename)

        except Exception as e:
            self.log_text += f"❌ Error: {str(e)}\n"
            print(self.log_text)

    async def upload_progress(self, current, total):
        if total:
            percentage = current * 100 / total
            speed = current / (time.time() - self.start_time)
            self.log_text = f"""
Uploading: {self.current_file}
Progress: {percentage:.1f}%
Speed: {self.format_size(speed)}/s
"""
            clear_output(wait=True)
            print(self.log_text)

#@markdown Enter the URLs to download (one per line):
URLS = "@you_downlaod_link_here" #@param {type:"string"}

async def main():
    uploader = FileUploader()
    urls = [url.strip() for url in URLS.split('\n') if url.strip()]
    
    if not urls:
        print("❌ Please enter at least one URL!")
        return
        
    print(f"🔄 Processing {len(urls)} URLs...")
    for url in urls:
        await uploader.download_and_send(url)

# Run the uploader
if __name__ == "__main__":
    if not all([API_ID, API_HASH, BOT_TOKEN, CHAT_ID]):
        print("❌ Please fill in all the required credentials!")
    else:
        asyncio.run(main())
