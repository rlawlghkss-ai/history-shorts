"""
data/script.json 의 내용을 바탕으로 장면별 AI 일러스트를 생성한다.
Pollinations.ai (가입/키 불필요, 완전 무료)의 이미지 생성 API를 사용한다.
https://image.pollinations.ai/prompt/{prompt}

훅(도입) / 본문(핵심 사건) / 마무리, 3장면에 맞춰 이미지를 3장 생성해서
data/images/ai_0.jpg, ai_1.jpg, ai_2.jpg 로 저장한다.
생성에 실패한 장면은 건너뛰고, 성공한 이미지만 사용한다.
"""
import json
import os
import random
import time
import urllib.parse

import requests

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT_PATH = os.path.join(BASE_DIR, "data", "script.json")
IMAGE_DIR = os.path.join(BASE_DIR, "data", "images")

W, H = 1080, 1920
STYLE_SUFFIX = (
    "cinematic historical illustration, digital painting, dramatic lighting, "
    "highly detailed, atmospheric, no text, no watermark, no logo"
)


def build_prompts(script: dict) -> list:
    year = script.get("key", "").split("_")[0] or "history"
    fact_en = script.get("fact_en") or ""

    prompts = [
        f"epic wide establishing shot representing the year {year}, {STYLE_SUFFIX}",
    ]
    if fact_en:
        prompts.append(f"scene depicting: {fact_en}. {STYLE_SUFFIX}")
    prompts.append(f"atmospheric closing shot, reflective mood, year {year}, {STYLE_SUFFIX}")
    return prompts


def generate_image(prompt: str, dest_path: str, retries: int = 2) -> bool:
    encoded = urllib.parse.quote(prompt)
    seed = random.randint(1, 999999)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width={W}&height={H}&nologo=true&seed={seed}"

    for attempt in range(retries + 1):
        try:
            resp = requests.get(url, timeout=60)
            resp.raise_for_status()
            if len(resp.content) < 5000:
                raise ValueError("이미지가 너무 작아 생성 실패로 간주")
            with open(dest_path, "wb") as f:
                f.write(resp.content)
            return True
        except Exception as e:
            print(f"이미지 생성 시도 {attempt + 1} 실패: {e}")
            time.sleep(3)
    return False


def generate_all_images() -> list:
    with open(SCRIPT_PATH, "r", encoding="utf-8") as f:
        script = json.load(f)

    os.makedirs(IMAGE_DIR, exist_ok=True)
    prompts = build_prompts(script)

    paths = []
    for i, prompt in enumerate(prompts):
        dest = os.path.join(IMAGE_DIR, f"ai_{i}.jpg")
        print(f"이미지 {i + 1}/{len(prompts)} 생성 중...")
        if generate_image(prompt, dest):
            paths.append(dest)
        else:
            print(f"이미지 {i + 1} 생성 실패, 건너뜁니다.")

    return paths


if __name__ == "__main__":
    result = generate_all_images()
    print(f"총 {len(result)}장의 AI 이미지 생성 완료")
