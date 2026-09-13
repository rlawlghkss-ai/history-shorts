"""
전체 파이프라인 실행: 주제선정 -> 대본 -> 음성/자막 -> 영상 -> 업로드
"""
import subprocess
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def run(script_name: str):
    path = os.path.join(BASE_DIR, "scripts", script_name)
    print(f"\n=== 실행: {script_name} ===")
    result = subprocess.run([sys.executable, path])
    if result.returncode != 0:
        print(f"{script_name} 실패 또는 스킵 (exit code {result.returncode})")
        sys.exit(result.returncode)


if __name__ == "__main__":
    run("fetch_topic.py")
    run("generate_script.py")
    run("generate_audio.py")
    run("generate_video.py")
    run("upload_youtube.py")
    print("\n모든 단계 완료!")
