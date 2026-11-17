"""
extract_ocr.py  --  FREE alternative to Claude vision. Runs on your own computer.

It uses OCR (a program that reads text from pictures), then finds each number by
looking at the label on the same row: "Trip pay ........ 120.83".

Works best on clean screenshots. Blurry or very tilted photos may fail; that's the
trade-off for being free and offline.
"""
import re

_ocr = None


def _get_ocr():
    global _ocr
    if _ocr is None:
        from rapidocr_onnxruntime import RapidOCR   # imported here so the app starts fast
        _ocr = RapidOCR()
    return _ocr


def _number(text):
    """Pull the number out of text like '₹221.85' or '23.3 kms' (the ₹ is often misread)."""
    m = re.findall(r"\d[\d,]*\.?\d*", text.replace(" ", ""))
    if not m:
        return None
    try:
        return float(m[-1].replace(",", ""))
    except ValueError:
        return None


def extract_one_ocr(path):
    result, _ = _get_ocr()(path)
    items = []
    for box, text, _conf in (result or []):
        y = sum(p[1] for p in box) / 4
        x = sum(p[0] for p in box) / 4
        items.append({"x": x, "y": y, "text": text.strip(), "low": text.lower()})

    def value_on_row(label_key, must_not=()):
        """Find the label, then the number to its right on the same row."""
        labels = [i for i in items
                  if label_key in i["low"] and not any(b in i["low"] for b in must_not)]
        if not labels:
            return None
        lab = labels[0]
        same_row = [i for i in items
                    if i is not lab and abs(i["y"] - lab["y"]) < 28 and i["x"] > lab["x"]]
        for cand in sorted(same_row, key=lambda i: i["x"]):
            n = _number(cand["text"])
            if n is not None:
                return n
        return None

    # The big total sits just under the "Trip earnings" heading.
    total = None
    head = [i for i in items if "trip earnings" in i["low"]]
    if head:
        below = sorted((i for i in items if i["y"] > head[0]["y"]), key=lambda i: i["y"])
        for cand in below:
            n = _number(cand["text"])
            if n is not None:
                total = n
                break

    return {
        "total_earnings": total,
        "trip_pay": value_on_row("trip pay"),
        "long_distance_return_pay": value_on_row("return pay"),
        "distance_km": value_on_row("trip distance"),
        "trip_time_mins": value_on_row("trip time"),
    }
