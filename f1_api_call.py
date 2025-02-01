import requests
import pandas as pd

def fetch_race_data(season, round_number):
    """
    Fetch race details for a specific season and round.
    """
    url = f"http://ergast.com/api/f1/{season}/{round_number}.json"
    response = requests.get(url)
    if response.status_code == 200:
        races = response.json()["MRData"]["RaceTable"]["Races"]
        if races:  # Ensuring the Races list is not empty
            return races[0]
        else:
            print(f"[INFO] No race data found for Season {season}, Round {round_number}. Skipping...")
            return None
    else:
        print(f"[ERROR] Failed to fetch data for Season {season}, Round {round_number}. HTTP Status: {response.status_code}")
        return None


def fetch_driver_standings(season, round_number):
    """
    Fetch driver standings for a specific season and round.
    """
    url = f"http://ergast.com/api/f1/{season}/{round_number}/driverStandings.json"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()["MRData"]["StandingsTable"]["StandingsLists"]
        # Ensuring data is present
        if data and len(data) > 0:
            return data[0]["DriverStandings"]
    return []


def fetch_race_results(season, round_number):
    """
    Fetch race results for a specific season and round.
    """
    url = f"http://ergast.com/api/f1/{season}/{round_number}/results.json"
    response = requests.get(url)
    if response.status_code == 200:
        race_table = response.json()["MRData"]["RaceTable"]["Races"]
        if race_table:
            return race_table[0]["Results"]
    return []


def fetch_qualifying_results(season, round_number):
    """
    Fetch qualifying results for each driver in a given season/round.
    Returns a dictionary keyed by driverId with details about the qualifying.
    For example:
    {
       'hamilton': {
         'position': '1',
         'Q1': '1:23.4',
         'Q2': '1:22.8',
         'Q3': '1:22.2'
       },
       'max_verstappen': { ... },
       ...
    }
    """
    url = f"http://ergast.com/api/f1/{season}/{round_number}/qualifying.json"
    response = requests.get(url)
    qualifying_data = {}
    if response.status_code == 200:
        data = response.json()["MRData"]["RaceTable"]["Races"]
        if data and len(data) > 0 and "QualifyingResults" in data[0]:
            for entry in data[0]["QualifyingResults"]:
                driver_id = entry["Driver"]["driverId"]
                qualifying_data[driver_id] = {
                    "position": entry["position"],
                    "Q1": entry.get("Q1", "N/A"),
                    "Q2": entry.get("Q2", "N/A"),
                    "Q3": entry.get("Q3", "N/A")
                }
    return qualifying_data


def fetch_finishing_status_for_season_driver(season, driver_id):
    """
    Fetch finishing status summary for a given driver in a season.
    This endpoint returns how many times a particular status
    occurred in that season for the driver, e.g.:
    [
      {
        'statusId': '1',
        'count': '14',
        'status': 'Finished'
      },
      ...
    ]
    In practice, the 'status' in the actual race result (`result["status"]`)
    is more directly relevant for that race. However, you might store this
    summary for additional info or analytics.
    """
    url = f"http://ergast.com/api/f1/{season}/drivers/{driver_id}/status.json"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()["MRData"]["StatusTable"]["Status"]
        return data
    return []


def fetch_pitstops(season, round_number, driver_id):
    url = f"http://ergast.com/api/f1/{season}/{round_number}/drivers/{driver_id}/pitstops.json"
    response = requests.get(url)
    if response.status_code == 200:
        race_table = response.json()["MRData"]["RaceTable"]["Races"]
        if race_table and "PitStops" in race_table[0]:
            return race_table[0]["PitStops"]
    return []


def main():
    all_race_data = []

    # Defining the range of seasons
    start_season = 2010
    end_season = 2024

    for season in range(start_season, end_season + 1):
        for round_number in range(1, 30):  # Assuming a max of 30 rounds per season
            race = fetch_race_data(season, round_number)
            if not race:  # Skipping if no race data is found
                continue

            race_name = race["raceName"]
            circuit_name = race["Circuit"]["circuitName"]
            location = race["Circuit"]["Location"]["locality"]
            race_date = race["date"]

            # Fetching the race results
            race_results = fetch_race_results(season, round_number)

            # Fetching the driver standings for that round
            standings = fetch_driver_standings(season, round_number)

            # Fetching the qualifying results for that round
            qualifying_data = fetch_qualifying_results(season, round_number)

            for result in race_results:
                driver = result["Driver"]
                constructor = result["Constructor"]
                driver_id = driver["driverId"]

                # Matching the driver in the standings
                driver_standing = next(
                    (s for s in standings if s["Driver"]["driverId"] == driver_id),
                    None
                )

                # Extracting Qualifying info
                qual_info = qualifying_data.get(driver_id, {})
                qual_position = qual_info.get("position", "N/A")
                q1_time = qual_info.get("Q1", "N/A")
                q2_time = qual_info.get("Q2", "N/A")
                q3_time = qual_info.get("Q3", "N/A")

                # Extracting Pitstop info
                pitstops = fetch_pitstops(season, round_number, driver_id)
                num_pitstops = len(pitstops)
                pitstop_details = "; ".join([
                    f"Stop {p['stop']} @Lap {p['lap']} (Duration={p['duration']}s)"
                    for p in pitstops
                ]) if pitstops else "No Pitstops"

                pitstop_details = "; ".join([
                    f"Stop {p['stop']} @Lap {p['lap']} (Duration={p['duration']}s)"
                    for p in pitstops
                ]) if pitstops else "No Pitstops"

                finishing_status = result["status"]

                # Building a row with all the data
                all_race_data.append({
                    "Season": season,
                    "Round": round_number,
                    "Race Name": race_name,
                    "Circuit Name": circuit_name,
                    "Location": location,
                    "Race Date": race_date,
                    "Driver Name": f"{driver['givenName']} {driver['familyName']}",
                    "Driver ID": driver_id,
                    "Driver Nationality": driver["nationality"],
                    "Constructor": constructor["name"],
                    
                    # Qualifying
                    "Qualifying Position": qual_position,
                    "Q1 Time": q1_time,
                    "Q2 Time": q2_time,
                    "Q3 Time": q3_time,
                    
                    # Grid, Race & Standings
                    "Starting Grid Position": result["grid"],
                    "Final Position": result["position"],
                    "Finishing Status": finishing_status,
                    "Time/Status": result["Time"]["time"] if "Time" in result else finishing_status,
                    "Points": result["points"],
                    "Laps Completed": result["laps"],
                    "Driver Total Points": driver_standing["points"] if driver_standing else "N/A",
                    
                    # Pit stop info
                    "Pit Stop Count": num_pitstops,
                    "Pit Stop Details": pitstop_details,
                })
        print("Collected data for Season - ", season)

    # Saving the collected data to a CSV
    df = pd.DataFrame(all_race_data)
    df.to_csv("f1_enhanced_race_data_final.csv", index=False)
    print("Enhanced race data saved to 'f1_enhanced_race_data_final.csv'.")


if __name__ == "__main__":
    main()
