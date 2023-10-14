import requests
import toml

from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional

from dataclasses_json import dataclass_json

@dataclass_json
@dataclass
class EnergyDetail:
    Timestamp: str
    Energy: float

@dataclass_json
@dataclass
class ChargerFirmwareVersion:
    Major: int
    Minor: int
    Build: int
    Revision: int
    MajorRevision: int
    MinorRevision: int

@dataclass_json
@dataclass
class ChargingSession:
    Id: str
    DeviceId: str
    StartDateTime: str
    EndDateTime: str
    Energy: float
    CommitMetadata: int
    CommitEndDateTime: str
    ChargerId: str
    DeviceName: str
    ExternallyEnded: bool
    EnergyDetails: List[EnergyDetail]
    ChargerFirmwareVersion: ChargerFirmwareVersion
    SignedSession: str

@dataclass_json
@dataclass
class ChargingHistory:
    Pages: int
    Data: List[ChargingSession]


def get_zaptech_token(username: str, password: str) -> str:
    """
    Obtain an access token from the ZapTech API.

    Parameters:
        username (str): The ZapTech username.
        password (str): The ZapTech password.

    Returns:
        str: The access token.
    """
    # API endpoint
    auth_url = "https://api.zaptec.com/oauth/token"
    
    # Payload
    payload = {
        "grant_type": "password",
        "username": username,
        "password": password
    }
    
    # Headers
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    # Make POST request
    response = requests.post(auth_url, data=payload, headers=headers)
    
    # Check if request was successful
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        raise Exception(f"Authentication failed: {response.status_code} - {response.text}")

def get_charging_sessions(token: str, from_date: datetime, to_date: datetime, 
                          page_index: int = 0, page_size: int = 500) -> ChargingHistory:
    """
    Fetch charging sessions from the ZapTech API.

    Parameters:
        token (str): Bearer token for API authentication.
        from_date (datetime): Start of the date range.
        to_date (datetime): End of the date range.
        page_index (int, optional): Page index for pagination. Defaults to 0.
        page_size (int, optional): Number of items per page. Defaults to 500.

    Returns:
        ChargingHistory: Object containing charging session data.
    """
    # API endpoint
    api_url = "https://api.zaptec.com/api/chargehistory"
    
    # Query parameters
    params = {
        "From": from_date.isoformat(),
        "To": to_date.isoformat(),
        "PageIndex": page_index,
        "PageSize": page_size,
        "DetailLevel": 1  # Include detailed session energy data
    }
    
    # Headers
    headers = {
        "Authorization": f"Bearer {token}",
        "accept": "application/json"
    }
    
    # Make GET request
    response = requests.get(api_url, params=params, headers=headers)
    
    # Check if request was successful
    if response.status_code == 200:
        result = ChargingHistory.from_dict(response.json())
        return result
    else:
        raise Exception(f"Failed to fetch data: {response.status_code} - {response.text}")

if __name__ == "__main__":
    # Get secrets from toml file
    secrets = toml.load("secrets.toml")
    username = secrets["zaptech"]["username"]
    password = secrets["zaptech"]["password"]

    # Get token
    token = get_zaptech_token(username, password)
    print(token)

    # Get charging sessions
    from_date = datetime(2023, 9, 1)
    to_date = datetime(2023, 10, 1)

    sessions = get_charging_sessions(token, from_date, to_date)
    print(sessions)