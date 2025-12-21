# Magyarország Információ Lekérdező

Ez egy egyszerű Python szkript, amely a [REST Countries API](https://restcountries.com/) segítségével kér le és jelenít meg aktuális adatokat Magyarországról.

## Funkciók

A szoftver a következő információkat gyűjti össze és írja ki a konzolra:
- Ország neve (köznyelvi és hivatalos)
- Főváros
- Régió
- Népesség (formázva)
- Terület (km²)
- Pénznem
- Szomszédos országok kódjai

## Előfeltételek

- Python 3.x telepítése szükséges.
- Internetkapcsolat az API eléréséhez.

## Telepítés és Futtatás

A legegyszerűbb módszer a mellékelt automatizáló szkript használata, amely létrehozza a környezetet és elindítja az alkalmazást.

### Gyors indítás (Ajánlott)

1. Navigálj a projekt könyvtárába.
2. Futtasd a `start-dev.sh` parancsot:

```bash
./start-dev.sh
```

*(Megjegyzés: Ha a futtatás jogosultsági hiba miatt nem sikerül, add ki egyszer a `chmod +x start-dev.sh` parancsot.)*

A szkript automatikusan:
- Törli az esetleges korábbi virtuális környezetet.
- Létrehoz egy újat (`venv`).
- Telepíti a szükséges függőségeket (`requirements.txt` alapján).
- Elindítja a programot.

### Manuális telepítés (Haladó)

Ha kézzel szeretnéd telepíteni:

1. Hozz létre egy virtuális környezetet:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
2. Telepítsd a függőségeket:
   ```bash
   pip install -r requirements.txt
   ```
3. Futtasd a programot:
   ```bash
   python get_hungary_info.py
   ```

## Példa kimenet

```text
=== Magyarország Információk ===
Megnevezés: Hungary
Hivatalos név: Hungary
Főváros: Budapest
Régió: Europe
Népesség: 9 730 000 fő
Terület: 93 028 km²
Pénznem: Hungarian forint (Ft)
Határos országok kódjai: AUT, HRV, ROU, SRB, SVK, SVN, UKR
```
