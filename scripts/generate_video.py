"""
- 위키백과에서 이벤트와 연관된 이미지를 여러 장(최대 6장) 다운로드 (AI 이미지가 없을 때 대비용)
- AI가 생성한 일러스트가 있으면 그것을 우선 사용
- 오디오 길이를 이미지 수만큼 나눠 순서대로 장면 전환 (각 장면은 켄 번즈 확대 효과)
- 이미지가 1장뿐이거나 없으면 그에 맞춰 단순하게 처리
- 오디오 길이에 맞춰 영상 길이 설정, SRT 자막을 번인(하드코딩)
- 결과: data/video.mp4 (1080x1920, 세로 쇼츠 규격)
"""
import json
import os
import subprocess

import requests

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT_PATH = os.path.join(BASE_DIR, "data", "script.json")
AUDIO_PATH = os.path.join(BASE_DIR, "data", "audio.mp3")
SRT_PATH = os.path.join(BASE_DIR, "data", "subtitles.srt")
IMAGE_DIR = os.path.join(BASE_DIR, "data", "images")
VIDEO_PATH = os.path.join(BASE_DIR, "data", "video.mp4")

W, H = 1080, 1920
MAX_IMAGES = 6


def download_images(urls: list) -> list:
    os.makedirs(IMAGE_DIR, exist_ok=True)
    paths = []
    for i, url in enumerate(urls[:MAX_IMAGES]):
        dest = os.path.join(IMAGE_DIR, f"image_{i}.jpg")
        try:
            resp = requests.get(url, timeout=20, headers={"User-Agent": "history-shorts-bot/1.0"})
            resp.raise_for_status()
            with open(dest, "wb") as f:
                f.write(resp.content)
            paths.append(dest)
        except Exception as e:
            print(f"이미지 다운로드 실패({url}): {e}")
    return paths


def make_solid_background() -> str:
    dest = os.path.join(IMAGE_DIR, "solid.jpg")
    os.makedirs(IMAGE_DIR, exist_ok=True)
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", f"color=c=0x14213D:s={W}x{H}",
        "-frames:v", "1", dest,
    ], check=True)
    return dest


def get_audio_duration() -> float:
    result = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", AUDIO_PATH,
    ], capture_output=True, text=True, check=True)
    return float(result.stdout.strip())


def zoompan_filter(seg_frames: int, fps: int) -> str:
    return (
        f"scale=-2:{int(H*1.3)},"
        f"zoompan=z='min(zoom+0.0007,1.15)':d={seg_frames}:"
        f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={fps}"
    )


def subtitles_filter_str() -> str:
    if not (os.path.exists(SRT_PATH) and os.path.getsize(SRT_PATH) > 0):
        return ""
    subtitle_style = (
        "FontName=Noto Sans KR,FontSize=17,PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,BorderStyle=3,Outline=2,Shadow=0,"
        "Alignment=2,MarginV=180"
    )
    escaped_srt_path = SRT_PATH.replace("\\", "\\\\").replace(":", "\\:")
    return f"subtitles='{escaped_srt_path}':force_style='{subtitle_style}'"


def run_ffmpeg(cmd: list, fallback_cmd: list = None):
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        if fallback_cmd:
            print("자막 포함 렌더링 실패, 자막 없이 다시 시도합니다.")
            subprocess.run(fallback_cmd, check=True)
        else:
            raise


def build_video(images: list):
    duration = get_audio_duration()
    fps = 30
    n = len(images)
    sub_filter = subtitles_filter_str()

    if n <= 1:
        image = images[0]
        total_frames = int(duration * fps)
        video_filter = zoompan_filter(total_frames, fps)
        if sub_filter:
            video_filter += f",{sub_filter}"
        cmd = [
            "ffmpeg", "-y", "-loop", "1", "-i", image, "-i", AUDIO_PATH,
            "-vf", video_filter, "-map", "0:v", "-map", "1:a",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
            "-shortest", "-t", str(duration), VIDEO_PATH,
        ]
        fallback = None
        if sub_filter:
            fallback = [
                "ffmpeg", "-y", "-loop", "1", "-i", image, "-i", AUDIO_PATH,
                "-vf", zoompan_filter(total_frames, fps), "-map", "0:v", "-map", "1:a",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
                "-shortest", "-t", str(duration), VIDEO_PATH,
            ]
        run_ffmpeg(cmd, fallback)
        print(f"영상 저장 완료 (이미지 1장): {VIDEO_PATH}")
        return

    seg_duration = duration / n
    inputs = []
    filter_parts = []
    for i, image in enumerate(images):
        inputs += ["-loop", "1", "-t", f"{seg_duration:.3f}", "-i", image]
        seg_frames = max(1, int(seg_duration * fps))
        filter_parts.append(f"[{i}:v]{zoompan_filter(seg_frames, fps)}[v{i}]")

    concat_inputs = "".join(f"[v{i}]" for i in range(n))
    filter_complex = ";".join(filter_parts) + f";{concat_inputs}concat=n={n}:v=1:a=0[vcat]"
    final_label = "vcat"
    if sub_filter:
        filter_complex += f";[vcat]{sub_filter}[vfinal]"
        final_label = "vfinal"

    audio_index = n
    cmd = [
        "ffmpeg", "-y", *inputs, "-i", AUDIO_PATH,
        "-filter_complex", filter_complex,
        "-map", f"[{final_label}]", "-map", f"{audio_index}:a",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
        "-shortest", "-t", str(duration), VIDEO_PATH,
    ]

    fallback = None
    if sub_filter:
        filter_complex_no_sub = ";".join(filter_parts) + f";{concat_inputs}concat=n={n}:v=1:a=0[vcat]"
        fallback = [
            "ffmpeg", "-y", *inputs, "-i", AUDIO_PATH,
            "-filter_complex", filter_complex_no_sub,
            "-map", "[vcat]", "-map", f"{audio_index}:a",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
            "-shortest", "-t", str(duration), VIDEO_PATH,
        ]

    run_ffmpeg(cmd, fallback)
    print(f"영상 저장 완료 (이미지 {n}장 슬라이드쇼): {VIDEO_PATH}")


if __name__ == "__main__":
    import glob

    ai_images = sorted(glob.glob(os.path.join(IMAGE_DIR, "ai_*.jpg")))

    if ai_images:
        images = ai_images
        print(f"AI 생성 이미지 {len(images)}장을 사용합니다.")
    else:
        print("AI 이미지가 없어 위키백과 사진으로 대체합니다.")
        with open(SCRIPT_PATH, "r", encoding="utf-8") as f:
            script = json.load(f)
        urls = script.get("thumbnail_urls") or []
        if not urls and script.get("thumbnail_url"):
            urls = [script["thumbnail_url"]]
        images = download_images(urls)

    if not images:
        images = [make_solid_background()]

    build_video(images)
