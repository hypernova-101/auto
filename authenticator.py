#!/usr/bin/env python3
"""
One-time script to generate YouTube API tokens
"""
import os
import json
import google_auth_oauthlib.flow

# YouTube API configuration
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def get_authenticated_credentials():
    """Get authenticated credentials through OAuth flow"""
    # Path to your downloaded client secrets file
    client_secrets_file = "client_secrets.json"
    
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        client_secrets_file, SCOPES)
    credentials = flow.run_local_server(port=8080)
    
    # Save the credentials for later use
    token_info = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }
    
    with open('youtube_token.json', 'w') as token_file:
        json.dump(token_info, token_file)
    
    print("Authentication successful!")
    print("Token saved to youtube_token.json")
    print("Content of your token (save this for GitHub secrets):")
    print(json.dumps(token_info))

if __name__ == "__main__":
    # For local testing, disable OAuthlib's HTTPS verification
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    get_authenticated_credentials()