"""Optional auto-upload of finished clips to YouTube Shorts.

Setup (one time, on your own machine):
  1. Create a Google Cloud project, enable the YouTube Data API v3.
  2. Create OAuth credentials (Desktop app) -> download client_secrets.json.
  3. Run:  python -m clipper.uploader_youtube --auth --secrets client_secrets.json
     (a browser window opens; the token is saved to youtube_token.json)
  4. Set env YOUTUBE_CLIENT_SECRETS=/path/client_secrets.json and
     YOUTUBE_TOKEN_FILE=/path/youtube_token.json on the server.

Then: python -m clipper.uploader_youtube clip.mp4 --title "..." --tags a b
"""
from __future__ import annotations

import argparse
import http.client
import os
import random
import time

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
_MAX_RETRIES = 5
_RETRIABLE = (500, 502, 503, 504)


def get_service(client_secrets: str, token_file: str):
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise RuntimeError(
            "Upload deps missing. Run: pip install -r requirements-clipper.txt"
        ) from exc

    creds = None
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        elif client_secrets and os.path.exists(client_secrets):
            flow = InstalledAppFlow.from_client_secrets_file(client_secrets, SCOPES)
            creds = flow.run_local_server(port=0)
        else:
            raise RuntimeError(
                "No valid YouTube credentials. Run the --auth flow locally first "
                "(see module docstring) and set YOUTUBE_TOKEN_FILE."
            )
        with open(token_file, "w") as f:
            f.write(creds.to_json())
    return build("youtube", "v3", credentials=creds)


def upload_short(path: str, title: str, description: str = "",
                 tags: list[str] | tuple = (), privacy: str = "unlisted",
                 category_id: str = "24", client_secrets: str = "",
                 token_file: str = "youtube_token.json") -> str:
    """Upload a vertical mp4 as a Short. Returns the watch URL."""
    from googleapiclient.http import MediaFileUpload

    service = get_service(client_secrets or os.environ.get("YOUTUBE_CLIENT_SECRETS", ""),
                          token_file or os.environ.get("YOUTUBE_TOKEN_FILE", "youtube_token.json"))
    body = {"snippet": {"title": title[:95] + (" #Shorts" if len(title) < 92 else ""),
                        "description": description[:4900],
                        "tags": list(tags)[:30],
                        "categoryId": category_id},
            "status": {"privacyStatus": privacy, "selfDeclaredMadeForKids": False}}
    media = MediaFileUpload(path, mimetype="video/mp4", resumable=True, chunksize=8 * 1024 * 1024)
    req = service.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    retries = 0
    while response is None:
        try:
            _status, response = req.next_chunk()
        except Exception as e:
            code = getattr(getattr(e, "resp", None), "status", None)
            if code in _RETRIABLE or isinstance(e, (http.client.HTTPException, OSError)):
                retries += 1
                if retries > _MAX_RETRIES:
                    raise
                time.sleep(2 ** retries + random.random())
            else:
                raise
    vid = response.get("id", "")
    url = f"https://www.youtube.com/shorts/{vid}" if vid else ""
    print(f"uploaded: {url}", flush=True)
    return url


def main() -> None:
    ap = argparse.ArgumentParser(description="Upload a clip to YouTube Shorts")
    ap.add_argument("video", nargs="?", help="mp4 file to upload")
    ap.add_argument("--auth", action="store_true", help="run OAuth flow and exit")
    ap.add_argument("--secrets", default=os.environ.get("YOUTUBE_CLIENT_SECRETS", ""))
    ap.add_argument("--token", default=os.environ.get("YOUTUBE_TOKEN_FILE", "youtube_token.json"))
    ap.add_argument("--title", default="Clip #Shorts")
    ap.add_argument("--description", default="")
    ap.add_argument("--tags", nargs="*", default=["Shorts"])
    ap.add_argument("--privacy", default=os.environ.get("YOUTUBE_PRIVACY", "unlisted"))
    args = ap.parse_args()

    if args.auth:
        get_service(args.secrets, args.token)
        print(f"auth OK, token saved to {args.token}")
        return
    if not args.video:
        ap.error("video file required (or use --auth)")
    upload_short(args.video, args.title, args.description, args.tags,
                 args.privacy, client_secrets=args.secrets, token_file=args.token)


if __name__ == "__main__":
    main()
