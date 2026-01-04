# Database Storage (Local Files)

Ez a mappa tartalmazza a **helyi adatbázis fájlokat** az oktatási verzióhoz.

## 📁 Struktúra

```
data/
├── postgres/     # PostgreSQL adatbázis fájlok
│   ├── base/     # Táblák, indexek
│   ├── global/   # Globális táblák
│   └── pg_wal/   # Write-Ahead Log
└── qdrant/       # Qdrant vector database fájlok
    └── storage/  # Embedded vectorok, kollekciók
```

## ✅ Előnyök (Oktatási Cél)

1. **Látható adatok**: Az oktató és a diák is látja a DB tartalmát
2. **Hordozható**: Projekt másolás = adatok másolása
3. **Debugolható**: Könnyű megnézni, mi van az adatbázisban
4. **Seed adatok**: Git-ben tárolhatók példa adatok

## 🔄 Seed Adatok (Auto-loaded)

Amikor először indítod a projektet:

**PostgreSQL:**
- 4 tenant (ACME Corp, TechStart Inc, Global Solutions, Inactive Corp)
- 3 user (Alice Johnson, Bob Smith, Charlie Davis)
- Üres dokumentum és chat táblák

**Qdrant:**
- Üres kollekciók (létrejönnek első document upload-nál)

## 🧹 Tisztítás

### Teljes reset (üres DB):
```powershell
# Windows
.\reset.ps1

# Vagy manuálisan:
docker-compose down
Remove-Item -Recurse -Force data/postgres/*
Remove-Item -Recurse -Force data/qdrant/*
docker-compose up -d
```

### Git workflow:
```bash
# Első indítás után, seed adatokkal:
git add data/
git commit -m "Add seed database files for education"

# Később, ha változtattál és vissza akarod állítani:
git checkout -- data/
```

## 📊 Méret

Üres DB (csak seed adatokkal):
- PostgreSQL: ~40-50 MB
- Qdrant: ~1-5 MB

Néhány dokumentum feltöltése után:
- PostgreSQL: +10-20 MB / 100 chunk
- Qdrant: +5-10 MB / 100 embedded chunk

## ⚠️ Fontos

- **NE szerkeszd kézzel** a fájlokat (használd a Docker containereket)
- **Git-ben maradhat** oktatási célból (diákok is megkapják)
- **Production verzióban** nincs ilyen mappa (managed services)

## 🎓 Oktatási Megjegyzés

Ez a megoldás **csak az edu verzióra** vonatkozik. A production verzióban (ai_chat_prod_v02) Railway PostgreSQL és Qdrant Cloud van, **nem** helyi fájlok.
