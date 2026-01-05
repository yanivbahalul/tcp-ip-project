# TCP/IP Network Protocol Implementation

## Installation
```bash
cd prt2
pip install -r requirements.txt

```

## Run Server
```bash
cd prt2
python gui/server_visual.py (cmd)
python3 gui/server_visual.py (bash)
```

השרת תומך ב-**5+ לקוחות בו-זמנית** (asyncio).

**או Server GUI המקורי:**
```bash
cd prt2
python gui/server_gui.py (cmd)
python3 gui/server_gui.py (bash)
```

## Run Client
```bash
cd prt2
python gui/client_gui.py (cmd)
python3 gui/client_gui.py (bash)
```

### Visual GUI Features

**Server Visual GUI:**
- תצוגה ויזואלית של כל הלקוחות המחוברים (עיגולים)
- קווים צהובים מחברים בין לקוחות שמצ'וטטים יחד
- תצוגה של קבוצות (מלבנים סגולים)
- קווים מקווקוים מחברים בין קבוצות לחבריהן

**Client GUI (includes Visual Network tab):**
- תצוגה ויזואלית של כל המשתמשים המחוברים (בטאב Visual Network)
- יצירת קבוצות וניהול קבוצות
- שליחת הודעות מקובץ CSV
- סטטיסטיקות וגרפים
- ייצוא לוגים וסטטיסטיקות

### Commands (Text-based)
1. **LIST_USERS** - רשימת כל המשתמשים המחוברים
2. **LIST_GROUPS** - רשימת כל הקבוצות
3. **CONNECT:name** - התחבר למשתמש אחר (צ'אט אחד-על-אחד)
4. **CREATE_GROUP:name** - צור קבוצה חדשה
5. **JOIN_GROUP:name** - הצטרף לקבוצה
6. **LEAVE_GROUP:name** - צא מקבוצה
7. **GROUP:group_name:message** - שלח הודעה לקבוצה

### Chat Usage
1. **Connect to server**: Enter your name and click "Connect"
2. **Open chat**: In "Send Single Message" field, type `CONNECT:name` (e.g., `CONNECT:Bob`) and click "Send"
3. **Send messages**: Type your message in "Send Single Message" field and click "Send"
4. **Close chat**: Disconnect from server or connect to another client
