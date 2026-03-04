# מערכת חניון חכמה – RAG

תיעוד קצר להפעלה ופיתוח של המערכת בתיקייה הזו.

## מה יש בפרויקט
- `workflow_system.py` – ממשק צ׳אט מבוסס Gradio עם ניתוב בין JSON ל‑Pinecone.
- `main.py` – דוגמת בניית אינדקס מול תיקיית מסמכים חיצונית.
- `parking_data.json` – נתונים קשיחים (למשל תעריפים/שעות) עבור שליפה ישירה.
- `workflow_flowchart.html` – תרשים זרימה אינטראקטיבי של ה‑Workflow (Mermaid).

## דרישות מוקדמות
- Python 3.10+ מומלץ
- חשבונות ומפתחות ל‑Cohere ול‑Pinecone

## הגדרת סביבה
צרו קובץ `.env` בתיקיית הפרויקט והוסיפו:
```
COHERE_API_KEY=your_key_here
PINECONE_API_KEY=your_key_here
```

## התקנת תלות
הפרויקט משתמש בספריות הבאות (ע״פ הקוד):
- `gradio`
- `pinecone-client`
- `llama-index`
- `llama-index-vector-stores-pinecone`
- `llama-index-embeddings-cohere`
- `llama-index-llms-cohere`
- `python-dotenv`

דוגמת התקנה:
```powershell
pip install gradio pinecone-client llama-index llama-index-vector-stores-pinecone llama-index-embeddings-cohere llama-index-llms-cohere python-dotenv
```

## הפעלה (מומלץ)
הפעלת המערכת עם הניתוב בין JSON ל‑Pinecone:
```powershell
python workflow_system.py
```

## הערות לגבי `main.py`
`main.py` מנסה לקרוא מסמכים מתוך הנתיב `../parking_system`. אם הנתיב לא קיים אצלך, עדכן את `input_dir` או צור תיקייה מתאימה.

## תקלות נפוצות
- **חסר מפתח API** – ודא שיש קובץ `.env` ושמפתחות קיימים.
- **שגיאה ב‑Pinecone Index** – ודא שה‑index בשם `parking-index` קיים בחשבון שלך.
- **טעינת מסמכים ב‑main.py** – ודא שהנתיב לתיקיית המסמכים נכון.
