import httpx

async def fetch_gas_exported_quantity(point_label: str, start_date: str, end_date: str):
    base_url = "https://transparency.entsog.eu/api/v1"

    # Fetch connection points to get pointKey
    connection_points_url = f"{base_url}/connectionPoints?extended=1&pointLabel={point_label}"
    async with httpx.AsyncClient() as client:
        response = await client.get(connection_points_url)
        response.raise_for_status()
        connection_points = response.json()

    if not connection_points.get("connectionPoints"):
        raise ValueError("No connection points found for the given label.")

    point_key = connection_points["connectionPoints"][0]["pointKey"]

    # Fetch operational data
    operational_data_url = (
        f"{base_url}/operationaldatas?indicator=Physical Flow&pointKey={point_key}"
        f"&from={start_date}&to={end_date}&periodType=day"
    )
    async with httpx.AsyncClient() as client:
        response = await client.get(operational_data_url)
        response.raise_for_status()
        operational_data = response.json()

    if not operational_data.get("operationalData"):
        raise ValueError("No operational data found for the given parameters.")

    # Extract and sum kWh quantities
    total_quantity = sum(
        entry["value"] for entry in operational_data["operationalData"]
        if entry.get("value")
    )

    return total_quantity