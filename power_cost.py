from dataclasses import dataclass
from enum import Enum
from typing import List

import pytz
import os
import json
import requests
from datetime import datetime, timedelta
from dateutil import parser  # to parse datetime strings
from dataclasses import replace

# Enum for price areas
class PriceArea(Enum):
    NO1 = "Oslo / Øst-Norge"
    NO2 = "Kristiansand / Sør-Norge"
    NO3 = "Trondheim / Midt-Norge"
    NO4 = "Tromsø / Nord-Norge"
    NO5 = "Bergen / Vest-Norge"

# Data class for electricity cost information
@dataclass
class ElectricityCost:
    NOK_per_kWh: float
    EUR_per_kWh: float
    EXR: float
    time_start: str
    time_end: str

# Type hint for a list of electricity costs
ElectricityCostList = List[ElectricityCost]

def fetch_electricity_cost(date: datetime, area: PriceArea) -> ElectricityCostList:
    # Format year, month, and day
    year = date.strftime("%Y")
    month = date.strftime("%m")
    day = date.strftime("%d")
    
    # Create path for caching
    cache_path = os.path.join("cache", year, month, f"{day}_{area.name}.json")
    
    # Check if data is already cached
    if os.path.exists(cache_path):
        with open(cache_path, 'r') as f:
            cached_data = json.load(f)
            return [ElectricityCost(**item) for item in cached_data]
    
    # Construct the API endpoint
    url = f"https://www.hvakosterstrommen.no/api/v1/prices/{year}/{month}-{day}_{area.name}.json"
    
    # Fetch the data from API (NOTE: This will not run in this environment)
    response = requests.get(url)
    
    # Check if request was successful
    if response.status_code == 200:
        data = response.json()
        
        # Cache the data
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        with open(cache_path, 'w') as f:
            json.dump(data, f)
            
        # Return data as a list of ElectricityCost objects
        return [ElectricityCost(**item) for item in data]
    else:
        raise Exception(f"Failed to fetch data: {response.status_code}")

def fetch_electricity_cost_utc(date_utc: datetime, area: PriceArea) -> list:
    """
    Fetch electricity cost data adjusted to UTC.

    Parameters:
        date_utc (datetime): The UTC date to fetch electricity cost data for.
        area (PriceArea): The price area to fetch electricity cost data for.

    Returns:
        list: A list of electricity cost data for the entire UTC day.
    """
    # Time zone information
    oslo_tz = pytz.timezone("Europe/Oslo")

    # Define the start and end of the UTC day
    start_date_utc = datetime(date_utc.year, date_utc.month, date_utc.day, tzinfo=pytz.utc)
    end_date_utc = start_date_utc + timedelta(days=1) - timedelta(seconds=1)

    # Convert the UTC dates to Oslo time
    start_date_oslo = start_date_utc.astimezone(oslo_tz).date()
    end_date_oslo = end_date_utc.astimezone(oslo_tz).date()

    # Fetch the electricity cost data for the Oslo dates
    if start_date_oslo == end_date_oslo:
        costs_oslo = fetch_electricity_cost(start_date_oslo, area)
    else:
        costs_oslo = fetch_electricity_cost(start_date_oslo, area) + fetch_electricity_cost(end_date_oslo, area)

    # Filter the costs based on the original UTC time range and adjust times to UTC
    costs_utc = []
    for cost in costs_oslo:
        time_start_utc = parser.parse(cost.time_start).astimezone(pytz.utc)
        time_end_utc = parser.parse(cost.time_end).astimezone(pytz.utc)

        # Check if the cost is within the original UTC time range
        if time_end_utc > start_date_utc and time_start_utc <= end_date_utc:
            cost_utc = replace(cost, time_start=time_start_utc.isoformat(), time_end=time_end_utc.isoformat())
            costs_utc.append(cost_utc)

    return costs_utc

if __name__ == "__main__":
    # Example usage
    date_example = datetime(2023, 10, 14)
    area_example = PriceArea.NO1
    prices = fetch_electricity_cost_utc(date_example, area_example)
    print(prices)