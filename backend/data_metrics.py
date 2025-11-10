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
            elif search.split()[0] in product['name']:
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
        company_name = company['name']
        policy_score = company['score']
        company_slug = company['slug']
        hostnames = company['hostnames']
        
        list_of_rubric.append({'company': company_name})
        list_of_rubric.append({'policy_score':policy_score})
        list_of_rubric.append({'hostnames':hostnames})
        list_of_rubric.append({'company_slug': company_slug})

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
            return 'No match'
        
        # grabs first id - api data is already fuzzy search enabled
        # makes sure that it is the right search
        search_id=''
        for service in tosdr_search_json['services']:
            if service['name'].lower() == search.lower():
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
        else:
            return None

        # dictionary of useful data
        tosdr_data = {
            'name': tosdr_service_json['name'],
            'slug': tosdr_service_json['slug'],
            'rating': tosdr_service_json['rating'],
            'urls':tosdr_service_json['urls'], 
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
                
            
            for search in tosdr_search_json['services']:
                try:
                    
                    # sanitize unused entries
                    response.append(search['name'].title()) if (not 'deprecated' in search['name'].lower() or not 'deleted' in search['name'].lower()) and search['slug'] and search['rating'] != 'N/A' else ''
                except TypeError:
                    continue
            
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
        privacyspy_score = privacyspy_data[1]['policy_score'] if isinstance(privacyspy_data, list) else 0


        if tosdr_score == 0:
            overall_score = privacyspy_score
        elif privacyspy_score == 0:
            overall_score = tosdr_score
        elif tosdr_score == 0 and privacyspy_score == 0:
            overall_score = None
        else:
            overall_score = privacyspy_score + tosdr_score / 20

        return overall_score


