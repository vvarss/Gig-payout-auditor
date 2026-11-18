"""
eval_ocr.py -- how many screenshots did the reader get completely right?

Compares data/extracted_ocr.json (what OCR read) with data/synthetic/answers.json
(the truth). Run:  python eval_ocr.py
"""
import json

with open("data/extracted_ocr.json", encoding="utf-8") as f:
    read = json.load(f)
with open("data/synthetic/answers.json", encoding="utf-8") as f:
    truth = {r["file"]: r for r in json.load(f)}

fields = {                      # name in OCR output -> name in answer key
    "total_earnings": "shown_total",
    "trip_pay": "shown_trip_pay",
    "long_distance_return_pay": "shown_return_pay",
    "distance_km": "km",
    "trip_time_mins": "mins",
}

correct = 0
for name, t in truth.items():
    r = read.get(name)
    if r is None:
        print(f"NOT READ  {name}")
        continue
    wrong = [(k, r.get(k), t[v]) for k, v in fields.items() if r.get(k) != t[v]]
    if wrong:
        for k, got, want in wrong:
            print(f"MISREAD   {name}: {k} read as {got}, should be {want}")
    else:
        correct += 1

print(f"\nScreens read completely correctly: {correct} of {len(truth)}")
