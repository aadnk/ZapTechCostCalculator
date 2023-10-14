import datetime
import pytz
import toml
from power_cost import PriceArea, fetch_electricity_cost, fetch_electricity_cost_utc
from zaptech_api import get_charging_sessions, get_zaptech_token
from dateutil import parser  # To parse datetime strings
from dataclasses import dataclass

@dataclass
class ChargingSessionEnergy:
    SessionId: str
    Timestamp: datetime.datetime
    Energy: float
    Cost: float
    NetUsageFee: float  # New field for the net usage fee
    TotalCostWithNetFee: float  # New field for total cost with net usage fee
    TotalCostWithVAT: float  # New field for total cost with VAT
    CostCurrency: str

def get_charging_session_energy(from_date, to_date):
    # Get secrets from toml file
    secrets = toml.load("secrets.toml")
    username = secrets["zaptech"]["username"]
    password = secrets["zaptech"]["password"]

    # Get token
    token = get_zaptech_token(username, password)

    history = get_charging_sessions(token, from_date, to_date)
    costs = {}

    for session in history.Data:
        for energy in session.EnergyDetails:
            original_datetime = parser.parse(energy.Timestamp)

            # Convert to the current time zone - this is because fetch_electricity_cost returns data in the local time zone
            energy_datetime = original_datetime.astimezone(tz=datetime.timezone.utc)
            energy_date = energy_datetime.date()

            # See if cost is already cached
            if energy_date not in costs:
                # Fetch costs for this day and cache it
                costs[energy_date] = fetch_electricity_cost_utc(energy_date, area=PriceArea.NO2)

            # Find the cost that is applicable for the timestamp of the energy detail
            applicable_cost = None
            for cost in costs[energy_date]:
                cost_start_time = parser.parse(cost.time_start)
                cost_end_time = parser.parse(cost.time_end)

                if cost_start_time <= energy_datetime < cost_end_time:
                    applicable_cost = cost
                    break
            
            if applicable_cost is None:
                print(f"No applicable cost found for session {session.Id} at {energy.Timestamp}")
                continue

            # Calculate cost of the energy detail
            energy_cost = energy.Energy * applicable_cost.NOK_per_kWh

             # Calculate the net usage fee
            daytime_start = energy_datetime.replace(hour=6, minute=0, second=0, microsecond=0)
            daytime_end = energy_datetime.replace(hour=22, minute=0, second=0, microsecond=0)
            
            # Check if it's a weekend (Saturday or Sunday)
            is_weekend = energy_datetime.weekday() >= 5
            
            # Use a lower rate during the night and on weekends
            if daytime_start <= energy_datetime < daytime_end and not is_weekend:
                net_usage_fee_per_kwh = 0.3059  # day time net usage fee in NOK
            else:
                net_usage_fee_per_kwh = 0.2259  # night time and weekend net usage fee in NOK
            
            net_usage_fee = energy.Energy * net_usage_fee_per_kwh

            # Calculate total cost with net usage fee
            total_cost_with_net_fee = energy_cost + net_usage_fee
            
            # Calculate total cost with VAT
            total_cost_with_vat = total_cost_with_net_fee * 1.25  # adding 25% VAT

            yield ChargingSessionEnergy(
                SessionId=session.Id,
                Timestamp=energy_datetime,
                Energy=energy.Energy,
                Cost=energy_cost,
                NetUsageFee=net_usage_fee,  # assign calculated net usage fee
                TotalCostWithNetFee=total_cost_with_net_fee,  # assign calculated total cost with net fee
                TotalCostWithVAT=total_cost_with_vat,  # assign calculated total cost with VAT
                CostCurrency="NOK"
            )

if __name__ == "__main__":
    from_date = datetime.datetime(2023, 9, 1)
    to_date = datetime.datetime(2023, 10, 1)

    sessions = get_charging_session_energy(from_date, to_date)

    # Print to CSV or any desired format
    print("SessionId,Timestamp,Energy,Cost,NetUsageFee,TotalCostWithNetFee,TotalCostWithVAT,CostCurrency")
    for session in sessions:
        print(f"{session.SessionId},{session.Timestamp},{session.Energy},{session.Cost},{session.NetUsageFee},{session.TotalCostWithNetFee},{session.TotalCostWithVAT},{session.CostCurrency}")