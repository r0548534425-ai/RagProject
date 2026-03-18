# RagProject – מערכת חניון חכמה (Agentic RAG)

פרויקט הדגמה לניהול ידע עבור מערכת חניון חכמה, עם ניתוב בין מידע “קשיח” (JSON) לחיפוש סמנטי (Pinecone) וממשק צ׳אט ב‑Gradio.

## מה המערכת עושה

המערכת מאפשרת לשאול שאלות על נהלים, תעריפים והחלטות טכניות של חניון חכם.
היא בוחרת מקור מידע מתאים:

- **JSON** – לתשובות קצרות, רשימות, חוקים והחלטות מדויקות.
- **Pinecone** – להסברים, רקע וניתוח סמנטי רחב.

התוצאה מוצגת בממשק צ׳אט מבוסס Gradio.

## מה יש כאן

- `workflow_system.py` – Workflow ראשי עם ניתוב בין JSON ל‑Pinecone.
- `main.py` – דוגמת אינדוקס מסמכים והפעלת ממשק צ׳אט.
- `parking_system/` – תיקיית מסמכים לדוגמה.
- `parking_data.json` – נתונים קשיחים לשליפה ישירה.
- `RAG/` – גרסה נוספת של הקוד (כולל Workflow ו‑Gradio).

## תרשים זרימה (בקצרה)

1. המשתמש שואל שאלה.
2. רכיב הניתוב מסווג את השאלה ל‑JSON או Pinecone.
3. מתבצע שליפה מהמקור המתאים.
4. המודל מסכם תשובה בהתאם להקשר שהתקבל.

## רכיבים מרכזיים

- **Routing** – סיווג שאלות לפי סוג מידע.
- **Retrieval** – שליפה מ‑JSON או Pinecone.
- **LLM Response** – ניסוח תשובה סופית.
- **UI** – ממשק צ׳אט ב‑Gradio.

## האם לשמור את הגרסה שמחוץ ל‑`RAG/`?

אם את עובדת רק עם הגרסה שבתיקיית `RAG/` (הגרסה המתקדמת), אפשר למחוק את הקבצים המקבילים בשורש כדי לצמצם בלבול.
עם זאת, כדאי להשאיר את הגרסה החיצונית אם את צריכה:

- גרסה פשוטה יותר להפעלה מהירה.
- נקודת השוואה/גיבוי לפני שינויים גדולים.
- בדיקת תקלות מול גרסה מינימלית.

המלצה: אם החלטת להתמקד ב‑`RAG/`, מחקי את הכפילויות בשורש ושמרי עותק גיבוי קודם.

## דרישות מוקדמות

- Python 3.10+ מומלץ
- חשבון ומפתחות API ל‑Cohere ול‑Pinecone

## הגדרת סביבה

צרו קובץ `.env` בשורש הפרויקט והוסיפו:

```
COHERE_API_KEY=your_key_here
PINECONE_API_KEY=your_key_here
```

## התקנת תלות

הפרויקט משתמש בספריות הבאות (לפי הקוד הקיים):

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

## הרצה מהירה

להפעלת ה‑Workflow הראשי:

```powershell
python workflow_system.py
```

אם רוצים להריץ את הגרסה שבתיקיית `RAG/`:

```powershell
python RAG\workflow_system.py
```

## איך נוצרים הנתונים ב‑JSON

ב‑`RAG/workflow_system.py` יש פונקציה `initialize_data_extraction()` שמחלצת מידע אוטומטית מקבצי הגדרות.
היא שומרת את המידע ב‑`parking_data.json` יחד עם מקור המסמך.

אם תעבירי את תיקיות `.cursor` / `.claudecode` לשורש הפרויקט, ודאי שהנתיבים שם מעודכנים בהתאם.

## נתיבים חשובים

- `main.py` ו‑`RAG/main.py` קוראים מסמכים מהנתיב `../parking_system` ביחס למיקום הקובץ.
	אם שינית מבנה תיקיות (למשל הזזת תקיות AI), עדכני את הנתיב בהתאם.
- `RAG/workflow_system.py` מחפש את תיקיות `.cursor` ו‑`.claudecode`. אם העברת אותן לשורש הפרויקט, כדאי לוודא שהנתיב מעודכן לשורש.

## התאמות מהירות שכדאי לדעת

- **שם ה‑Index ב‑Pinecone**: בקוד מופיע `parking-index`. אם אצלך שם אחר – צריך לעדכן.
- **הגדרת מודלים**: מוגדרים מודלי Cohere (`embed-multilingual-v3.0`, `command-r-08-2024`). אפשר לשנות לפי צורך.
- **סיווג שאלות**: ההנחיות לסיווג נמצאות ב‑`router_step` ב‑`workflow_system.py`.

## תקלות נפוצות

- **חסר מפתח API** – ודאי שקובץ `.env` קיים ובו המפתחות.
- **שגיאה ב‑Pinecone Index** – ודאי שה‑index בשם `parking-index` קיים בחשבון שלך.
- **טעינת מסמכים** – ודאי שהנתיב לתיקיית המסמכים נכון במשתנה `input_dir`.
