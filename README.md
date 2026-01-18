# TCP/IP Network Protocol Implementation

פרויקט צ'אט מבוסס TCP/IP עם ממשק גרפי (GUI).

## Installation
```bash
cd prt2
pip install -r requirements.txt
```

## Run Server
```bash
cd prt2
python server_gui.py
```
או:
```bash
cd prt2
python3 server_gui.py
```

השרת תומך ב-**מספר לקוחות בו-זמנית** ומנהל את כל החיבורים.

**הגדרת השרת:**
- **Binding IP Address**: הכנס `0.0.0.0` כדי לאפשר חיבורים מכל כתובת IP ברשת, או `127.0.0.1` רק ל-localhost
- **Listening Port**: ברירת מחדל `10000`

## Run Client
```bash
cd prt2
python client_gui.py
```
או:
```bash
cd prt2
python3 client_gui.py
```

**הגדרת הלקוח:**
- **Nickname**: הכנס את השם שלך
- **Server IP**: הכנס את כתובת ה-IP של השרת (לדוגמה: `127.0.0.1` ל-localhost או `10.0.0.12` לשרת ברשת)
- **Port**: הכנס את הפורט של השרת (ברירת מחדל `10000`)

## Usage

1. **הפעל את השרת**: הרץ את `server_gui.py` והקש על "RUN SERVER"
2. **התחבר כקליינט**: הרץ את `client_gui.py`, הכנס שם משתמש וכתובת שרת, והקש "LOGIN"
3. **בחר משתמש**: בחר משתמש מהרשימה בצד שמאל
4. **שלח הודעות**: הקלד הודעה והקש "SEND" או Enter
5. **קבל הודעות**: הודעות נכנסות יוצגו אוטומטית בצ'אט

## Network Configuration

**לחיבור ברשת מקומית:**
- במחשב השרת: הכנס `0.0.0.0` ב-Binding IP Address
- במחשב הלקוח: הכנס את כתובת ה-IP של מחשב השרת

**לחיבור מקומי (localhost):**
- במחשב השרת: הכנס `127.0.0.1` או `0.0.0.0`
- במחשב הלקוח: הכנס `127.0.0.1`
