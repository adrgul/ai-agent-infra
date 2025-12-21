from typing import Dict, Any
import httpx

def create_jira_ticket(summary: str, description: str = None, priority: str = "Medium") -> Dict[str, Any]:
    """
    Mock tool to create a Jira ticket.
    """
    # In a real app, this would use the Jira API
    ticket_id = f"IT-{hash(summary) % 10000}"
    print(f"--> TOOL EXECUTION: Creating Jira Ticket [{ticket_id}]")
    print(f"    Summary: {summary}")
    print(f"    Priority: {priority}")
    
    return {
        "status": "success",
        "ticket_id": ticket_id,
        "link": f"https://jira.company.com/browse/{ticket_id}",
        "message": f"Ticket {ticket_id} created successfully."
    }

def calculate_vacation_days(user_id: str) -> Dict[str, Any]:
    """
    Mock tool to fetch available vacation days.
    """
    print(f"--> TOOL EXECUTION: Checking vacation days for {user_id}")
    # Mock database lookup
    return {
        "status": "success",
        "available_days": 12,
        "pending_requests": 1,
        "message": "You have 12 vacation days remaining."
    }

def get_country_info(country: str) -> Dict[str, Any]:
    """
    Fetches information about a country from the REST Countries API.
    """
    print(f"--> TOOL EXECUTION: Fetching info for country: {country}")
    
    url = f"https://restcountries.com/v3.1/name/{country}"
    
    try:
        with httpx.Client() as client:
            response = client.get(url)
            
        if response.status_code == 200:
            data = response.json()[0] # Take the first result
            
            common_name = data.get("name", {}).get("common", country)
            official_name = data.get("name", {}).get("official", "")
            capital = ", ".join(data.get("capital", []))
            region = data.get("region", "Unknown")
            population = data.get("population", 0)
            currencies = ", ".join([c["name"] for c in data.get("currencies", {}).values()])
            
            message = (
                f"Country: {common_name} ({official_name})\n"
                f"Capital: {capital}\n"
                f"Region: {region}\n"
                f"Population: {population:,}\n"
                f"Currency: {currencies}"
            )
            
            return {
                "status": "success",
                "message": message,
                "data": { # Return raw data if needed later
                    "name": common_name,
                    "capital": capital,
                    "population": population
                }
            }
        else:
            return {
                "status": "error",
                "message": f"Could not find country '{country}'. API returned {response.status_code}."
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error fetching country info: {str(e)}"
        }

# Registry mapping tool names to functions
TOOL_REGISTRY = {
    "create_jira_ticket": create_jira_ticket,
    "check_vacation_balance": calculate_vacation_days,
    "get_country_info": get_country_info
}
