#!/usr/bin/env python3
"""
Script to download videos from URLs in urls.txt and upload them to YouTube
"""
import os
import json
import time
from datetime import datetime
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from googleapiclient.http import MediaFileUpload
import subprocess

# YouTube API configuration
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def get_authenticated_service():
    """Get authenticated YouTube service using stored token"""
    credentials = google.oauth2.credentials.Credentials.from_authorized_user_info(
        json.loads(os.environ.get('YOUTUBE_TOKEN'))
    )
    return googleapiclient.discovery.build(
        API_SERVICE_NAME, API_VERSION, credentials=credentials
    )

def download_video(url, output_dir="downloads"):
    """Download video using yt-dlp"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_template = f"{output_dir}/{timestamp}_%(title)s.%(ext)s"
    
    command = [
        "yt-dlp",
        "--format", "best",
        "--output", output_template,
        "--no-playlist",
        url
    ]
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        output_lines = result.stdout.strip().split('\n')
        
        # Find the line that contains the output filename
        for line in output_lines:
            if "Destination" in line and output_dir in line:
                parts = line.split("Destination: ")
                if len(parts) > 1:
                    return parts[1].strip()
        
        # If we couldn't find the filename in the output, list files in the directory
        # and take the most recent one
        files = [os.path.join(output_dir, f) for f in os.listdir(output_dir)]
        if files:
            return max(files, key=os.path.getctime)
        
        return None
    except subprocess.CalledProcessError as e:
        print(f"Error downloading video: {e}")
        print(f"Error output: {e.stderr}")
        return None

def upload_to_youtube(youtube, file_path, url):
    """Upload video to YouTube"""
    try:
        # Extract video title from filename
        filename = os.path.basename(file_path)
        video_title = os.path.splitext(filename)[0]
        # Remove timestamp prefix if it exists
        if '_' in video_title and video_title[:15].replace('_', '').isdigit():
            video_title = video_title[16:]
        
        # Video metadata
        body = {
            "snippet": {
                "title": video_title,
                "description": f"Automatically uploaded video from: {url}",
                "tags": ["auto-upload"]
            },
            "status": {
                "privacyStatus": "private"  # Set to private by default for safety
            }
        }

        # Upload the video
        media = MediaFileUpload(
            file_path, 
            resumable=True,
            chunksize=1024*1024,
            mimetype="application/octet-stream"
        )
        
        request = youtube.videos().insert(
            part=",".join(body.keys()),
            body=body,
            media_body=media
        )
        
        print(f"Uploading {file_path} to YouTube...")
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"Uploaded {int(status.progress() * 100)}%")
        
        print(f"Upload Complete! Video ID: {response['id']}")
        return response['id']
    except Exception as e:
        print(f"Error uploading to YouTube: {e}")
        return None

def main():
    # Read URLs from file
    with open("urls.txt", "r") as f:
        urls = [line.strip() for line in f.readlines() if line.strip()]
    
    if not urls:
        print("No URLs found in urls.txt")
        return
    
    # Get authenticated YouTube service
    youtube = get_authenticated_service()
    
    for url in urls:
        print(f"Processing URL: {url}")
        # Download video
        video_path = download_video(url)
        if not video_path:
            print(f"Failed to download video from {url}, skipping...")
            continue
        
        print(f"Downloaded video: {video_path}")
        
        # Upload to YouTube
        video_id = upload_to_youtube(youtube, video_path, url)
        if video_id:
            print(f"Successfully uploaded video from {url} to YouTube with ID: {video_id}")
        else:
            print(f"Failed to upload video from {url} to YouTube")
        
        # Add a delay between uploads to avoid rate limiting
        if url != urls[-1]:
            print("Waiting 30 seconds before next upload...")
            time.sleep(30)
        
        # Optional: remove the downloaded file after successful upload
        # if video_id and os.path.exists(video_path):
        #     os.remove(video_path)

if __name__ == "__main__":
    main()