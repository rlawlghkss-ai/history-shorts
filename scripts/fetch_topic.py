"""
오늘 날짜의 '역사 속 오늘' 이벤트를 영어 위키백과 REST API에서 가져와
아직 다루지 않은 주제를 하나 골라 data/topic.json 으로 저장한다.
(한국어 위키백과는 이 기능을 지원하지 않아서 영어판을 쓰고, 대본 생성 단계에서
 무료 번역기로 한국어로 옮긴다)

API는 무료이며 키가 필요 없다.
https://en.wikipedia.org/api/rest_v1/feed/onthisday/events/{month}/{day}
"""
import json
import os
import random
import sys
from datetime import datetime, timezone, timedelta

import requests

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USED_TOPICS_PATH = os.path.join(BASE_DIR, "data", "used_topics.json")
TOPIC_OUTPUT_PATH = os.path.join(BASE_DIR, "data", "topic.json")

KST = timezone(timedelta(hours=9))


def load_used_topics():
    if not os.path.exists(USED_TOPICS_PATH):
        return []
    with open(USED_TOPICS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_used_topics(used):
    os.makedirs(os.path.dirname(USED_TOPICS_PATH), exist_ok=True)
    with open(USED_TOPICS_PATH, "w", encoding="utf-8") as f:
        json.dump(used, f, ensure_ascii=False, indent=2)


def fetch_events(month: int, day: int):
    url = f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/events/{month:02d}/{day:02d}"
    headers = {"User-Agent": "history-shorts-bot/1.0 (personal project)"}
    resp = requests.get(url, headers=headers, timeout=20)
    resp.raise_for_status()
    return resp.json().get("events", [])


def pick_topic():
    now_kst = datetime.now(KST)
    events = fetch_events(now_kst.month, now_kst.day)
    used = load_used_topics()
    used_keys = {u["key"] for u in used}

    candidates = [
        e for e in events
        if e.get("text") and len(e["text"]) >= 25
        and f"{e.get('year')}_{e['text'][:20]}" not in used_keys
    ]

    if not candidates:
        print("사용 가능한 새 주제가 없습니다. 오늘은 건너뜁니다.")
        sys.exit(2)

    random.shuffle(candidates)
    chosen = candidates[0]

    key = f"{chosen.get('year')}_{chosen['text'][:20]}"
    title = None
    page_title = None
    thumbnails = []
    pages = chosen.get("pages") or []
    for page in pages:
        thumb = page.get("thumbnail") or {}
        src = thumb.get("source")
        if src and src not in thumbnails:
            thumbnails.append(src)
    if pages:
        page_title = pages[0].get("title")
        title = pages[0].get("normalizedtitle") or pages[0].get("displaytitle")

    topic = {
        "key": key,
        "year": chosen.get("year"),
        "text": chosen["text"],
        "page_title": page_title,
        "display_title": title,
        "thumbnail_url": thumbnails[0] if thumbnails else None,
        "thumbnail_urls": thumbnails,
        "date_kst": now_kst.strftime("%Y-%m-%d"),
    }

    os.makedirs(os.path.dirname(TOPIC_OUTPUT_PATH), exist_ok=True)
    with open(TOPIC_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(topic, f, ensure_ascii=False, indent=2)

    used.append({"key": key, "date_used": now_kst.strftime("%Y-%m-%d")})
    save_used_topics(used)

    print(f"선택된 주제: {topic['year']}년 - {topic['text'][:40]}...")


if __name__ == "__main__":
    pick_topic()
