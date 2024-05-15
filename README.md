# RestfulAPI-github-scraper
This project contains a RESTful API, using Python and Flask, that (partially) recreates some of the GitHub API endpoints. The information provided by the API is scraped on-demand from the GitHub website using Beautiful Soup. 

The Flask API is created in a file named github_api.py and exposes itself on the port specified by the GITHUB_API_PORT environment variable. This environment variable is not set by the code. The API relies on web scraping functions that are defined in a file named github_scraper.py. All python dependencies (as output by pip freeze) are specified in requirements.txt.

#!/usr/bin/env bash
SCRIPT="github_api.py"
TIMEOUT=30
PORT=23467
export GITHUB_API_PORT=$PORT
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python $SCRIPT &
while ! $(curl -s localhost:$PORT > /dev/null) && [ $TIMEOUT -gt 0 ]
do sleep 1; ((TIMEOUT--)); done
pkill -f $SCRIPT
deactivate
if [ $TIMEOUT -gt 0 ]; then echo "Verified"; else echo "Failed"; fi

    
The endpoints locations, query parameters, data types and response codes matches those of the GitHub API, but only certain endpoints and fields are implemented. The endpoints have been chosen such that there was no need to implement user authentication in the API. The project does not use the GitHub Octokit library, GitHub CLI or make requests to api.github.com.
