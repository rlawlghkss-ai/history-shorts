"""
- 위키백과 썸네일 이미지가 있으면 다운로드, 없으면 단색 배경 사용
- ffmpeg의 zoompan 필터로 켄 번즈(천천히 확대) 효과
- 오디오 길이에 맞춰 영상 길이 설정, SRT 자막을 번인(하드코딩)
- 결과: data/video.mp4 (1080x1920, 세로 쇼츠 규격)
"""
import json
import os
import subprocess

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT_PATH = os.path.join(BASE_DIR, "data", "script.json")
AUDIO_PATH = os.path.join(BASE_DIR, "data", "audio.mp3")
SRT_PATH = os.path.join(BASE_DIR, "data", "subtitles.srt")
IMAGE_PATH = os.path.join(BASE_DIR, "data", "background.jpg")
VIDEO_PATH = os.path.join(BASE_DIR, "data", "video.mp4")

W, H = 1080, 1920


def download_image(url: str) -> bool:
    import requests
    try:
        resp = requests.get(url, timeout=20, headers={"User-Agent": "history-shorts-bot/1.0"})
        resp.raise_for_status()
        with open(IMAGE_PATH, "wb") as f:
            f.write(resp.content)
        return True
    except Exception as e:
        print(f"이미지 다운로드 실패, 단색 배경으로 대체: {e}")
        return False


def make_solid_background():
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", f"color=c=0x14213D:s={W}x{H}",
        "-frames:v", "1", IMAGE_PATH,
    ], check=True)


def get_audio_duration() -> float:
    result = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", AUDIO_PATH,
    ], capture_output=True, text=True, check=True)
    return float(result.stdout.strip())


def build_video():
    duration = get_audio_duration()
    fps = 30
    total_frames = int(duration * fps)

    zoompan = (
        f"scale=-2:{int(H*1.3)},"
        f"zoompan=z='min(zoom+0.0007,1.15)':d={total_frames}:"
        f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={fps}"
    )

    has_subtitles = os.path.exists(SRT_PATH) and os.path.getsize(SRT_PATH) > 0

    if has_subtitles:
        subtitle_style = (
            "FontName=Noto Sans KR,FontSize=17,PrimaryColour=&H00FFFFFF,"
            "OutlineColour=&H00000000,BorderStyle=3,Outline=2,Shadow=0,"
            "Alignment=2,MarginV=180"
        )
        escaped_srt_path = SRT_PATH.replace("\\", "\\\\").replace(":", "\\:")
        subtitles_filter = f",subtitles='{escaped_srt_path}':force_style='{subtitle_style}'"
    else:
        print("자막 파일이 비어있거나 없어서 자막 없이 영상을 만듭니다.")
        subtitles_filter = ""

    video_filter = f"{zoompan}{subtitles_filter}"

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", IMAGE_PATH,
        "-i", AUDIO_PATH,
        "-vf", video_filter,
        "-map", "0:v", "-map", "1:a",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k",
        "-shortest",
        "-t", str(duration),
        VIDEO_PATH,
    ]
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        if has_subtitles:
            print("자막 포함 렌더링 실패, 자막 없이 다시 시도합니다.")
            cmd_no_sub = [
                "ffmpeg", "-y",
                "-loop", "1", "-i", IMAGE_PATH,
                "-i", AUDIO_PATH,
                "-vf", zoompan,
                "-map", "0:v", "-map", "1:a",
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "160k",
                "-shortest",
                "-t", str(duration),
                VIDEO_PATH,
            ]
            subprocess.run(cmd_no_sub, check=True)
        else:
            raise

    print(f"영상 저장 완료: {VIDEO_PATH}")


if __name__ == "__main__":
    with open(SCRIPT_PATH, "r", encoding="utf-8") as f:
        script = json.load(f)

    ok = False
    if script.get("thumbnail_url"):
        ok = download_image(script["thumbnail_url"])
    if not ok:
        make_solid_background()

    build_video()
