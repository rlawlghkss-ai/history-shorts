"""
data/topic.json 의 위키백과 이벤트를 바탕으로
60초 쇼츠용 대본(훅+본문+마무리)과 제목/설명/태그를 만들어
data/script.json 으로 저장한다.

무료로 동작하도록 LLM API 없이 템플릿 기반으로 문장을 재구성한다.
(위키백과 원문을 그대로 읽지 않고, 핵심 사실만 뽑아 새로 문장을 쓴다)

topic.json의 사실 문장은 영어 위키백과에서 온 것이라, 무료 번역기
(deep-translator, 구글 번역 비공식 무료 래퍼)로 한국어로 옮긴 뒤 사용한다.
"""
import json
import os
import re

from deep_translator import GoogleTranslator

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOPIC_PATH = os.path.join(BASE_DIR, "data", "topic.json")
SCRIPT_PATH = os.path.join(BASE_DIR, "data", "script.json")

HOOK_TEMPLATES = [
    "오늘, {year}년 이 날 벌어진 사건 하나를 아시나요?",
    "역사 속 오늘, {year}년에는 이런 일이 있었습니다.",
    "{year}년 오늘, 세계사가 이렇게 바뀌었습니다.",
]

OUTRO_TEMPLATES = [
    "역사 속 오늘 이야기, 다음 편도 기대해주세요.",
    "매일 하나씩, 세계사 속으로 함께 떠나봐요.",
    "오늘의 역사, 여기까지입니다. 내일 또 만나요.",
]


def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text


def translate_to_korean(text: str) -> str:
    try:
        return GoogleTranslator(source="en", target="ko").translate(text)
    except Exception as e:
        print(f"번역 실패, 원문 그대로 사용: {e}")
        return text


def build_script(topic: dict) -> dict:
    year = topic.get("year") or "역사 속"
    fact_en = clean_text(topic["text"])
    fact = translate_to_korean(fact_en)

    hook = HOOK_TEMPLATES[abs(hash(topic["key"])) % len(HOOK_TEMPLATES)].format(year=year)
    outro = OUTRO_TEMPLATES[abs(hash(topic["key"]) // 7) % len(OUTRO_TEMPLATES)]

    body = fact
    if not body.endswith((".", "!", "?", "다")):
        body += "."

    full_script = f"{hook} {body} {outro}"

    title_topic_en = topic.get("display_title")
    title_topic = translate_to_korean(title_topic_en) if title_topic_en else fact[:18]
    title = f"{year}년 오늘, {title_topic} #shorts #세계사 #역사"
    if len(title) > 95:
        title = title[:92] + "..."

    description = (
        f"{fact}\n\n"
        f"매일 아침 9시, 세계사 속 오늘의 사건을 1분으로 만나보세요.\n"
        f"#세계사 #오늘의역사 #shorts #history"
    )

    tags = ["세계사", "오늘의역사", "역사", "shorts", "쇼츠", "history", "onthisday"]

    script = {
        "key": topic["key"],
        "narration": full_script,
        "hook": hook,
        "body": body,
        "outro": outro,
        "title": title,
        "description": description,
        "tags": tags,
        "thumbnail_url": topic.get("thumbnail_url"),
    }

    os.makedirs(os.path.dirname(SCRIPT_PATH), exist_ok=True)
    with open(SCRIPT_PATH, "w", encoding="utf-8") as f:
        json.dump(script, f, ensure_ascii=False, indent=2)

    print("생성된 대본:")
    print(full_script)
    return script


if __name__ == "__main__":
    with open(TOPIC_PATH, "r", encoding="utf-8") as f:
        topic = json.load(f)
    build_script(topic)
