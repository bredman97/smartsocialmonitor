import math
from prepare_data import get_data

class Controller:
    def __init__(self):

        # Load CSV files
        self.trackers = get_data()['sites_trackers']
        self.sites = get_data()['sites']

    def get_category_numbers(self, site = 'google.com'):
        # gets the number of trackers in each category
        trackers = self.trackers
        match_site = trackers[trackers['site'] == site]

        category_counts = (
        match_site
        .groupby("category")["tracker"]
        .nunique()
        .reset_index(name="num_trackers")
    )

        total = category_counts["num_trackers"].sum()
        category_counts["percent"] = (category_counts["num_trackers"] / total * 100).round(2)
        #category_counts["total_trackers"] = sites['total_trackers']
        
        #returns dataframe
        return category_counts
    
    def get_sites_trackers_df(self, site = 'google.com'):
        # get sites to trackers dataset in dataframe 
        trackers = self.trackers
        match_site = trackers[trackers['site'] == site]

        if match_site.empty:
            return None
        
        return match_site
    
    def get_privacy_score(self, site = 'google.com'):
        # get the privacy score
        sites_df = self.sites
        
        match_site = sites_df[sites_df['site'] == site]

        if match_site.empty:
            return None
        
        score = float(match_site['privacy_score'].iloc[0])

        return math.floor(score)

    def get_tracker_total(self, site = 'google.com'):
        #get the total # of trackers seen on a site
        sites_df = self.sites
        
        match_site = sites_df[sites_df['site'] == site]

        if match_site.empty:
            return None
        
        total = int(match_site['total_trackers'].iloc[0])

        return total
    
    def get_avg_companies(self, site = 'google.com'):
        # get number of companies present on a site
        sites_df = self.sites

        match_site = sites_df[sites_df['site'] == site]

        if match_site.empty:
            return None
        
        companies = float(match_site['companies'].iloc[0])

        return round(companies, 2)
    
    def get_tracked(self, site = 'google.com'):
        # gets tracked value used for privacy score
        sites_df = self.sites
        match_site = sites_df[sites_df['site'] == site]

        if match_site.empty:
            return None
        
        tracked = float(match_site['tracked'].iloc[0])
        return tracked
    
    def get_percent_request_tracking(self, site = 'google.com'):
        # gets percentage of requests that are tracking on a site
        sites_df = self.sites

        match_site = sites_df[sites_df['site'] == site]

        if match_site.empty:
            return None
        
        percentage = float(match_site['percentage_tracking_requests'].iloc[0])
        return round(percentage, 2)
    
    def get_avg_trackers_on_site(self, site = 'google.com'):
        # gets avg number of trackers on a site at any given time
        sites_df = self.sites

        match_site = sites_df[sites_df['site'] == site]

        if match_site.empty:
            return None
        
        avg_trackers_on_site = float(match_site['trackers'].iloc[0])

        return round(avg_trackers_on_site)
    
    def get_referer_leaked(self, site = 'google.com'):
        # gets referer leaked score which is used for privacy score
        sites_df = self.sites
        match_site = sites_df[sites_df['site'] == site]

        if match_site.empty:
            return None
        
        avg_trackers_on_site = float(match_site['referer_leaked'].iloc[0])
        return avg_trackers_on_site

    def list_of_domains(self):
        # gets the list of all domains in the dataset
        sites_df = self.sites
        sites_df.sort_values(by='popularity')
        site_options = [ s for s in sites_df['site'].unique() ]
        return site_options
    