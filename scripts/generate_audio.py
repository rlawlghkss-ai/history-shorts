"""
Microsoft Edge의 무료 TTS 엔진(edge-tts, 비공식 라이브러리, API 키 불필요)으로
대본을 음성(mp3)으로 변환하고, 단어 타이밍 정보를 이용해 자막(.srt)까지 만든다.

한국어 음성: ko-KR-SunHiNeural (여성) / ko-KR-InJoonNeural (남성) 중 선택 가능
"""
import asyncio
import json
import os

import edge_tts

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT_PATH = os.path.join(BASE_DIR, "data", "script.json")
AUDIO_PATH = os.path.join(BASE_DIR, "data", "audio.mp3")
SRT_PATH = os.path.join(BASE_DIR, "data", "subtitles.srt")

VOICE = os.environ.get("TTS_VOICE", "ko-KR-SunHiNeural")
RATE = os.environ.get("TTS_RATE", "+0%")


def ms_to_srt_time(ms: float) -> str:
    total_ms = int(ms)
    hours = total_ms // 3600000
    minutes = (total_ms % 3600000) // 60000
    seconds = (total_ms % 60000) // 1000
    millis = total_ms % 1000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


async def synthesize(text: str):
    communicate = edge_tts.Communicate(text, VOICE, rate=RATE)
    submaker = edge_tts.SubMaker()

    with open(AUDIO_PATH, "wb") as audio_file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                submaker.feed(chunk)

    # 단어 단위 자막을 4~6단어씩 묶어 자연스러운 캡션 라인으로 재구성
    cues = submaker.cues
    lines = []
    buffer_words = []
    buffer_start = None
    for cue in cues:
        if buffer_start is None:
            buffer_start = cue.start
        buffer_words.append(cue.content)
        if len(buffer_words) >= 5:
            lines.append((buffer_start, cue.end, " ".join(buffer_words)))
            buffer_words = []
            buffer_start = None
    if buffer_words:
        lines.append((buffer_start, cues[-1].end, " ".join(buffer_words)))

    with open(SRT_PATH, "w", encoding="utf-8") as f:
        for i, (start, end, content) in enumerate(lines, start=1):
            f.write(f"{i}\n")
            f.write(f"{ms_to_srt_time(start / 10000)} --> {ms_to_srt_time(end / 10000)}\n")
            f.write(f"{content}\n\n")

    print(f"오디오 저장: {AUDIO_PATH}")
    print(f"자막 저장: {SRT_PATH}")


if __name__ == "__main__":
    with open(SCRIPT_PATH, "r", encoding="utf-8") as f:
        script = json.load(f)
    asyncio.run(synthesize(script["narration"]))
