"""
extract.py  --  Step 1 of the pipeline: screenshot -> numbers.

What it does:
  1. Takes a screenshot of a trip-earnings screen.
  2. Sends it to Claude (which can "see" images) and asks for the numbers as JSON.
  3. Saves every result to data/extracted.json so you never pay twice
     for the same image.

How to run (terminal, venv active, ANTHROPIC_API_KEY set):
  python extract.py data/sample1.png     -> reads ONE image, prints the result
  python extract.py 3                    -> reads the first 3 images in data/synthetic
  python extract.py                      -> reads ALL images in data/synthetic
"""
import base64
import glob
import json
import os
import sys

import anthropic

MODEL = "claude-haiku-5-5"            # cheaper; switch to "claude-sonnet-5-5" if accuracy is poor
IMAGE_DIR = os.path.join("data", "synthetic")
CACHE_FILE = os.path.join("data", "extracted.json")

client = anthropic.Anthropic()        # reads ANTHROPIC_API_KEY from your terminal

PROMPT = """You are reading a screenshot of a delivery partner's trip earnings screen.
Return ONLY a JSON object, with no other text, using exactly these keys:

  total_earnings            (the big number at the top)
  trip_pay                  (the "Trip pay" row)
  long_distance_return_pay  (the "Long distance return pay" row; null if there is no such row)
  distance_km               (number only)
  trip_time_mins            (number only)

Rules:
- Numbers only: no rupee symbol, no commas, no units.
- If a value is not visible, use null. Never guess or calculate a value.
- Copy the numbers exactly as shown on the screen, even if they look wrong."""


def extract_one(path):
    """Send one image to Claude and return a dict of numbers."""
    with open(path, "rb") as f:
        img_b64 = base64.standard_b64encode(f.read()).decode()

    media_type = "image/jpeg" if path.lower().endswith((".jpg", ".jpeg")) else "image/png"

    message = client.messages.create(
        model=MODEL,
        max_tokens=500,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image",
                 "source": {"type": "base64", "media_type": media_type, "data": img_b64}},
                {"type": "text", "text": PROMPT},
            ],
        }],
    )
    text = message.content[0].text
    text = text.replace("```json", "").replace("```", "").strip()
    return json.loads(text)


def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(cache):
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)


def extract_many(paths):
    """Extract each image, skipping ones already saved in the cache."""
    cache = load_cache()
    for path in paths:
        name = os.path.basename(path)
        if name in cache:
            print(f"skip   {name} (already done)")
            continue
        try:
            cache[name] = extract_one(path)
            save_cache(cache)             # save after every image, so a crash loses nothing
            print(f"done   {name}: {cache[name]}")
        except Exception as e:
            print(f"FAILED {name}: {e}")
    return cache


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else None

    if arg and arg.lower().endswith((".png", ".jpg", ".jpeg")):
        # one specific image, just print it
        print(json.dumps(extract_one(arg), indent=2))
    else:
        files = sorted(glob.glob(os.path.join(IMAGE_DIR, "trip_*.png")))
        if arg and arg.isdigit():
            files = files[: int(arg)]
        if not files:
            print(f"No images found in {IMAGE_DIR}. Run generate_data.py first.")
        else:
            extract_many(files)
            print(f"\nSaved to {CACHE_FILE}")
