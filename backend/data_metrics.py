import urllib.parse
import requests

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
        
        # Load the JSON file
        data = self.privacyspy

        # return msg if there are errors
        if not data:
            return None
        
        if not search or not search.isalpha():
            return None
        

        list_of_rubric = []

        # check if search is in the hostnames 
        # different domains share same policy in some cases
        for product in data:
            hostnames = product.get('hostnames')
            if any(search.lower() in url for url in hostnames):
                company = product
                break
            else:
                company = None

            
        # return msg if cannot find search in privacyspy
        if not company:
            return f"Analysis for {search.capitalize()} are currently unavailable..."
        
        else:
            # get all useful data
            company_name = company['name']
            policy_score = company['score']
            hostnames = company['hostnames']
            
            list_of_rubric.append({'company': company_name})
            list_of_rubric.append({'policy_score':policy_score})
            list_of_rubric.append({'hostnames':hostnames})

            rubric = company['rubric']

            # check if there is a rubric for the search
            if not rubric:
                return f"{search.capitalize()} in data but no rubric information currently..."
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

        if not search or not search.isalpha():
            return None
        

        TOSDR_SERVICE_URL = "https://api.tosdr.org/service/v3?"
        TOSDR_SEARCH_URL = "https://api.tosdr.org/search/v5?"
        
        search_params = {'query':search}

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

        for service in tosdr_search_json['services']:
            if service['slug'] == search:
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
            'rating': tosdr_service_json['rating'],
            'urls':tosdr_service_json['urls'], 
            'points': tosdr_service_json['points']
        }
        
        return tosdr_data
    
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
