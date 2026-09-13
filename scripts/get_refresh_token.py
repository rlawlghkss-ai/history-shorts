"""
최초 1회, 본인 컴퓨터(로컬)에서 실행하는 스크립트.
Google Cloud Console에서 받은 client_secret.json을 프로젝트 루트에 두고 실행하면
브라우저가 열리고 로그인/동의 후 refresh_token이 출력된다.
이 값을 GitHub 저장소의 Secrets(YT_REFRESH_TOKEN)에 등록한다.

실행: python scripts/get_refresh_token.py
"""
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

if __name__ == "__main__":
    flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
    creds = flow.run_local_server(port=0)
    print("\n=== 아래 값을 GitHub Secrets에 등록하세요 ===")
    print(f"YT_CLIENT_ID={creds.client_id}")
    print(f"YT_CLIENT_SECRET={creds.client_secret}")
    print(f"YT_REFRESH_TOKEN={creds.refresh_token}")
