import requests
import json

def get_hungary_info():
    # Az API végpontja Magyarország adatainak lekérdezéséhez
    url = "https://restcountries.com/v3.1/name/hungary"
    
    try:
        # HTTP GET kérés küldése
        response = requests.get(url)
        
        # Státuszkód ellenőrzése (ha nem 200-as, hibát dob)
        response.raise_for_status()
        
        # JSON válasz feldolgozása
        data = response.json()
        
        # Az eredmény egy lista, így az első elemet vesszük
        if isinstance(data, list) and len(data) > 0:
            country_data = data[0]
            
            # Fontosabb adatok kinyerése és kiírása magyarul
            common_name = country_data.get('name', {}).get('common', 'N/A')
            official_name = country_data.get('name', {}).get('official', 'N/A')
            capital = country_data.get('capital', ['N/A'])[0]
            region = country_data.get('region', 'N/A')
            population = country_data.get('population', 'N/A')
            area = country_data.get('area', 'N/A')
            currency_data = country_data.get('currencies', {}).get('HUF', {})
            currency = f"{currency_data.get('name', 'N/A')} ({currency_data.get('symbol', 'N/A')})"
            
            print("=== Magyarország Információk ===")
            print(f"Megnevezés: {common_name}")
            print(f"Hivatalos név: {official_name}")
            print(f"Főváros: {capital}")
            print(f"Régió: {region}")
            print(f"Népesség: {population:,} fő".replace(',', ' '))
            print(f"Terület: {area:,} km²".replace(',', ' '))
            print(f"Pénznem: {currency}")
            
            # További érdekesség: határos országok
            borders = country_data.get('borders', [])
            print(f"Határos országok kódjai: {', '.join(borders) if borders else 'Nincs adat'}")

        else:
            print("Nem érkezett érvényes adat.")

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP hiba történt: {http_err}")
    except Exception as err:
        print(f"Egyéb hiba történt: {err}")

if __name__ == "__main__":
    get_hungary_info()
