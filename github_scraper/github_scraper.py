import requests
from bs4 import BeautifulSoup
import backoff

#Wrapper function for requests.get with exponential back-off on 429 responses (dealing wiithb rate-limit of GitHub)
@backoff.on_exception(backoff.expo, requests.exceptions.RequestException, max_tries=3)
def get_with_backoff(url, **kwargs):
    response = requests.get(url, **kwargs)
    response.raise_for_status()
    return response

def check_user_type(url):
    try:
        response = get_with_backoff(url)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return None
        if e.response.status_code == 304:
            return None
        raise

    #response = get_with_backoff(url)
    if response.status_code == 200:     #GitHub API documentation specified 200 as a successful response
        soup = BeautifulSoup(response.content, 'html.parser')

        #Extract user's type (user or organisation)
        user_type_element = soup.find('div', class_='h-card mt-md-n5')
        if user_type_element is not None:
            user_type = 1
        else:
            user_type = 0

        return user_type
    else:
        return None

#Function for GET /users/{username}
def scrape_github_users_endpoint(url,username):
    try:
        response = get_with_backoff(url)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return None
        if e.response.status_code == 304:
            return None
        raise
    
    #response = get_with_backoff(url)
    if response.status_code == 200:     #GitHub API documentation specified 200 as a successful response
        soup = BeautifulSoup(response.content, 'html.parser')

        #Extract user's type (user or organisation)
        user_type_element = soup.find('div', class_='h-card mt-md-n5')
        if user_type_element is not None:
            user_data = scrape_person_user(soup,url,username)
        else:
            user_data = scrape_org_user(soup,url,username)

        return user_data
    else:
        return None
    
def scrape_person_user(soup,url, username):
    #Extract the user's login
    login_element = soup.find('span',class_='p-nickname vcard-username d-block', itemprop= 'additionalName')
    user_login = login_element.text.strip() if login_element else None

    #Extract user's id
    data_element = soup.find('a', itemprop= 'image')
    data = data_element["href"] if data_element else None

    # Extracting the specific substring from the user's blog URL
    if data is not None:
        # Extracting the numeric value after the last '/'
        data_parts = data.split('/')
        last_part = data_parts[-1]
        
        # If the last part has a query parameter (?v=4), remove it
        last_part = last_part.split('?')[0]
        
        # Try to convert the last part to an integer
        try:
            extracted_number = int(last_part)
            user_id = extracted_number
        except ValueError:
            user_id = None

    #Extract user's avatar_url
    avatar_element = soup.find('a', itemprop= 'image')
    user_avatar_url = avatar_element["href"] if avatar_element else None

    #Extract user's url
    user_url = f"https://api.github.com/users/{username}"

    #Extract user's html_url
    user_html_url = url

    #Extract user's type
    user_type = "User"

    #Extract user's name
    full_name_element = soup.find('span', class_= 'p-name vcard-fullname d-block overflow-hidden', itemprop = 'name')
    user_name = full_name_element.text.strip() if full_name_element else None
        
    #Extract user's company
    company_element = soup.find('span', class_='p-org')
    user_company = company_element.text.strip() if company_element else None

    #Extract user's blog
    blog_element = soup.find('li', itemprop= 'url')
    user_blog = blog_element.find('a') if blog_element else None
    user_blog = user_blog.text.strip() if user_blog else None

    #Extract user's location
    location_element = soup.find('li', itemprop = 'homeLocation')
    user_location = location_element.find('span') if location_element else None
    user_location = user_location.text.strip() if user_location else None

    #Extract user's bio
    bio_element = soup.find('div', class_ = 'p-note user-profile-bio mb-3 js-user-profile-bio f4')
    user_bio = bio_element.find('div') if bio_element else None
    user_bio = user_bio.text.strip() if user_bio else None

    #Extract user's twitter_username
    twitter_handle_element = soup.find('a', href=lambda href: href and 'twitter.com' in href)
    user_twitter = twitter_handle_element.text.strip() if twitter_handle_element else None

    #Extract user's public_repos
    number_public_repo_element = soup.find('a', href = f'/{username}?tab=repositories')
    user_repos = number_public_repo_element.find('span') if number_public_repo_element else None
    user_repos = user_repos.text.strip() if user_repos else None
    if user_repos is not None:
        user_repos = convert_k_to_zeros(user_repos)

    #Extract user's followers
    number_followers_element = soup.find('a', href= f'https://github.com/{username}?tab=followers')
    user_followers = number_followers_element.find('span') if number_followers_element else None
    user_followers = user_followers.text.strip() if user_followers else None
    if user_followers is not None:
        user_followers = convert_k_to_zeros(user_followers)

    #Extract user's follwing
    number_following_element = soup.find('a', href= f'https://github.com/{username}?tab=following')
    user_following = number_following_element.find('span') if number_following_element else None
    user_following = user_following.text.strip() if user_following else None
    if user_following is not None:
            user_following = convert_k_to_zeros(user_following)

    user_data = {"login": user_login, "id": user_id, "avatar_url": user_avatar_url, "url": user_url, "html_url": user_html_url, "type": user_type, "name": user_name, "company": user_company, "blog": user_blog, "location": user_location, "bio": user_bio, "twitter_username": user_twitter, "public_repos": user_repos, "followers": user_followers, "following": user_following}
    
    return user_data


def scrape_org_user(soup, url, username):
    #Extract the user's login
    login_element = soup.find('meta', {'property': 'profile:username'})
    user_login = login_element["content"] if login_element else None

    #Extract user's id
    data_element = soup.find('img', itemprop= 'image')
    data = data_element["src"] if data_element else None
    
    if data is not None:
        # Extracting the numeric value after the last '/'
        data_parts = data.split('/')
        last_part = data_parts[-1]

        # If the last part has a query parameter (?v=4), remove it
        last_part = last_part.split('?')[0]
        
        # Try to convert the last part to an integer
        try:
            extracted_number = int(last_part)
            user_id = extracted_number
        except ValueError:
            user_id = None

    #Extract user's avatar_url
    avatar_element = soup.find('img', itemprop= 'image')
    user_avatar_url = avatar_element["src"] if avatar_element else None

    #Extract user's url
    user_url = f"https://api.github.com/users/{username}"

    #Extract user's html_url
    url_element = soup.find('meta', {'property': 'og:url'})
    user_html_url = url_element["content"] if url_element else None

    #Extract user's type
    user_type = "Organization"
    
    #Extract user's name
    full_name_element = soup.find('h1', class_= 'h2 lh-condensed')
    user_name = full_name_element.text.strip() if full_name_element else None

    #Extract user's company
    user_company = None

    #Extract user's blog
    blog_element = soup.find('a', itemprop= 'url')
    user_blog = blog_element["href"] if blog_element else None

    #Extract user's location
    location_element = soup.find('span', itemprop = 'location')
    user_location = location_element.text.strip() if location_element else None

    #Extract user's bio
    bio_element = soup.find('div', class_ = 'color-fg-muted')
    user_bio = bio_element.find('div') if bio_element else None
    user_bio = user_bio.text.strip() if user_bio else None

    #Extract user's twitter_username
    twitter_handle_element = soup.find('a', href=lambda href: href and 'twitter.com' in href)
    user_twitter = twitter_handle_element.text.strip() if twitter_handle_element else None

    #Extract user's public_repos
    number_public_repo_element = soup.find('a',href=lambda href: href and 'repositories' in href)
    number_public_repo_element = number_public_repo_element.find('span',class_='Counter js-profile-repository-count') if number_public_repo_element else None
    user_repos = number_public_repo_element.text.strip() if number_public_repo_element else None
    # if user_repos is not None:
    #     user_repos = convert_k_to_zeros(user_repos)

    #Extract user's followers
    number_followers_element = soup.find('a', href=lambda href: href and 'followers' in href)
    user_followers = number_followers_element.find('span') if number_followers_element else None
    user_followers = user_followers.text.strip() if user_followers else None
    if user_followers is not None:
        user_followers = convert_k_to_zeros(user_followers)

    #Extract user's follwing
    user_following = 0

    user_data = {"login": user_login, "id": user_id, "avatar_url": user_avatar_url, "url": user_url, "html_url": user_html_url, "type": user_type, "name": user_name, "company": user_company, "blog": user_blog, "location": user_location, "bio": user_bio, "twitter_username": user_twitter, "public_repos": user_repos, "followers": user_followers, "following": user_following}

    return user_data

#Function for GET /users/{username}/repos for user
def scrape_user_repo(url,username,per_page,sort_by,direction,page):
    response = get_with_backoff(url)
    if response.status_code == 200:     #GitHub API documentation specified 200 as a successful response
        soup = BeautifulSoup(response.content, 'html.parser')
        user_repo_list = []
        repos_list = soup.find_all('li', class_='col-12 d-flex flex-justify-between width-full py-4 border-bottom color-border-muted public source' )

        if sort_by == 'full_name':
            key_function = lambda x: x.find('a').text.strip().lower()
        elif sort_by == 'pushed':
            key_function = lambda x: x.find('relative-time')['datetime']

        sorted_repos_list = sorted(repos_list, key=key_function, reverse=(direction == 'desc'))

        start_index = (page - 1) * per_page
        end_index = start_index + per_page

        for repo_element in sorted_repos_list[start_index:end_index]:
            repo = {}

            #Extract repos' name and full name
            name_element = repo_element.find('a', itemprop= 'name codeRepository')
            repo['name'] = name_element.text.strip() if name_element else None
            repo['full_name'] = name_element["href"] if name_element else None

            #Extract repos' owner (i.e. owner id and owner login)
            owner_login = username
            data_element = soup.find('a', itemprop= 'image')
            data = data_element["href"] if data_element else None
            # Extracting the specific substring from the user's blog URL
            if data is not None:
            # Extracting the numeric value after the last '/'
                data_parts = data.split('/')
                last_part = data_parts[-1]
            
            # If the last part has a query parameter (?v=4), remove it
                last_part = last_part.split('?')[0]
            
            # Try to convert the last part to an integer
                try:
                    extracted_number = int(last_part)
                    owner_id = extracted_number
                except ValueError:
                    owner_id = None
            repo['owner'] ={"login": owner_login, "id": owner_id}

            #Extract repos' html url
            html_element = repo_element.find('a', itemprop= 'name codeRepository')
            html_url = html_element["href"] if html_element else None
            repo['html_url'] = f'https://github.com{html_url}'

            # Creating 2nd layer of scraper url to scrape data from each repo's endpoint
            layered_url = f'https://github.com{html_url}'

            #Extract repos' id
            id = scrape_repo_id(layered_url)
            repo['id'] = int(id)

            #Extract repos' private
            private_element = repo_element.find('span', class_='Label Label--secondary v-align-middle ml-1 mb-1')
            checker = private_element.text.strip() if private_element else None
            if checker == 'Public':
                repo['private'] = bool(1)
            else:
                repo['private'] = bool(0)

            #Extract repos' description
            description_element = repo_element.find('p', itemprop='description')
            repo['description'] = description_element.text.strip() if description_element else None

            #Extract repos' fork
            fork = scrape_repo_fork(layered_url)
            if fork is not None:
                repo['fork'] = bool(fork)
            else:
                repo['fork'] = None

            #Extract repos' url
            url_element = repo_element.find('a', itemprop= 'name codeRepository')
            url = html_element['href'] if html_element else None
            repo['url'] = f'https://api.github.com/repos{url}'

            #Extract repos' homepage
            homepage = scrape_repo_homepage(layered_url)
            repo['homepage'] = homepage

            #Extract repos' language
            language_element = repo_element.find('span', itemprop='programmingLanguage')
            repo['language'] = language_element.text.strip() if language_element else None

            #Extract repos' forks count
            forks_num = scrape_repo_forks_count(layered_url)
            if forks_num is not None:
                repo['forks_count'] = convert_k_to_zeros(forks_num)
            else:
                repo['forks_count'] = None

            #Extract repos' stargazers count
            stargazers_num = scrape_repo_stargazers_count(layered_url)
            if stargazers_num is not None:
                repo['stargazers_count'] = convert_k_to_zeros(stargazers_num)
            else:
                repo['stargazers_count'] = None

            #Extract repos' watchers count
            if stargazers_num is not None:
                repo['watchers_count'] = convert_k_to_zeros(stargazers_num)
            else:
                repo['watchers_count'] = None

            #Extract repos' default branch
            default_branch = scrape_repo_default_branch(layered_url)
            repo['default_branch'] = default_branch

            #Extract repos' open issues count and has_issues field
            open_issues_num = scrape_repo_open_issues_count(layered_url)
            if open_issues_num is not None:
                open_issues_num = convert_k_to_zeros(open_issues_num)
                repo['open_issues_count'] = open_issues_num
                #repo['open issues count'] = open_issues_num
                if open_issues_num > 0:
                    repo['has_issues'] = bool(1)
                else:
                    repo['has_issues'] = bool(0)
            else:
                repo['open issues count'] = None
                repo['has_issues'] = None

            #Extract repos' topics
            topics = []
            topic_elements = repo_element.find_all('a', class_='topic-tag topic-tag-link f6 my-1')
            for topic_elem in topic_elements:
                topics.append(topic_elem.text.strip())
            repo['topics'] = topics

            #Extract repos' has projects
            projects_num = scrape_repo_has_projects(layered_url)
            if projects_num is not None:
                projects_num = convert_k_to_zeros(projects_num)
                if projects_num > 0:
                    repo['has_projects'] = bool(1)
                else:
                    repo['has_projects'] = bool(0)
            else:
                repo['has_projects'] = None

            #Extract repos' has discussions
            discussions = scrape_repo_discussions(layered_url)
            if discussions is not None:
                repo['has_discussions'] = bool(1)
            else:
                repo['has_discussions'] = bool(0)    

            #Extract repos' archived
            archive_element = repo_element.find('span', class_='Label Label--secondary v-align-middle ml-1 mb-1')
            archive_element = private_element.text.strip() if archive_element else None
            checker = "archive"
            if archive_element is not None:
                if checker in archive_element:
                    repo['archived'] = bool(1)
                else:
                    repo['archived'] = bool(0)
            
            #Extract repos' pushed at date
            pushed_element = repo_element.find('relative-time')
            repo['pushed_at'] = pushed_element["datetime"] if pushed_element else None
    
            user_repo_list.append(repo)
        return user_repo_list
    else:
        return None
    
#Function for GET /users/{username}/repos for organisations
def scrape_org_repo(url,username,per_page,sort_by,direction,page):
    response = get_with_backoff(url)
    if response.status_code == 200:     #GitHub API documentation specified 200 as a successful response
        soup = BeautifulSoup(response.content, 'html.parser')
        org_repo_list = []
        repos_list = soup.find_all('li', class_='Box-row' )

        if sort_by == 'full_name':
            key_function = lambda x: x.find('a').text.strip().lower()
        elif sort_by == 'pushed':
            key_function = lambda x: x.find('relative-time')['datetime']

        sorted_repos_list = sorted(repos_list, key=key_function, reverse=(direction == 'desc'))

        start_index = (page - 1) * per_page
        end_index = start_index + per_page

        for repo_element in sorted_repos_list[start_index:end_index]:
            repo = {}

            #Extract repos' name and full name
            name_element = repo_element.find('a', itemprop= 'name codeRepository')
            repo['name'] = name_element.text.strip() if name_element else None
            repo['full_name'] = name_element["href"] if name_element else None

            #Extract repos' owner (i.e. owner id and owner login)
            login_element = soup.find('a', class_='color-fg-default no-underline')
            user_login = login_element["data-name"] if login_element else None

            data_element = soup.find('img', itemprop= 'image')
            data = data_element["src"] if data_element else None
            
            if data is not None:
                # Extracting the numeric value after the last '/'
                data_parts = data.split('/')
                last_part = data_parts[-1]

                # If the last part has a query parameter (?v=4), remove it
                last_part = last_part.split('?')[0]
                
                # Try to convert the last part to an integer
                try:
                    extracted_number = int(last_part)
                    user_id = extracted_number
                except ValueError:
                    user_id = None

            #Extract repos' html url
            html_element = repo_element.find('a', itemprop= 'name codeRepository')
            html_url = html_element["href"] if html_element else None
            repo['html_url'] = f'https://github.com{html_url}'

            # Creating 2nd layer of scraper url to scrape data from each repo's endpoint
            layered_url = f'https://github.com{html_url}'

            #Extract repos' private
            private_element = repo_element.find('span', class_='Label Label--secondary v-align-middle ml-1 mb-1')
            checker = private_element.text.strip() if private_element else None
            if checker == 'Public':
                repo['private'] = bool(1)
            else:
                repo['private'] = bool(0)

            #Extract repos' description
            description_element = repo_element.find('p', itemprop='description')
            repo['description'] = description_element.text.strip() if description_element else None

            #Extract repos' fork
            fork = scrape_repo_fork(layered_url)
            if fork is not None:
                repo['fork'] = bool(fork)
            else:
                repo['fork'] = None

            #Extract repos' url
            url_element = repo_element.find('a', itemprop= 'name codeRepository')
            url = html_element['href'] if html_element else None
            repo['url'] = f'https://api.github.com/repos{url}'

            #Extract repos' homepage
            homepage = scrape_repo_homepage(layered_url)
            repo['homepage'] = homepage

            #Extract repos' language
            language_element = repo_element.find('span', itemprop='programmingLanguage')
            repo['language'] = language_element.text.strip() if language_element else None

            #Extract repos' forks count
            forks_num = scrape_repo_forks_count(layered_url)
            if forks_num is not None:
                repo['forks_count'] = convert_k_to_zeros(forks_num)
            else:
                repo['forks_count'] = None

            #Extract repos' stargazers count
            stargazers_num = scrape_repo_stargazers_count(layered_url)
            if stargazers_num is not None:
                repo['stargazers_count'] = convert_k_to_zeros(stargazers_num)
            else:
                repo['stargazers_count'] = None

            #Extract repos' watchers count
            if stargazers_num is not None:
                repo['watchers_count'] = convert_k_to_zeros(stargazers_num)
            else:
                repo['watchers_count'] = None
            

            #Extract repos' default branch
            default_branch = scrape_repo_default_branch(layered_url)
            repo['default_branch'] = default_branch

            #Extract repos' open issues count and has_issues field
            open_issues_num = scrape_repo_open_issues_count(layered_url)
            if open_issues_num is not None:
                open_issues_num = convert_k_to_zeros(open_issues_num)
                repo['open_issues_count'] = open_issues_num
                if open_issues_num > 0:
                    repo['has_issues'] = bool(1)
                else:
                    repo['has_issues'] = bool(0)
            else:
                repo['open issues count'] = 0
                repo['has_issues'] = bool(0)

            #Extract repos' topics
            topics = []
            topic_elements = repo_element.find_all('a', class_='topic-tag topic-tag-link f6 my-1')
            for topic_elem in topic_elements:
                topics.append(topic_elem.text.strip())
            repo['topics'] = topics

            #Extract repos' has projects
            projects_num = scrape_repo_has_projects(layered_url)
            if projects_num is not None:
                projects_num = convert_k_to_zeros(projects_num)
                if projects_num > 0:
                    repo['has_projects'] = bool(1)
                else:
                    repo['has_projects'] = bool(0)
            else:
                repo['has_projects'] = None

            #Extract repos' has discussions
            discussions = scrape_repo_discussions(layered_url)
            if discussions is not None:
                repo['has_discussions'] = bool(1)
            else:
                repo['has_discussions'] = bool(0)

            #Extract repos' archived
            archive_element = repo_element.find('span', class_='Label Label--secondary v-align-middle ml-1 mb-1')
            archive_element = private_element.text.strip() if archive_element else None
            checker = "archive"
            if archive_element is not None:
                if checker in archive_element:
                    repo['archived'] = bool(1)
                else:
                    repo['archived'] = bool(0)

            #Extract repos' pushed at date
            pushed_element = repo_element.find('relative-time')
            repo['pushed_at'] = pushed_element["datetime"] if pushed_element else None

            org_repo_list.append(repo)
        return org_repo_list
    else:
        return None

    
def scrape_repo_homepage(url):
    response = get_with_backoff(url)
    if response.status_code == 200:     #GitHub API documentation specified 200 as a successful response
        soup = BeautifulSoup(response.content, 'html.parser')
        homepage_element = soup.find('a',class_= 'mr-lg-3 color-fg-inherit flex-order-2', )
        homepage = homepage_element.text.strip() if homepage_element else None
        return homepage
    else:
        return None

def scrape_repo_discussions(url):
    response = get_with_backoff(url)
    if response.status_code == 200:     #GitHub API documentation specified 200 as a successful response
        soup = BeautifulSoup(response.content, 'html.parser')
        discussions_element = soup.find('a', id="discussions-tab")
        return discussions_element
    else:
        return None
    
def scrape_repo_fork(url):
    response = get_with_backoff(url)
    if response.status_code == 200:     #GitHub API documentation specified 200 as a successful response
        soup = BeautifulSoup(response.content, 'html.parser')
        fork_element = soup.find('meta', {'name': 'octolytics-dimension-repository_is_fork'})
        fork = fork_element["content"] if fork_element else None
        if fork == 'true':
            fork = 1
        else:
            fork = 0
        return fork
    else:
        return None 

def scrape_repo_id(url):
    response = get_with_backoff(url)
    if response.status_code == 200:     #GitHub API documentation specified 200 as a successful response
        soup = BeautifulSoup(response.content, 'html.parser')
        id_element = soup.find('meta', {'name': 'octolytics-dimension-repository_network_root_id'})
        id = id_element["content"] if id_element else None
        return id
    else:
        return None

def scrape_repo_forks_count(url):
    response = get_with_backoff(url)
    if response.status_code == 200:     #GitHub API documentation specified 200 as a successful response
        soup = BeautifulSoup(response.content, 'html.parser')
        forks_count_element = soup.find('span', id= 'repo-network-counter')
        forks_num = forks_count_element.text.strip() if forks_count_element else None
        return forks_num
    else:
        return None

    
def scrape_repo_stargazers_count(url):
    response = get_with_backoff(url)
    if response.status_code == 200:     #GitHub API documentation specified 200 as a successful response
        soup = BeautifulSoup(response.content, 'html.parser')
        stargazers_element = soup.find('span', id='repo-stars-counter-star')
        stargazers_num = stargazers_element.text.strip() if stargazers_element else None
        return stargazers_num
    else:
        return None
    

def scrape_repo_has_projects(url):
    response = get_with_backoff(url)
    if response.status_code == 200:     #GitHub API documentation specified 200 as a successful response
        soup = BeautifulSoup(response.content, 'html.parser')
        projects_element = soup.find('span', id='projects-repo-tab-count',hidden='hidden', class_='Counter')
        projects_num = projects_element.text.strip() if projects_element else 0 #or NONE
        return projects_num
    else:
        return None

def scrape_repo_default_branch(url):
    response = get_with_backoff(url)
    if response.status_code == 200:     #GitHub API documentation specified 200 as a successful response
        soup = BeautifulSoup(response.content, 'html.parser')
        default_element = soup.find('span', class_='css-truncate-target')
        default_branch = default_element.text.strip() if default_element else None
        return default_branch
    else:
        return None
    
def scrape_repo_open_issues_count(url):
    response = get_with_backoff(url)
    if response.status_code == 200:     #GitHub API documentation specified 200 as a successful response
        soup = BeautifulSoup(response.content, 'html.parser')
        open_issues_element = soup.find('span', id='issues-repo-tab-count')
        open_issues_num = open_issues_element.text.strip() if open_issues_element else None
        return open_issues_num
    else:
        return None

def convert_k_to_zeros(input_str):
    if 'k' in str(input_str):
        number_part = str(input_str).replace('k', '')  # Remove 'k' from the string

        try:
            number = float(number_part) * 1000  # Convert to an integer and multiply by 1000
            return int(number)
        except ValueError:
            return 0
    else:
        number = int(input_str)
        return number