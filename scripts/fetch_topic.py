"""
오늘 날짜의 '역사 속 오늘' 이벤트를 한국어 위키백과 REST API에서 가져와
아직 다루지 않은 주제를 하나 골라 data/topic.json 으로 저장한다.

API는 무료이며 키가 필요 없다.
https://ko.wikipedia.org/api/rest_v1/feed/onthisday/events/{month}/{day}
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
    url = f"https://ko.wikipedia.org/api/rest_v1/feed/onthisday/events/{month:02d}/{day:02d}"
    headers = {"User-Agent": "history-shorts-bot/1.0 (personal project)"}
    resp = requests.get(url, headers=headers, timeout=20)
    resp.raise_for_status()
    return resp.json().get("events", [])


def pick_topic():
    now_kst = datetime.now(KST)
    events = fetch_events(now_kst.month, now_kst.day)
    used = load_used_topics()
    used_keys = {u["key"] for u in used}

    # 연도가 오래되고 설명이 충분히 긴 이벤트를 우선한다 (쇼츠 소재로 적합)
    candidates = [
        e for e in events
        if e.get("text") and len(e["text"]) >= 25
        and f"{e.get('year')}_{e['text'][:20]}" not in used_keys
    ]

    if not candidates:
        # 오늘자 새 소재가 없으면 예외 처리 — 워크플로우에서 스킵하도록 종료 코드로 신호
        print("사용 가능한 새 주제가 없습니다. 오늘은 건너뜁니다.")
        sys.exit(2)

    random.shuffle(candidates)
    chosen = candidates[0]

    key = f"{chosen.get('year')}_{chosen['text'][:20]}"
    title = None
    thumbnail = None
    page_title = None
    pages = chosen.get("pages") or []
    if pages:
        page = pages[0]
        page_title = page.get("title")
        title = page.get("normalizedtitle") or page.get("displaytitle")
        thumb = page.get("thumbnail") or {}
        thumbnail = thumb.get("source")

    topic = {
        "key": key,
        "year": chosen.get("year"),
        "text": chosen["text"],
        "page_title": page_title,
        "display_title": title,
        "thumbnail_url": thumbnail,
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
