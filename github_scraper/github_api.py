import os
from flask import Flask, jsonify, request
import github_scraper

app = Flask(__name__)

@app.route('/users/<username>', methods =['GET'])
def get_user(username):  
    url_scrape = f'https://github.com/{username}'
    user_data = github_scraper.scrape_github_users_endpoint(url_scrape,username)
    if user_data is not None:
        return jsonify(user_data)
    else:
        error_return = {"message": "Not Found", "documentation_url" : "https://docs.github.com/rest/users/users#get-a-user"}
        return jsonify(error_return), 404

@app.route('/users/<username>/repos', methods=['GET'])
def get_user_repos(username): 
    per_page = int(request.args.get('per_page', 30))    # According to API: default to 30 repos

    # Default to sorting by full_name
    sort_by = request.args.get('sort', 'full_name')     # According to API: default to full_name 

    page = int(request.args.get('page', 1))  # According to API: default to 1

    if sort_by not in ['full_name', 'pushed']:
        return jsonify({"error": "Invalid sort parameter. Use 'full_name' or 'pushed'."}), 400

    if sort_by == 'full_name':
        direction = request.args.get('direction', 'asc')  # According to API: default to ascending (in case of full_name)
    
    if sort_by == 'pushed':
        direction = request.args.get('direction', 'desc')  # According to API: default to descending (in case of pushed_date)
    
    if direction not in ['asc', 'desc']:
        return jsonify({"error": "Invalid direction parameter. Use 'asc' or 'desc'."}), 400
    
    #First check whether the user is a person/organisation 
    url_type_check = f'https://github.com/{username}'
    user_type = github_scraper.check_user_type(url_type_check)
    if user_type is not None:
        #If the user is a person
        if user_type == 1:
            url_scrape = f'https://github.com/{username}?tab=repositories'
            repo_data = github_scraper.scrape_user_repo(url_scrape,username,per_page,sort_by,direction,page)
        #If the user is an organisation
        elif user_type == 0:
            url_scrape = f'https://github.com/orgs/{username}/repositories'
            repo_data = github_scraper.scrape_org_repo(url_scrape,username,per_page,sort_by,direction,page)
        
        return jsonify(repo_data)
    else:
        error_return = {"message": "Not Found", "documentation_url" : "https://docs.github.com/rest/users/users#get-a-user"}
        return jsonify(error_return), 404

if __name__ == '__main__':
    port = int(os.environ.get('GITHUB_API_PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
