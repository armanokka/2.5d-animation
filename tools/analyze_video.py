#!/usr/bin/env python3
"""Разбор референс-ролика через Gemini (OpenRouter).

Использование:
    export OPENROUTER_API_KEY=sk-or-...
    python3 tools/analyze_video.py path/to/video.mp4 [-o analysis/video.md]

Ключ берётся только из переменной окружения — не коммитьте его.
"""
import argparse
import base64
import json
import os
import pathlib
import sys
import urllib.request

MODEL = "google/gemini-3.1-pro-preview"
URL = "https://openrouter.ai/api/v1/chat/completions"

PROMPT = """Ты — моушн-дизайнер. Разбери этот вертикальный YouTube Shorts в стиле
"Hoodie Guy / WhyGuyStories" (2.5D: мультяшная голова на реалистичном/ИИ теле и фоне)
так, чтобы по разбору можно было пересобрать ролик в After Effects.

Дай ответ в двух частях.

ЧАСТЬ 1 — стиль (markdown):
- персонаж: как устроена голова (рисованная/векторная), как сшита с телом, эмоции, рот, моргание;
- фоны: тип (фото/ИИ), глубина, параллакс, размытие, камера (зумы, пуш-ины, тряска, motion blur);
- переходы между кадрами и их длительность, ритм смены кадров;
- субтитры: шрифт, размер, обводка/тень, позиция, по одному слову или фразами, анимация появления;
- счётчик пунктов (кружок с номером): позиция, вид, анимация;
- вотермарка, эффекты (glow, shake, speed lines, сердечки, Zzz и т.п.);
- звук: голос (тон, темп), музыка, SFX (whoosh, pop, удары) и где они стоят.

ЧАСТЬ 2 — покадровый монтажный лист в JSON (массив) внутри блока ```json:
[{"start": 0.0, "end": 1.4, "fact_number": null, "voiceover": "...",
  "background": "...", "character": {"pose": "...", "emotion": "...", "mouth": "talk|closed|open"},
  "props": ["..."], "camera": "...", "transition_in": "...", "sfx": ["..."],
  "image_prompt": "промпт для генерации фона/тела этого кадра"}]
Таймкоды — в секундах, по реальным склейкам."""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("-o", "--out")
    ap.add_argument("--model", default=MODEL)
    args = ap.parse_args()

    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        sys.exit("OPENROUTER_API_KEY не задан")

    video = pathlib.Path(args.video)
    data_url = "data:video/mp4;base64," + base64.b64encode(video.read_bytes()).decode()
    body = {
        "model": args.model,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": PROMPT},
                {"type": "video_url", "video_url": {"url": data_url}},
            ],
        }],
    }
    req = urllib.request.Request(
        URL,
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=600) as resp:
        result = json.load(resp)
    text = result["choices"][0]["message"]["content"]

    out = pathlib.Path(args.out or f"analysis/{video.stem}.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text)
    print(f"Сохранено: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
