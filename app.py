
from flask import Flask, render_template, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
import re
import html

app = Flask(__name__)

def extract_video_id(url_or_id: str) -> str:
    s = (url_or_id or "").strip()
    patterns = [
        r"(?:v=)([A-Za-z0-9_-]{11})",
        r"youtu\.be/([A-Za-z0-9_-]{11})",
        r"youtube\.com/shorts/([A-Za-z0-9_-]{11})",
        r"youtube\.com/embed/([A-Za-z0-9_-]{11})",
        r"^([A-Za-z0-9_-]{11})$",
    ]
    for p in patterns:
        m = re.search(p, s)
        if m:
            return m.group(1)
    raise ValueError("I couldn't recognise that YouTube link.")

def normalise(text: str) -> str:
    text = html.unescape(text or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text

def score_sentence(text: str) -> float:
    words = re.findall(r"[A-Za-z']+", text)
    n = len(words)
    if n < 3 or n > 18:
        return -999
    common = {
        "actually","really","just","still","already","probably","maybe","right",
        "think","know","want","need","have","get","got","going","come","look",
        "make","take","give","tell","mean","feel","work","good","sure","okay"
    }
    phrasal = {
        "get up","find out","go on","come on","pick up","look at","look for",
        "work out","turn out","give up","take off","put on","carry on"
    }
    low = text.lower()
    score = 0
    score += min(n, 12) * 0.5
    score += sum(1.3 for w in common if re.search(rf"\b{re.escape(w)}\b", low))
    score += sum(2.2 for p in phrasal if p in low)
    if "?" in text:
        score += 1.5
    if any(x in low for x in ["um", "uh", "[music]", "[applause]"]):
        score -= 4
    return score

def phrase_notes(text: str):
    low = text.lower()
    notes = []
    pairs = [
        ("going to", "very common way to talk about plans"),
        ("want to", "common way to express what you want"),
        ("have to", "means something is necessary"),
        ("get up", "phrasal verb: leave your bed / stand"),
        ("find out", "phrasal verb: discover information"),
        ("come on", "very common spoken expression; meaning depends on context"),
        ("pick up", "phrasal verb with several meanings, e.g. collect or learn"),
        ("work out", "phrasal verb: solve, calculate, or exercise"),
        ("turn out", "phrasal verb: result or prove to be"),
        ("carry on", "British English: continue"),
    ]
    for key, note in pairs:
        if key in low:
            notes.append({"phrase": key, "note": note})
    return notes[:3]

def build_lesson(segments):
    candidates = []
    seen = set()
    for seg in segments:
        text = normalise(seg["text"])
        if not text:
            continue
        # Split long subtitle chunks into natural-looking parts.
        parts = re.split(r"(?<=[.!?])\s+", text)
        for part in parts:
            p = part.strip()
            key = re.sub(r"[^a-z']+", " ", p.lower()).strip()
            if len(key) < 8 or key in seen:
                continue
            seen.add(key)
            sc = score_sentence(p)
            if sc > 0:
                candidates.append({
                    "text": p,
                    "start": round(float(seg.get("start", 0)), 1),
                    "score": sc,
                    "notes": phrase_notes(p)
                })
    candidates.sort(key=lambda x: x["score"], reverse=True)
    selected = candidates[:12]
    selected.sort(key=lambda x: x["start"])
    for i, item in enumerate(selected, 1):
        item["number"] = i
        item.pop("score", None)
    return selected

@app.get("/")
def index():
    return render_template("index.html")

@app.post("/api/lesson")
def lesson():
    payload = request.get_json(force=True, silent=True) or {}
    url = payload.get("url", "")
    manual = normalise(payload.get("transcript", ""))

    try:
        video_id = extract_video_id(url)
    except Exception as e:
        print(f"YOUTUBE ERROR: {type(e).__name__}: {e}", flush=True)
        if manual:
            video_id = ""
        else:
            return jsonify({"ok": False, "error": str(e)}), 400

    segments = []
    source = "manual transcript"

    if video_id:
        try:
            api = YouTubeTranscriptApi()
            transcript = api.fetch(video_id, languages=["en", "en-GB", "en-US"])
            segments = [
                {"text": s.text, "start": s.start, "duration": s.duration}
                for s in transcript
            ]
            source = "YouTube transcript"
        except Exception as e:
            if not manual:
                return jsonify({
                    "ok": False,
                    "error": "I couldn't fetch subtitles for this video. Paste the transcript below instead.",
                    "detail": str(e)
                }), 422

    if not segments and manual:
        # For manually pasted transcript we split into sentences and assign approximate order.
        parts = re.split(r"(?<=[.!?])\s+|\n+", manual)
        segments = [
            {"text": p.strip(), "start": i * 5.0, "duration": 5.0}
            for i, p in enumerate(parts) if p.strip()
        ]

    lesson_items = build_lesson(segments)
    if not lesson_items:
        return jsonify({"ok": False, "error": "I couldn't find enough useful English in that transcript."}), 422

    return jsonify({
        "ok": True,
        "video_id": video_id,
        "source": source,
        "items": lesson_items
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
