import sqlite3
import requests
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import requests
from io import StringIO

def get_privacyspy_data():

    PRIVACYSPY_URL = "https://privacyspy.org/api/v2/products.json"

    # get the full json of privacyspy
    json_response = requests.get(PRIVACYSPY_URL)
    json_response.raise_for_status()
    privacy_data = json_response.json()

    return privacy_data

def get_wtm_csv():
    # urls for where to retrieve data
    
    URL_TO_CSVS = {
        'trackers':"https://s3.amazonaws.com/data.whotracks.me/2025-09/us/trackers.csv",
        'sites_trackers': "https://s3.amazonaws.com/data.whotracks.me/2025-09/us/sites_trackers.csv",
        'sites': "https://s3.amazonaws.com/data.whotracks.me/2025-09/us/sites.csv",
    }
    
    # get the csvs of the datasets needed
    wtm_csvs={}
    for name, url in URL_TO_CSVS.items():
        csv_response = requests.get(url)
        csv_response.raise_for_status()
        wtm_csvs[name] = pd.read_csv(StringIO(csv_response.text))

    return wtm_csvs

def get_merged_trackers():

    URL_TO_DB = "https://raw.githubusercontent.com/whotracksme/whotracks.me/master/whotracksme/data/assets/trackerdb.sql"

    db_response = requests.get(URL_TO_DB)
    db_response.raise_for_status()
    db_file = db_response.text

    # connect to the database
    con = sqlite3.connect(':memory:')
    con.executescript(db_file)

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
    sites_trackers = get_wtm_csv()['sites_trackers']
    trackers = get_wtm_csv()['trackers']

    filtered_trackers = trackers[['tracker','reach', 'site_reach_top10k']]

    first_merge = sites_trackers.merge(
        merged_sql,
        left_on='tracker',
        right_on='tracker_id',
        how="left"
    )
    merged_trackers = first_merge.merge(
        filtered_trackers,
        on='tracker',
        how="left"
    )

    merged_trackers['category'] = merged_trackers['category'].str.replace('_', ' ',regex=False).str.title()
       

    # return merged dataset
    return merged_trackers

#scales values
def scaler(column):
        return MinMaxScaler().fit_transform(column)
        
def get_merged_sites(sites_trackers, sites):

    # adds columns of scaled data to datasets
    tracker_total = (
    sites_trackers
    .groupby("site")["tracker"]
    .nunique()
    .reset_index(name="total_trackers")
    )

    category_total = (
    sites_trackers
    .groupby(["site", "category"])["tracker"]
    .nunique()
    .reset_index(name="total_ad_trackers")
    )

    ad_tracker_total = category_total[category_total['category']=='Advertising']

    merged_categories = sites.merge(ad_tracker_total, how='left', on='site')
    merged_sites = merged_categories.merge(tracker_total, how='left', on='site')

    merged_sites[['total_trackers']] = merged_sites[['total_trackers']].fillna(0).astype(int)
    merged_sites[['total_ad_trackers']] = merged_sites[['total_ad_trackers']].fillna(0).astype(int)

    merged_sites['scaled_ad_total'] = scaler(merged_sites[['total_ad_trackers']])
    merged_sites['scaled_total'] = scaler(merged_sites[['total_trackers']])
    merged_sites['scaled_companies'] = scaler(merged_sites[['companies']])
    merged_sites['scaled_requests_tracking'] = scaler(merged_sites[['requests_tracking']])
    merged_sites['scaled_trackers'] = scaler(merged_sites[['trackers']])
    merged_sites['percentage_tracking_requests'] = (merged_sites['requests_tracking'] / merged_sites['requests']) * 100

    #calculates the privacy score
    merged_sites['privacy_score'] = 10 * (
        (1 - merged_sites['scaled_total']) * 0.20 +
        (1 - merged_sites['scaled_ad_total']) * 0.10 +
        (1 - merged_sites['scaled_companies']) * 0.05 +
        (1 - merged_sites['tracked']) * 0.20 +
        (1 - merged_sites['scaled_requests_tracking']) * 0.15 +
        (1 - merged_sites['scaled_trackers']) * 0.15 +
        (1 - merged_sites['referer_leaked']) * 0.15
    )

    return merged_sites

def get_data():
    sites_trackers = get_merged_trackers()
    sites = get_merged_sites(sites_trackers, get_wtm_csv()['sites'])
    privacy_spy_data = get_privacyspy_data()

    return {
    'sites_trackers': sites_trackers,
    'sites': sites,
    'ps_data': privacy_spy_data
}
