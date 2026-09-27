
# Clip2English — Mobile edition

A small mobile-first web app that turns a YouTube clip into an English lesson.

## What it does
- Accepts a YouTube link.
- Tries to download English subtitles.
- Selects useful spoken-English sentences.
- Shows timestamp buttons that jump back into the video.
- Reads sentences aloud with the phone's British-English text-to-speech voice when available.
- Includes a simple recall/practice box.
- Falls back to a pasted transcript when subtitles cannot be fetched.
- Can be installed to the Android home screen as a PWA after it is hosted over HTTPS.

## Run on a computer
1. Install Python 3.11+.
2. Open a terminal in this folder.
3. Run:

   pip install -r requirements.txt
   python app.py

4. Open http://127.0.0.1:5000

## Use it from your Android phone
The easiest route is to host this folder on a Python web host such as Render, Railway,
or another service that can run `gunicorn app:app`.

After deployment:
1. Open the HTTPS address in Chrome on Android.
2. Use the browser menu and choose "Add to Home screen" / "Install app".
3. It then behaves much like a normal mobile app.

## Important limitation
YouTube can block subtitle requests from some hosting providers or for some videos.
If that happens, paste the transcript into the fallback box.

## Notes
This first mobile version deliberately does not require an AI API key.
That makes it cheaper and simpler. A later version can add:
- Polish translations
- AI explanations
- vocabulary grading
- spaced repetition
- user accounts and progress
- pronunciation feedback
