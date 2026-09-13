"""
data/video.mp4 를 YouTube에 업로드한다.
GitHub Actions에서는 환경변수(Secrets)로 인증 정보를 받는다:
  YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN

최초 1회는 scripts/get_refresh_token.py 를 로컬에서 실행해
YT_REFRESH_TOKEN 값을 얻어야 한다 (README 참고).
"""
import json
import os

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT_PATH = os.path.join(BASE_DIR, "data", "script.json")
VIDEO_PATH = os.path.join(BASE_DIR, "data", "video.mp4")

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def get_credentials():
    client_id = os.environ["YT_CLIENT_ID"]
    client_secret = os.environ["YT_CLIENT_SECRET"]
    refresh_token = os.environ["YT_REFRESH_TOKEN"]

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES,
    )
    return creds


def upload():
    with open(SCRIPT_PATH, "r", encoding="utf-8") as f:
        script = json.load(f)

    creds = get_credentials()
    youtube = build("youtube", "v3", credentials=creds)

    body = {
        "snippet": {
            "title": script["title"],
            "description": script["description"],
            "tags": script["tags"],
            "categoryId": "27",  # Education
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(VIDEO_PATH, mimetype="video/mp4", resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"업로드 진행률: {int(status.progress() * 100)}%")

    video_id = response["id"]
    print(f"업로드 완료: https://youtube.com/shorts/{video_id}")
    return video_id


if __name__ == "__main__":
    upload()
