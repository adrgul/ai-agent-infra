"""
GitHub Public API Client - Házi Feladat
=========================================
Publikus API hívás példa, amely később beépíthető a Knowledge Router projektbe.

Telepítés:
    python -m venv venv
    source venv/Scripts/activate  (Windows)
    source venv/bin/activate       (Linux/Mac)
    pip install requests

Használat:
    python public_api_demo.py

API Dokumentáció:
    https://docs.github.com/en/rest
"""

import requests
from typing import Dict, List, Optional
import json


class GitHubPublicAPI:
    """GitHub publikus API kliens - nincs szükség API kulcsra."""
    
    BASE_URL = "https://api.github.com"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Python-Student-Demo"
        })
    
    def search_repos(self, keyword: str, limit: int = 5) -> List[Dict]:
        """
        Repository keresés publikus GitHub repo-k között.
        
        Args:
            keyword: Keresési kulcsszó (pl. "python", "langchain")
            limit: Maximum találatok száma
            
        Returns:
            Lista a repository adatokkal
        """
        try:
            url = f"{self.BASE_URL}/search/repositories"
            params = {
                "q": keyword,
                "sort": "stars",
                "order": "desc",
                "per_page": limit
            }
            
            print(f"🔍 Keresés: '{keyword}'...")
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            repos = []
            
            for item in data.get("items", []):
                repos.append({
                    "name": item["name"],
                    "owner": item["owner"]["login"],
                    "full_name": item["full_name"],
                    "description": item["description"] or "Nincs leírás",
                    "stars": item["stargazers_count"],
                    "language": item["language"] or "N/A",
                    "url": item["html_url"]
                })
            
            return repos
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Hiba az API hívás során: {e}")
            return []
    
    def get_repo_details(self, owner: str, repo: str) -> Optional[Dict]:
        """
        Részletes információ egy konkrét repository-ról.
        
        Args:
            owner: Repository tulajdonos
            repo: Repository neve
            
        Returns:
            Repository részletek vagy None
        """
        try:
            url = f"{self.BASE_URL}/repos/{owner}/{repo}"
            
            print(f"📦 Lekérdezés: {owner}/{repo}...")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                "name": data["name"],
                "full_name": data["full_name"],
                "description": data["description"] or "Nincs leírás",
                "stars": data["stargazers_count"],
                "forks": data["forks_count"],
                "watchers": data["watchers_count"],
                "open_issues": data["open_issues_count"],
                "language": data["language"] or "N/A",
                "created": data["created_at"],
                "updated": data["updated_at"],
                "license": data.get("license", {}).get("name", "Nincs licenc"),
                "topics": data.get("topics", []),
                "url": data["html_url"]
            }
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Hiba: {e}")
            return None


def demo():
    """Demonstráció: GitHub API használat."""
    
    print("=" * 70)
    print("GitHub Publikus API - Házi Feladat Demo")
    print("=" * 70)
    print()
    
    # API kliens inicializálás
    api = GitHubPublicAPI()
    
    # 1. FELADAT: Repository keresés
    print("📌 1. FELADAT: Repository keresés")
    print("-" * 70)
    
    search_term = "fastapi"
    repos = api.search_repos(search_term, limit=3)
    
    if repos:
        print(f"\n✅ Találatok: {len(repos)} db\n")
        for i, repo in enumerate(repos, 1):
            print(f"{i}. {repo['full_name']}")
            print(f"   ⭐ Csillagok: {repo['stars']:,}")
            print(f"   💬 Leírás: {repo['description'][:80]}...")
            print(f"   🔗 {repo['url']}")
            print()
    else:
        print("❌ Nincs találat.\n")
    
    print("=" * 70)
    
    # 2. FELADAT: Részletes info lekérése
    print("\n📌 2. FELADAT: Részletes repository információ")
    print("-" * 70)
    
    if repos:
        first = repos[0]
        owner = first["owner"]
        repo_name = first["name"]
        
        details = api.get_repo_details(owner, repo_name)
        
        if details:
            print(f"\n✅ Repository: {details['full_name']}\n")
            print(f"📝 Leírás: {details['description']}")
            print(f"⭐ Csillagok: {details['stars']:,}")
            print(f"🍴 Forkolt: {details['forks']:,}")
            print(f"👀 Megfigyelők: {details['watchers']:,}")
            print(f"🐛 Nyitott issue-k: {details['open_issues']:,}")
            print(f"💻 Nyelv: {details['language']}")
            print(f"📜 Licenc: {details['license']}")
            print(f"📅 Létrehozva: {details['created'][:10]}")
            print(f"🔄 Frissítve: {details['updated'][:10]}")
            
            if details['topics']:
                print(f"🏷️  Témák: {', '.join(details['topics'][:5])}")
            
            print(f"\n🔗 URL: {details['url']}")
    
    print("\n" + "=" * 70)
    print("✅ Demo sikeresen lefutott!")
    print("=" * 70)
    print("\n💡 Később ez beépíthető a Knowledge Router 'IT domain' részébe.")


if __name__ == "__main__":
    demo()