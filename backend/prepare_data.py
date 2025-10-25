import sqlite3
import urllib.request
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import requests
import json

def get_csv_and_sql():
    # urls for where to retrieve data
    URL_TO_DB = "https://raw.githubusercontent.com/whotracksme/whotracks.me/master/whotracksme/data/assets/trackerdb.sql"
    URL_TO_CSVS = {
            'trackers':"https://s3.amazonaws.com/data.whotracks.me/2025-09/global/trackers.csv",
            'sites_trackers': "https://s3.amazonaws.com/data.whotracks.me/2025-09/global/sites_trackers.csv",
            'sites': "https://s3.amazonaws.com/data.whotracks.me/2025-09/global/sites.csv"
    }
    PRIVACYSPY_URL = "https://privacyspy.org/api/v2/products.json"

    # get the sql script to create database
    urllib.request.urlretrieve(URL_TO_DB,('trackerdb.sql'))

    # get the csvs of the datasets needed
    for name, url in URL_TO_CSVS.items():
        urllib.request.urlretrieve(url,f'{name}.csv')
    
    # get the full json of privacyspy
    json_response = requests.get(PRIVACYSPY_URL)
    json_response.raise_for_status()
    privacy_data = json_response.json()

    #create file for the json file
    with open('privacyspy_products.json', 'w', encoding='utf-8') as f:
        json.dump(privacy_data, f, indent=2, ensure_ascii=False)

def merge_sql_to_csv():
    # create and connect to the database
    con = sqlite3.connect('trackerdb.sqlite')
    with open('trackerdb.sql', "r", encoding="utf-8") as f:
        sql_script = f.read()
    con.executescript(sql_script)

    # links databases together
    query = """
    SELECT 
        t.id AS tracker_id,
        t.name AS tracker_name,
        c.name AS category,
        comp.name AS company_name
    FROM trackers t
    LEFT JOIN categories c ON t.category_id = c.id
    LEFT JOIN companies comp ON t.company_id = comp.id;
"""

    merged_sql = pd.read_sql_query(query, con)
    
    con.close()

    # combines database and csv files into one csv
    sites_trackers = pd.read_csv('sites_trackers.csv')
    trackers = pd.read_csv('trackers.csv')

    filtered_trackers = trackers[['tracker','reach', 'site_reach_top10k']]

    first_merge = sites_trackers.merge(
        merged_sql,
        left_on='tracker',
        right_on='tracker_id',
        how="left"
    )
    final_merge = first_merge.merge(
        filtered_trackers,
        on='tracker',
        how="left"
    )

    # Export merged dataset
    final_merge.to_csv("full_sites_trackers.csv", index=False)

#scales values
def scaler(column):
        scaler = MinMaxScaler()
        scaled = scaler.fit_transform(column)
        return scaled

def add_columns():

    # adds columns of scaled data to datasets

    sites_trackers = pd.read_csv('full_sites_trackers.csv')
    sites = pd.read_csv('sites.csv')

    tracker_total = (
    sites_trackers
    .groupby("site")["tracker"]
    .nunique()
    .reset_index(name="total_trackers")
    )

    merged_sites = sites.merge(tracker_total, how='left', on='site')
    merged_sites[['total_trackers']] = merged_sites[['total_trackers']].fillna(0).astype(int)

    merged_sites['scaled_total'] = scaler(merged_sites[['total_trackers']])
    merged_sites['scaled_companies'] = scaler(merged_sites[['companies']])
    merged_sites['scaled_requests_tracking'] = scaler(merged_sites[['requests_tracking']])
    merged_sites['scaled_trackers'] = scaler(merged_sites[['trackers']])
    merged_sites['percentage_tracking_requests'] = (merged_sites['requests_tracking'] / merged_sites['requests']) * 100

    #calculates the privacy score
    merged_sites['privacy_score'] = 100 * (
        (1 - merged_sites['scaled_total']) * 0.10 +
        (1 - merged_sites['scaled_companies']) * 0.10 +
        (1 - merged_sites['tracked']) * 0.20 +
        (1 - merged_sites['scaled_requests_tracking']) * 0.15 +
        (1 - merged_sites['scaled_trackers']) * 0.25 +
        (1 - merged_sites['referer_leaked']) * 0.20
    )

    merged_sites.to_csv('sites_full.csv', index=False)

get_csv_and_sql()
merge_sql_to_csv()
add_columns()