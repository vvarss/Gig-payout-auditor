# Gig-payout-auditor

# Trip Payout Checker

This project is mainly used to check the rightful payment for each trip made by the delivery servicemen/servicewomen.
The project is mainly designed to read the costs from the screenshots, calculate the cost and the inconsistencies, and draft a polite message to support. It flags the things worth asking about.It never claims anyone cheated.


> Built by Varshini S as an individual project for the Touchcast India AI Solutions Architect internship assessment.

# The Problem
Delivery riders get an earnings screen after every trip, but nobody checks a whole week for consistency: do the parts add up, was one trip paid far below the usual rate, did a long trip miss the return pay that similar trips got? Doing this by hand is slow and boring, so mistakes go unnoticed.

## How it works
 
```
Screenshots -> read numbers (OCR or Claude vision) -> checks (plain Python) -> explanation + message
```

1. **Read** (`extract.py`, `extract_ocr.py`): turns each screenshot into numbers. Default is a free, offline OCR reader (RapidOCR). Claude vision is available as an alternative when API credit exists.
2. **Check** (`checks.py`): deterministic Python, no AI, so arithmetic is never "guessed":
   - **Sum check:** trip pay + return pay must equal the total shown (5 paise tolerance).
   - **Rate check:** flags trips paid more than 25% below the median pay per km.
   - **Return-pay check:** learns the shortest trip that received return pay, then flags longer trips with none.
3. **Explain** (`explain.py`): a built-in template, or Claude (English/Tamil) when enabled. If Claude fails, it falls back to the template.
4. **Screen** (`app.py`): Streamlit app with a sample mode and an upload mode.


### Why this design
- Code does the math because it is exact and testable. AI/OCR is used for reading and wording.
- The extractor is swappable: free OCR by default, Claude vision as an option.
- Checks only flag; the wording is always "looks inconsistent, worth asking about."
## Test data and results
No real rider data is used. `generate_data.py` draws 30 fake trip screens from a pay formula I control (including blurry/tilted ones) and writes a separate answer key with 5 planted errors: 2 missing return-pay lines, 2 totals that don't match their parts, and 1 trip paid far below the normal rate.
 
| Measure | Result |
|---|---|
| Screens read correctly (OCR) | [FILL: e.g. 30 of 30] |
| Planted errors caught | [FILL: e.g. 5 of 5] |
| False alarms on normal trips | [FILL: e.g. 0 of 25] |
| Harder test (NOISE = 0.08) | [FILL: what was caught / missed] |
 
Reproduce: `python generate_data.py`, `python extract.py ocr`, `python checks.py ocr`.
 
## Run it (Windows, Python 3.12 or 3.13)
 
```powershell
git clone [YOUR REPO LINK]
cd gig-payout-auditor
py -3.12 -m venv venv
venv\Scripts\activate
python -m pip install anthropic streamlit pandas pillow rapidocr-onnxruntime
python generate_data.py
streamlit run app.py
```
 
Optional, for Claude vision or Claude explanations: set `ANTHROPIC_API_KEY` in your terminal. Never put the key in a file.
 
## Project structure
 
```
app.py            Streamlit screen
extract.py        screenshot -> numbers (engine switch: ocr / claude)
extract_ocr.py    free offline reader
checks.py         the three checks + scoring against the answer key
explain.py        explanation + draft message
generate_data.py  synthetic screenshots + answers.json
```
 
## Honest Limits
- Tested on synthetic data and one real screenshot layout; real phone photos, glare and other apps' layouts are untested.
- The OCR parser is tuned to this screen's labels. Other apps need label changes in `extract_ocr.py`.
- Pay can legitimately vary (peak hours, pickup distance, incentives). A flag is a question to ask, not proof of an error.
- The rate check needs roughly 8+ trips to be meaningful.
## Future work
Weekly payout reconciliation, duplicate-trip detection, a regression on pay vs. distance and time, Tamil support in the template, a second screen layout (restaurant payouts).
 
## AI tools used
- **Claude (chat):** [FILL: be specific, e.g. helped design the architecture, wrote the first versions of the scripts, helped debug install problems. Then list what YOU did: chose the problem, decided the checks, ran and tuned tests, made the commits.]
- **RapidOCR:** offline screenshot reading.
- **Claude API (optional in the app):** vision extraction and English/Tamil explanations when credit is available.
- **Streamlit, pandas, Pillow:** UI, tables, synthetic image generation.
 
