import urllib.parse
import requests
import time
from rapidfuzz import fuzz

class Controller:

    def __init__(self):
        #initialize class by getting full privacyspy json
        self.privacyspy = self.get_privacyspy_data()

    def get_privacyspy_data(self):
        #gets full privacyspy json
        PRIVACYSPY_URL = "https://privacyspy.org/api/v2/products.json"

        try:
            ps_response = requests.get(PRIVACYSPY_URL)
        
        # return none if getting link fails for endpoint
        except Exception:
            return None
        
        # return none if the get requests is not successful
        if ps_response.status_code == 200:
            privacyspy_data = ps_response.json()
        else:
            return None
        
        return privacyspy_data
    
    def get_privacyspy_info(self, search):
        '''
        search: (str)
        '''
        
        # Load the JSON file
        data = self.privacyspy

        # return msg if there are errors
        if not data:
            return None
        
        if not search:
            return None

        list_of_rubric = []

        company =''
    
        # if doesnt match on name then fuzzy search for match
        for product in data:
            if search.lower() == product['name'].lower():
                company = product
                break

            # only fuzzy search for first word in string as that tends to be parent company
            elif search.lower().split()[0] in product['name'].lower():
                fuzzy = fuzz.ratio(search.lower(), product['name'].lower())
                fuzzy1 = fuzz.partial_ratio(search.lower(), product['name'].lower())
                if fuzzy>=51 and fuzzy1>=87:
                    company = product
                    break
                
            
        # return msg if cannot find search in privacyspy
        if not company:
            return f"Analysis for {search.capitalize()} are currently unavailable..."
        
        while company['parent']:
            parent_name= company['parent']

            for product in data:
                if parent_name == product['slug']:
                    company = product
                    break

        
        # get all useful data
        
        list_of_rubric.append(
            {
            'company': company['name'],
            'policy_score': company['score'],
            'icon': company['icon'],
            'sources': company['sources']
            }
        )
        

        rubric = company['rubric']

        # check if there is a rubric for the search
        if not rubric:
            return f"{search} in data but no rubric information currently..."
        else:
            
            for item in rubric:
                
                question = item['question']
                score = (
                    item['option']['percent'] / 100
                    * question['points']
                    )
                list_of_rubric.append({
                    'question': question['text'],
                    'category': question['category'].capitalize(),
                    'option': item['option']['text'],
                    'percent': item['option']['percent'],
                    'total_points': question['points'],
                    'citations': item['citations'],
                    'score': round(score)
                    })

        return list_of_rubric
        
    def get_tosdr_data(self, search):
        '''
        search: (str)
        '''
        
        if not search:
            return None
        
        TOSDR_SERVICE_URL = "https://api.tosdr.org/service/v3?"
        TOSDR_SEARCH_URL = "https://api.tosdr.org/search/v5?"
        
        search_params = {'query': search}

        # check if search is in tosdr
        search_url = TOSDR_SEARCH_URL + urllib.parse.urlencode(search_params)

        # return none if search endpoint fails
        try:
            tosdr_search = requests.get(search_url)
        except Exception:
            return None

        # return none if request is unsuccessful
        if tosdr_search.status_code == 200:
            tosdr_search_json = tosdr_search.json()
        elif tosdr_search.status_code == 429:
            return 'Sent Too Many Requests...'
        else:
            return None
        
        # if succeeds but search is not in data then return msg
        if len(tosdr_search_json['services']) == 0:
            return 'No points available...'
        
        # grabs first id - api data is already fuzzy search enabled
        # makes sure that it is the right search
        search_id=''
        for service in tosdr_search_json['services']:
            if service['rating'] == 'N/A':
                continue
            elif service['name'].lower() == search.lower():
                search_id = service['id']
                break
            elif any(search.lower() in url.lower() for url in service['urls']):
                search_id = service['id']
                break

        id_params = {'id': search_id}
        
        service_url = TOSDR_SERVICE_URL + urllib.parse.urlencode(id_params)

        # return none if service url fails
        try:
            tosdr_service = requests.get(service_url)
        except Exception:
            return None
        
        #return none if request fails
        if tosdr_service.status_code == 200:
            tosdr_service_json = tosdr_service.json()
        elif tosdr_service.status_code == 429:
            return 'Sent Too Many Requests...'
        elif tosdr_service.status_code == 422:
            return 'No Points Available...'
        else:
            return None

        # dictionary of useful data
        tosdr_data = {
            'name': tosdr_service_json['name'],
            'rating': tosdr_service_json['rating'],
            'image':tosdr_service_json['image'], 
            'documents':tosdr_service_json['documents'],
            'points': tosdr_service_json['points']
        }
        
        return tosdr_data
    
    # gets list of all sites
    def get_site_list(self):
        TOSDR_ALLSERVICE_URL = "https://api.tosdr.org/service/v3?"

        params = {'page':1}

        response = []
        while True:
            # check if search is in tosdr
            service_url = TOSDR_ALLSERVICE_URL + urllib.parse.urlencode(params)
            time.sleep(1)
            # return none if search endpoint fails
            try:
                tosdr_search = requests.get(service_url)
            except Exception:
                return None

            # return none if request is unsuccessful
            if tosdr_search.status_code == 200:
                tosdr_search_json = tosdr_search.json()
            elif tosdr_search.status_code == 429: #too many requests so pause
                time.sleep(1)
                
            filtered_sites = [
                "YouPorn",
                "XVideos",
                "Pornhub",
                "Spankbang",
                "4porn",
                "Thumbzilla",
                "Rule34",
                "Danbooru",
                "FAKKU",
                "e621/e926",
                "CockFile",
                "OnlyFans",
                "Weasyl",
                "Pixiv",
                "Cock.li",
                "deprecated",
                "depricated",
                "deleted",
                "discontinued"

            ]

            for search in tosdr_search_json['services']:
                    
                # sanitize filtered entries
                if any(site.lower() in search['name'].lower() for site in filtered_sites):
                    continue

                if search['slug'] and search['rating'] != 'N/A':
                    response.append(search['name'].title())

            
            #pagination
            current_page = tosdr_search_json['page']['current']
            end_page = tosdr_search_json['page']['end']

            if current_page==end_page:
                break

            params['page'] +=1
        
        privacyspy_data = self.privacyspy

        # if entries already in list from tosdr then dont add
        for product in privacyspy_data:
           
            name = product['name'] if product['slug'] else ''

            if any(name.lower().split()[0] in res.lower() for res in response):
                continue
            else:
                response.append(product['name'].title()) if product['slug'] else ''
        
        response.sort()

        return response
    
    # turns tosdr grade into a num
    def grade_site(self, score):
        
        if score == 'A':
            return 9
        elif score == 'B':
            return 7
        elif score == 'C':
            return 5
        elif score == 'D':
            return 3
        elif score == 'E':
            return 1
        else:
            return 0
    
    # compute overall privacy score    
    def overall_privacy_score(self, privacyspy_data, tosdr_data ):
        '''
        privacyspy_data = (list)
        tosdr_data = (dict)
        '''

        tosdr_score = self.grade_site(tosdr_data['rating']) if isinstance(tosdr_data, dict) else 0
        privacyspy_score = privacyspy_data[0]['policy_score'] if isinstance(privacyspy_data, list) else 0

        if tosdr_score == 0:
            overall_score = privacyspy_score
        elif privacyspy_score == 0:
            overall_score = tosdr_score
        elif tosdr_score == 0 and privacyspy_score == 0:
            overall_score = None
        else:
            overall_score = (privacyspy_score + tosdr_score) / 2

        return overall_score
    
    #gets the logo of the chosen site
    def get_site_image(self, privacyspy_data, tosdr_data):
        
        if isinstance(tosdr_data, dict) and isinstance(privacyspy_data, list):
            image_url = tosdr_data['image']
            image_res = requests.get(image_url)
            if image_res.status_code == 200:
                return image_url
            else:
                image_url = 'https://privacyspy.org/static/icons/'
                return image_url + privacyspy_data[0]['icon']
        elif isinstance(tosdr_data, dict) and isinstance(privacyspy_data, str):
            image_url = tosdr_data['image']
            image_res = requests.get(image_url)
            if image_res.status_code == 200:
                return image_url
            else:
                return None
        elif isinstance(tosdr_data, str) and isinstance(privacyspy_data, list):
            url = 'https://privacyspy.org/static/icons/'
            return url + privacyspy_data[0]['icon']
        else:
            return None
    
    #gets the policy links of the chosen site
    def get_policy_urls(self, privacyspy_data, tosdr_data):

        if isinstance(tosdr_data, dict) and isinstance(privacyspy_data, list):
            policies = {}

            for doc in tosdr_data['documents']:
                policies[doc['name']] = doc['url']

            return policies
        elif isinstance(tosdr_data, dict) and isinstance(privacyspy_data, str):
            policies = {}

            for doc in tosdr_data['documents']:
                policies[doc['name']] = doc['url']

            return policies
        elif isinstance(privacyspy_data, list) and isinstance(tosdr_data, str):
            policies = {}

            for i, link in enumerate(privacyspy_data[0]['sources']):
                policies[f'Policy Link {i+1}'] = link

            return policies
        else:
            return None