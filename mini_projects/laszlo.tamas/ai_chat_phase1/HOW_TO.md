# AI Chat Phase 1 - Használati Útmutató

## 🎯 Program Célja
Multi-user chat alkalmazás OpenAI integrációval, amely képes:
- Felhasználók kezelésére
- Beszélgetési előzmények tárolására
- Nyelvspecifikus válaszok generálására
- Debug információk megjelenítésére

## 🚀 Gyors Kezdés

### 1. Konténerek Indítása
```bash
docker-compose up -d
```

### 2. Alkalmazás Elérése
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 👤 Teszt Felhasználók

### Alice Johnson (ID: 1)
- **Becenév**: alice_j
- **Nyelv**: Magyar (hu)
- **Szerepkör**: Developer
- **Állapot**: Aktív
- 💡 Az LLM magyarul válaszol neki

### Bob Smith (ID: 2)
- **Becenév**: bob_s
- **Nyelv**: Angol (en)
- **Szerepkör**: Manager
- **Állapot**: Aktív
- 💡 Az LLM angolul válaszol neki

### Charlie Davis (ID: 3)
- **Becenév**: charlie_d
- **Nyelv**: Angol (en)
- **Szerepkör**: Analyst
- **Állapot**: ❌ Inaktív
- 💡 Nem tud chatben részt venni

## 🧪 Tesztelési Lépések

### Alapműködés Tesztelése
1. **Felhasználó választás**: Válaszd ki Alice-t a dropdown-ból
2. **Üzenet küldés**: Írj be egy kérdést magyarul
3. **Válasz ellenőrzés**: Az LLM magyarul válaszol
4. **Váltás**: Válts Bob-ra, írj angolul
5. **Nyelvi kontextus**: Az LLM angolul válaszol

### Memória Tesztelése
1. Kérdezd meg: "Mi a nevem?"
2. Említs valamit: "Szeretek programozni Python-ban"
3. Később kérdezd: "Miről beszélgettünk korábban?"
4. Az LLM emlékezik az utolsó **10 üzenetváltásra**

### Inaktív Felhasználó
1. Válaszd Charlie-t
2. Próbálj üzenetet küldeni
3. Hibaüzenet jelenik meg (inaktív felhasználó)

## 🐛 Debug Funkciók

### Debug Ablak Megnyitása
- Kattints a **🐛 Debug** gombra jobb felül
- Csak akkor látható, ha ki van választva felhasználó

### Mit Látsz a Debug Ablakban?

#### 📊 Felhasználói Adatok
- User ID, név, becenév
- Email, szerepkör
- **Nyelv beállítás** (default_lang)
- Aktív státusz
- Létrehozás dátuma

#### 🤖 AI Összefoglaló
- LLM által generált összefoglaló
- Mit tud a felhasználóról a beszélgetések alapján
- Érdeklődési körök, témák

#### 💬 Utolsó 10 Üzenetváltás
- Időpont
- Felhasználó üzenete
- Asszisztens válasza
- Fordított sorrend (legújabb alul)

## 🗑️ Előzmények Törlése
*Figyelem: Ez a funkció fejlesztés alatt áll*

## 📊 Működési Folyamat

### Üzenet Feldolgozása
```
1. User kiválasztása → Session ID generálása/betöltése
2. Üzenet beírása → Backend API hívás
3. User validáció → Aktív státusz ellenőrzés
4. Előzmények betöltése → Utolsó 20 üzenet (10 váltás)
5. LLM Context építése → System prompt + user info + history
6. OpenAI API hívás → gpt-3.5-turbo model
7. Válasz mentése → SQLite adatbázis
8. Megjelenítés → Frontend
```

### Adatbázis Struktúra
- **users**: Felhasználói adatok
- **chat_sessions**: Beszélgetési sessionök
- **chat_messages**: Üzenetek (event log)

### LLM Context
```
System Prompt:
- AI asszisztens szerepe
- User alapadatok (név, email, szerepkör)
- Nyelvi preferencia (hu/en) ← FONTOS: Az LLM ezen alapul válaszol!
- Környezet (teszt mód)

Beszélgetési előzmények:
- Utolsó 10 üzenetváltás
- Időrendi sorrend

Aktuális üzenet:
- User legfrissebb kérdése
```

### Nyelvi Támogatás
- **default_lang** mező a users táblában
- Alice (ID: 1): **hu** → Magyar válaszok
- Bob (ID: 2): **en** → Angol válaszok
- Charlie (ID: 3): **en** → Angol válaszok (de inaktív)
- Az LLM context automatikusan tartalmazza a nyelvi preferenciát

## 💡 Tippek az Oktatáshoz

### 1. Nyelvváltás Demonstrálása
- Váltogass Alice (magyar) és Bob (angol) között
- Ugyanazt a kérdést tedd fel mindkettőnek
- Figyeld meg a nyelvi különbséget

### 2. Memória Demonstrálása
- Alice-szal beszélgess 5-6 üzenetváltást
- Kérdezd: "Összefoglalnád, miről beszéltünk?"
- Nyisd meg a Debug ablakot → AI összefoglaló

### 3. Session Persistence
- Beszélgess Alice-szal
- Frissítsd az oldalt (F5)
- Válaszd újra Alice-t
- Az előzmények visszatöltődnek

### 4. Debug Ablak Használata
- Beszélgetés közben nyisd meg
- Nézd meg, mit tud rólad az LLM
- Ellenőrizd az utolsó üzeneteket
- Hasonlítsd össze az AI összefoglalót a valósággal

## 🔧 Hibaelhárítás

### Backend nem indul
```bash
docker-compose logs backend
```

### Frontend nem tölti be a usereket
- Ellenőrizd: http://localhost:8000/api/users
- Nézd meg a browser console-t (F12)

### LLM nem válaszol
- Ellenőrizd az OPENAI_API_KEY environment változót
- Nézd a backend logokat

### Adatbázis reset
```bash
docker-compose down
rm backend/chat_app.db
docker-compose up -d
```

## �️ Előzmények Törlése

### Debug Ablakból
1. Nyisd meg a **🐛 Debug** ablakot
2. Ha vannak üzenetek, jobb felül megjelenik a **🗑️ Előzmények törlése** gomb
3. Kattintásra megerősítő popup:
   - "Biztosan törölni akarod az összes beszélgetési előzményt?"
   - "Ez a művelet nem vonható vissza!"
4. **OK** esetén:
   - Törlődik az adatbázisból az összes üzenet
   - Törlődik az adatbázisból az összes session
   - Debug ablak frissül (nincs több üzenet)
   - Chat ablak kiürül
5. **Mégse** esetén: Semmi nem történik

⚠️ **Figyelem**: A törlés végleges és csak az adott felhasználóra vonatkozik!

## �📝 Továbbfejlesztési Ötletek
- ~~Előzmények törlése gomb implementálása~~ ✅ Kész
- Chat export funkció
- Üzenet szerkesztése/törlése
- Fájl feltöltés
- Markdown renderelés az üzenetekben
- User profil szerkesztés
- Chat témák/kategóriák
