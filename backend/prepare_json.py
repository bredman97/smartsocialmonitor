import json

def get_policy_info(search = 'google.com'):
    list_of_rubric = []
    # Load the JSON file
    with open("privacyspy_products.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    for product in data:
        if search in [url for url in product.get('hostnames')]:
            company = product
            break
        else:
            company = None
        
    # if no company is found
    if not company:
        list_of_rubric.append(f" Scores for {search} are currently unavailable...")
        return list_of_rubric
    else:
        #create list w/ company score, name, rubric
        policy_score = f'{company.get('score')}'
        company_name = f'{company.get('name')}'
        list_of_rubric.append({'company': company_name})
        list_of_rubric.append({'policy_score':policy_score})
        rubric = company.get("rubric")

        #if no ruric found
        if not rubric:
            list_of_rubric.append({'error': f"No rubric information found for {search}..."})
        else:
            
            for item in rubric:
                
                question = item.get("question")

                #score is option as a percent x points
                score = (
                    item.get('option').get('percent') / 100
                    * question.get('points')
                    )
                list_of_rubric.append({
                    'question': question.get('text'),
                    'category': question.get('category').capitalize(),
                    'option': item.get('option').get('text'),
                    'percent': item.get('option').get('percent'),
                    'total_points': question.get('points'),
                    'citations': item.get('citations'),
                    'score': round(score)
                    })

        return list_of_rubric

#print(get_policy_info()[0])