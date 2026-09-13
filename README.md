# 세계사 쇼츠 자동 업로드 봇 (완전 무료)

매일 한국시간 오전 9시, 한국어 위키백과 "역사 속 오늘" 이벤트 중 하나를 골라
1분짜리 유튜브 쇼츠를 자동 생성·업로드합니다.

**사용 도구 (전부 무료)**
- 소재: 한국어 위키백과 REST API
- 음성(TTS): edge-tts (Microsoft Edge 음성엔진, 비공식 무료 라이브러리)
- 영상 합성: ffmpeg (오픈소스)
- 실행 스케줄러: GitHub Actions (public/private 저장소 무료 티어)
- 업로드: YouTube Data API v3 (무료 쿼터, 하루 업로드 1회면 충분)

---

## 1. 준비물

- GitHub 계정
- Google 계정 (유튜브 채널 보유)

## 2. YouTube API 설정 (최초 1회, 15분)

1. [Google Cloud Console](https://console.cloud.google.com/)에서 새 프로젝트 생성
2. "API 및 서비스 > 라이브러리"에서 **YouTube Data API v3** 사용 설정
3. "API 및 서비스 > OAuth 동의 화면" 설정 (외부 / 테스트 사용자에 본인 계정 추가)
4. "사용자 인증 정보 > OAuth 클라이언트 ID 만들기" → 유형: **데스크톱 앱**
5. 생성된 클라이언트의 JSON을 다운로드하여 `client_secret.json` 이름으로 프로젝트 루트에 저장
6. 로컬에서 실행:
   ```bash
   pip install -r requirements.txt
   python scripts/get_refresh_token.py
   ```
   브라우저가 열리면 본인 유튜브 계정으로 로그인/동의 → 터미널에 아래 3개 값 출력됨
   ```
   YT_CLIENT_ID=...
   YT_CLIENT_SECRET=...
   YT_REFRESH_TOKEN=...
   ```

## 3. GitHub 저장소 설정

1. 이 폴더를 새 GitHub 저장소로 push
   ```bash
   git init
   git add .
   git commit -m "init"
   git branch -M main
   git remote add origin <내 저장소 URL>
   git push -u origin main
   ```
2. 저장소 → **Settings > Secrets and variables > Actions**에서 Secret 3개 등록:
   - `YT_CLIENT_ID`
   - `YT_CLIENT_SECRET`
   - `YT_REFRESH_TOKEN`
3. **Settings > Actions > General**에서 워크플로우에 쓰기 권한 부여:
   - "Workflow permissions" → **Read and write permissions** 선택 (used_topics.json 자동 커밋용)

## 4. 완료 — 이제부터 매일 자동 업로드

- `.github/workflows/daily_upload.yml`이 매일 UTC 00:00(=한국시간 09:00)에 자동 실행됩니다.
- 바로 테스트해보고 싶다면 저장소의 **Actions** 탭 → `Daily History Shorts Upload` → **Run workflow** 버튼으로 수동 실행 가능합니다.

---

## 로컬에서 미리 테스트하는 법

```bash
pip install -r requirements.txt
brew install ffmpeg   # 또는 apt install ffmpeg
export YT_CLIENT_ID=...
export YT_CLIENT_SECRET=...
export YT_REFRESH_TOKEN=...
python main.py
```

## 커스터마이징

- **목소리 바꾸기**: `scripts/generate_audio.py`의 `TTS_VOICE` (예: 남성 목소리는 `ko-KR-InJoonNeural`)
- **말하는 속도**: `TTS_RATE` (예: `"+10%"`로 더 빠르게)
- **자막 스타일**: `scripts/generate_video.py`의 `subtitle_style`
- **채널 공개 범위**: `scripts/upload_youtube.py`의 `privacyStatus` (`"private"`로 바꾸면 비공개 업로드 후 직접 검토·공개 가능 — 처음에는 이 방식 추천)

## 알아두면 좋은 점

- 위키백과 "역사 속 오늘" 항목이 그날그날 다르기 때문에, 소재가 부족한 날은 자동으로 스킵됩니다 (실패 아님).
- 대본은 위키백과 원문을 그대로 읽지 않고 짧게 재구성한 문장을 사용하지만, 채널을 키울 계획이라면 이 부분을 유료 LLM API(Claude/GPT)로 교체해 훨씬 자연스럽고 풍부한 대본을 만드는 걸 추천합니다 (`scripts/generate_script.py`만 교체하면 됩니다).
- 처음 며칠은 `privacyStatus`를 `"private"`으로 두고 결과물을 직접 확인한 뒤 `"public"`으로 바꾸는 걸 권장합니다.
