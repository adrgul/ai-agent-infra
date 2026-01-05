# Quick Start Guide

## 1. Környezet Beállítása

```bash
cd mini_projects/istvan.hadhazi/hf2
cp env.example .env
```

Szerkeszd a `.env` fájlt és add meg az OpenAI API kulcsod:
```env
OPENAI_API_KEY=sk-your-actual-key-here
```

## 2. Indítás Docker-rel

```bash
# Egyszerű indítás
make run

# Vagy manuálisan
docker-compose up -d qdrant
sleep 3
docker-compose run --rm app
```

## 3. Használat

Az alkalmazás elindul és betölti a dokumentumokat:

```
====================================
  AI Knowledge Router - RAG System
====================================

Dokumentumok betöltése...
✓ IT: 3 dokumentum (12 chunk)
✓ HR: 2 dokumentum (8 chunk)
✓ FINANCE: 2 dokumentum (7 chunk)

Összesen: 27 chunk betöltve

Kérdezz bármit! ('exit' - kilépés)
-----------------------------------

Kérdés: 
```

## 4. Példa Kérdések

**IT:**
```
Hogyan kapcsolódjak a VPN-hez?
Milyen szoftvereket telepíthetek?
```

**HR:**
```
Mennyi szabadság jár nekem?
Milyen benefit-ek vannak?
```

**Finance:**
```
Hogyan igényeljek költségtérítést?
Mikor érkezik a fizetés?
```

## 5. Kilépés

```
Kérdés: exit
Viszlát!
```

## 6. Cleanup

```bash
make clean
```

## Troubleshooting

**Qdrant nem indul:**
```bash
docker-compose logs qdrant
```

**OpenAI API hiba:**
- Ellenőrizd az API kulcsot
- Ellenőrizd a model hozzáférést (gpt-4o)

**Python import hiba:**
```bash
pip install -r requirements.txt
```

