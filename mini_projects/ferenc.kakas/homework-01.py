import os
import sys
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import requests
from requests.auth import HTTPBasicAuth

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


# =========================
# Config
# =========================

GOOGLE_CREDENTIALS_FILE = "credentials.json"
GOOGLE_TOKEN_FILE = "token.json"

# Két scope egy tokenben: Calendar + Gmail readonly
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/gmail.readonly",
]


# =========================
# Memory (simple log)
# =========================

@dataclass
class MemoryItem:
    role: str
    content: Any


class Memory:
    def __init__(self) -> None:
        self.items: List[MemoryItem] = []

    def add(self, role: str, content: Any) -> None:
        self.items.append(MemoryItem(role=role, content=content))

    def dump_last(self, n: int = 10) -> None:
        print("\n🧠 Memory (utolsó bejegyzések):")
        for it in self.items[-n:]:
            print(f"- {it.role}: {it.content}")
        print()


# =========================
# Agent decision
# =========================

def decide_tool(text: str) -> str:
    t = text.lower().strip()
    if "jira" in t:
        return "jira"
    if any(k in t for k in ["naptár", "naptar", "calendar", "meeting", "találkozó", "talalkozo"]):
        return "calendar"
    if any(k in t for k in ["email", "gmail", "levél", "level", "mail"]):
        return "gmail"
    if t in {"help", "?"}:
        return "help"
    if t in {"memory", "mem"}:
        return "memory"
    return "unknown"


# =========================
# Jira tools
# =========================

def _get_jira_env() -> Dict[str, str]:
    missing = []
    base = os.environ.get("JIRA_BASE")
    email = os.environ.get("JIRA_EMAIL")
    token = os.environ.get("JIRA_API_TOKEN")
    if not base:
        missing.append("JIRA_BASE")
    if not email:
        missing.append("JIRA_EMAIL")
    if not token:
        missing.append("JIRA_API_TOKEN")
    if missing:
        raise RuntimeError(f"Hiányzó Jira környezeti változó(k): {', '.join(missing)}")
    return {"base": base.rstrip("/"), "email": email, "token": token}


def jira_search(jql: str, max_results: int = 10) -> List[Dict[str, Any]]:
    env = _get_jira_env()
    url = f"{env['base']}/rest/api/3/search"
    auth = HTTPBasicAuth(env["email"], env["token"])
    headers = {"Accept": "application/json"}
    params = {
        "jql": jql,
        "maxResults": max_results,
        "fields": "key,summary,status,assignee,created,priority",
    }

    r = requests.get(url, headers=headers, params=params, auth=auth, timeout=25)
    r.raise_for_status()
    data = r.json()

    issues = data.get("issues", []) or []
    out = []
    for it in issues:
        fields = it.get("fields", {}) or {}
        out.append({
            "key": it.get("key"),
            "summary": fields.get("summary"),
            "status": (fields.get("status") or {}).get("name"),
            "priority": (fields.get("priority") or {}).get("name"),
            "assignee": (fields.get("assignee") or {}).get("displayName"),
            "created": fields.get("created"),
        })
    return out


# =========================
# Google OAuth + Services
# =========================

def google_creds() -> Credentials:
    """
    Token cache: GOOGLE_TOKEN_FILE
    Client secrets: GOOGLE_CREDENTIALS_FILE
    """
    creds: Optional[Credentials] = None

    if os.path.exists(GOOGLE_TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(GOOGLE_TOKEN_FILE, GOOGLE_SCOPES)

    if not creds or not creds.valid:
        if not os.path.exists(GOOGLE_CREDENTIALS_FILE):
            raise RuntimeError(
                f"Nem találom a {GOOGLE_CREDENTIALS_FILE} fájlt. "
                "Töltsd le Google Cloud Console-ból (OAuth Desktop client)."
            )
        flow = InstalledAppFlow.from_client_secrets_file(GOOGLE_CREDENTIALS_FILE, GOOGLE_SCOPES)
        creds = flow.run_local_server(port=0)
        with open(GOOGLE_TOKEN_FILE, "w", encoding="utf-8") as f:
            f.write(creds.to_json())

    return creds


def calendar_service():
    return build("calendar", "v3", credentials=google_creds())


def gmail_service():
    return build("gmail", "v1", credentials=google_creds())


# =========================
# Calendar tools
# =========================

def list_events(time_min: datetime, time_max: datetime, max_results: int = 10) -> List[Dict[str, Any]]:
    svc = calendar_service()
    events = (
        svc.events()
        .list(
            calendarId="primary",
            timeMin=time_min.isoformat(),
            timeMax=time_max.isoformat(),
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
        .get("items", [])
    )

    out = []
    for e in events:
        start = e.get("start", {}).get("dateTime") or e.get("start", {}).get("date")
        end = e.get("end", {}).get("dateTime") or e.get("end", {}).get("date")
        out.append({
            "start": start,
            "end": end,
            "summary": e.get("summary", "(nincs cím)"),
            "location": e.get("location"),
        })
    return out


def list_today_and_tomorrow(max_results: int = 15) -> List[Dict[str, Any]]:
    now = datetime.now(timezone.utc)
    end = now + timedelta(days=2)
    return list_events(now, end, max_results=max_results)


# =========================
# Gmail tools
# =========================

def gmail_search(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    svc = gmail_service()
    res = svc.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
    msgs = res.get("messages", []) or []

    out = []
    for m in msgs:
        full = svc.users().messages().get(userId="me", id=m["id"], format="metadata").execute()
        payload = full.get("payload", {}) or {}
        headers_list = payload.get("headers", []) or []
        headers = {h.get("name"): h.get("value") for h in headers_list if h.get("name")}

        out.append({
            "from": headers.get("From"),
            "subject": headers.get("Subject"),
            "date": headers.get("Date"),
            "snippet": full.get("snippet"),
        })
    return out


# =========================
# Pretty output helpers
# =========================

def print_help():
    print(
        "\nParancs példák:\n"
        "  - jira\n"
        "  - naptár\n"
        "  - email\n"
        "  - memory   (utolsó logok)\n"
        "  - help\n"
        "  - exit\n\n"
        "Jira-nál kérni fogok project key-t (pl. PROJ) vagy JQL-t.\n"
        "Emailnél Gmail keresőkifejezést (pl. 'from:amazon subject:invoice newer_than:30d').\n"
    )


def print_jira_issues(issues: List[Dict[str, Any]]):
    if not issues:
        print("\n🧩 Nincs találat a megadott JQL-re.\n")
        return
    print("\n🧩 Jira issue-k:")
    for it in issues:
        assignee = it["assignee"] or "—"
        prio = it["priority"] or "—"
        print(f"- {it['key']} [{it['status']}] (prio: {prio}) {it['summary']}  | assignee: {assignee}")
    print()


def print_calendar_events(events: List[Dict[str, Any]]):
    if not events:
        print("\n📅 Nincs esemény a megadott időablakban.\n")
        return
    print("\n📅 Következő események:")
    for e in events:
        loc = f" @ {e['location']}" if e.get("location") else ""
        print(f"- {e['start']} → {e['end']}: {e['summary']}{loc}")
    print()


def print_emails(emails: List[Dict[str, Any]]):
    if not emails:
        print("\n✉️ Nincs találat erre a keresésre.\n")
        return
    print("\n✉️ Talált levelek:")
    for i, m in enumerate(emails, 1):
        print(f"{i}. From: {m.get('from')}")
        print(f"   Subject: {m.get('subject')}")
        print(f"   Date: {m.get('date')}")
        print(f"   Snippet: {m.get('snippet')}\n")


# =========================
# Main agent loop
# =========================

def main():
    mem = Memory()

    print("Mini-Agent CLI (Jira + Calendar + Gmail)")
    print("Írd be: jira / naptár / email  | help  | exit\n")

    while True:
        user_text = input("Te: ").strip()
        if not user_text:
            continue
        if user_text.lower() in {"exit", "quit", "kilep", "kilép"}:
            print("Szia!")
            break

        mem.add("user", user_text)
        tool = decide_tool(user_text)

        try:
            if tool == "help":
                print_help()
                mem.add("assistant", "help shown")

            elif tool == "memory":
                mem.dump_last(12)

            elif tool == "jira":
                print("\nJira mód.")
                mode = input("Írd be: (1) project key alapján lista, vagy (2) saját JQL? [1/2]: ").strip() or "1"
                if mode == "2":
                    jql = input("JQL: ").strip()
                    if not jql:
                        print("Üres JQL, visszalépek.\n")
                        continue
                else:
                    proj = input("Project key (pl. PROJ): ").strip()
                    if not proj:
                        print("Üres project key, visszalépek.\n")
                        continue
                    jql = f'project = "{proj}" AND statusCategory != Done ORDER BY created DESC'

                maxn = input("Max találat (default 10): ").strip()
                max_results = int(maxn) if maxn.isdigit() else 10

                mem.add("action", {"tool": "jira_search", "jql": jql, "max_results": max_results})
                issues = jira_search(jql=jql, max_results=max_results)
                mem.add("observation", {"jira_issues_count": len(issues)})

                print_jira_issues(issues)

            elif tool == "calendar":
                print("\nNaptár mód.")
                mode = input("Időablak: (1) ma+holnap (default), (2) következő N nap? [1/2]: ").strip() or "1"

                if mode == "2":
                    nd = input("Hány nap előre? (pl. 7): ").strip()
                    days = int(nd) if nd.isdigit() else 7
                    now = datetime.now(timezone.utc)
                    end = now + timedelta(days=days)
                    maxn = input("Max esemény (default 15): ").strip()
                    max_results = int(maxn) if maxn.isdigit() else 15

                    mem.add("action", {"tool": "calendar_list_events", "days": days, "max_results": max_results})
                    events = list_events(now, end, max_results=max_results)
                else:
                    mem.add("action", {"tool": "calendar_list_today_and_tomorrow"})
                    events = list_today_and_tomorrow(max_results=15)

                mem.add("observation", {"calendar_events_count": len(events)})
                print_calendar_events(events)

            elif tool == "gmail":
                print("\nGmail mód.")
                print("Példa query: from:amazon subject:invoice newer_than:30d")
                query = input("Gmail keresés (q): ").strip()
                if not query:
                    print("Üres query, visszalépek.\n")
                    continue
                maxn = input("Max találat (default 5): ").strip()
                max_results = int(maxn) if maxn.isdigit() else 5

                mem.add("action", {"tool": "gmail_search", "query": query, "max_results": max_results})
                emails = gmail_search(query=query, max_results=max_results)
                mem.add("observation", {"gmail_results_count": len(emails)})

                print_emails(emails)

            else:
                print("\nNem értem. Írd: jira / naptár / email / help\n")

        except requests.exceptions.RequestException as e:
            print(f"\n🌐 Hálózati/API hiba (requests): {e}\n")
            mem.add("error", {"type": "requests", "detail": str(e)})

        except Exception as e:
            print(f"\n❌ Hiba: {e}\n")
            mem.add("error", {"type": "general", "detail": str(e)})


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nKilépés.")
        sys.exit(0)
