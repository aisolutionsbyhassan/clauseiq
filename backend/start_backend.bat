call "C:\Users\Administrator\miniconda3\Scripts\activate.bat" genai
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
