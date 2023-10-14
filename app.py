import argparse
import datetime
import os
import sys
from typing import Iterable
import toml
from power_cost import PriceArea, fetch_electricity_cost_utc
from zaptech_api import get_charging_sessions, get_zaptech_token
from dateutil import parser  # To parse datetime strings
from dataclasses import dataclass

@dataclass
class ChargingSessionEnergy:
    SessionId: str
    Timestamp: datetime.datetime
    Energy: float
    EnergyUsageFee: float  # New field for the energy usage fee
    NetUsageFee: float  # New field for the net usage fee
    EnergyCost: float
    NetUsageCost: float  
    TotalCostNoVat: float  # New field for total cost without VAT
    TotalCostWithVAT: float  # New field for total cost with VAT
    CostCurrency: str

def get_charging_session_energy(secrets, from_date, to_date, 
                                price_area=PriceArea.NO2, 
                                low_net_usage_fee=0.2259, high_net_usage_fee=0.3059):
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
                costs[energy_date] = fetch_electricity_cost_utc(energy_date, area=price_area)

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
                net_usage_fee_per_kwh = high_net_usage_fee # day time net usage fee in NOK
            else:
                net_usage_fee_per_kwh = low_net_usage_fee # night time and weekend net usage fee in NOK
            
            net_usage_fee = energy.Energy * net_usage_fee_per_kwh

            # Calculate total cost without VAT
            total_cost_without_vat = energy_cost + net_usage_fee
            
            # Calculate total cost with VAT
            total_cost_with_vat = total_cost_without_vat * 1.25  # adding 25% VAT

            yield ChargingSessionEnergy(
                SessionId=session.Id,
                Timestamp=energy_datetime,
                Energy=energy.Energy,
                EnergyUsageFee=applicable_cost.NOK_per_kWh,
                NetUsageFee=net_usage_fee, 
                EnergyCost=energy_cost,
                NetUsageCost=net_usage_fee,
                TotalCostNoVat=total_cost_without_vat,  
                TotalCostWithVAT=total_cost_with_vat,  
                CostCurrency="NOK"
            )

def get_secrets(args):
    # Check environment variables
    username = os.environ.get('ZAPTECH_USERNAME')
    password = os.environ.get('ZAPTECH_PASSWORD')

    # Check secrets file
    if username is None or password is None:
        if args.secrets_file:
            if not os.path.exists(args.secrets_file):
                # If the user has supplied a secrets file, but it doesn't exist, raise an error
                if args.secrets_file != "secrets.toml":
                    raise ValueError(f"Secrets file {args.secrets_file} does not exist. Create it or provide credentials via environment variables or command line arguments.")
            else:
                secrets = toml.load(args.secrets_file)
                username = secrets["zaptech"]["username"]
                password = secrets["zaptech"]["password"]

    # Check command line arguments
    if args.username and args.password:
        username = args.username
        password = args.password

    if username is None or password is None:
        raise ValueError("Credentials are missing. Provide them via environment variables, a secrets file, or command line arguments.")

    return {"zaptech": {"username": username, "password": password}}

def main():
    parser = argparse.ArgumentParser(description='Fetch and calculate charging session energy costs.')
    parser.add_argument('--from_date', required=True, type=lambda s: datetime.datetime.strptime(s, '%Y-%m-%d'), help='Start date (inclusive) in format YYYY-MM-DD.')
    parser.add_argument('--to_date', required=True, type=lambda s: datetime.datetime.strptime(s, '%Y-%m-%d'), help='End date (exclusive) in format YYYY-MM-DD.')
    parser.add_argument('--output_file', required=False, help='Path to the output CSV file.')
    parser.add_argument('--secrets_file', default='secrets.toml', help='Path to the secrets file. Default is "secrets.toml".')
    parser.add_argument('--username', help='Zaptech API username. Overrides secrets file.')
    parser.add_argument('--password', help='Zaptech API password. Overrides secrets file.')
    parser.add_argument('--price_area', default='NO2', help='Price area to use for electricity cost. Default is "NO2".')
    parser.add_argument('--low_net_usage_fee', default=0.2259, type=float, help='Net usage fee for night time and weekends. Default is 0.2259 NOK/kWh.')
    parser.add_argument('--high_net_usage_fee', default=0.3059, type=float, help='Net usage fee for day time. Default is 0.3059 NOK/kWh.')

    args = parser.parse_args()
    secrets = get_secrets(args)

    # Parse price area
    price_area = PriceArea[args.price_area.upper()]

    sessions = get_charging_session_energy(secrets, args.from_date, args.to_date, 
                                           price_area=price_area, 
                                           low_net_usage_fee=args.low_net_usage_fee, high_net_usage_fee=args.high_net_usage_fee)

    if args.output_file is not None:
        with open(args.output_file, 'w') as f:
            # Print to CSV
            print_csv(sessions, f)
    else:
        # Print to console
        print_csv(sessions, sys.stdout)

def print_csv(sessions: Iterable[ChargingSessionEnergy], file):
    # Print to CSV
    print("SessionId,Timestamp,Energy,EnergyUsageFee,NetUsageFee,EnergyCost,NetUsageCost,TotalCostNoVat,TotalCostWithVAT,CostCurrency", file=file)

    for session in sessions:
        print(f"{session.SessionId},{session.Timestamp},{session.Energy},{session.EnergyUsageFee},{session.NetUsageFee},{session.EnergyCost},{session.NetUsageCost},{session.TotalCostNoVat},{session.TotalCostWithVAT},{session.CostCurrency}", file=file)

if __name__ == "__main__":
    main()