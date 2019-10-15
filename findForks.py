import requests
from requests.auth import HTTPBasicAuth
import json
from math import ceil

## My GitHub Username and Password
username = ''
password = ''

## Global variables
apicalls = 0
apicalls_left = 0
apicalls_reset = None
branches_ahead = 0
ahead_list = []
targetUser = '' ## GitHub username of target user
targetRepo = '' ## GitHub Repo to target

## To connect to GitHub api
def fetch(url):
    global username
    global password
    global apicalls
    global apicalls_left
    global apicalls_reset
    try:
        #Github api req user-agent
        headers = {'User-Agent': 'Mozilla/5.0'}
        data = requests.get(url, auth=HTTPBasicAuth(username, password), timeout=15, headers=headers)
        apicalls += 1
        apicalls_left = data.headers["X-RateLimit-Remaining"]
        apicalls_reset = data.headers["X-RateLimit-Reset"]

        return json.loads(data.text)
    except Exception as e:
        print(e,url)

## try and get repo list of target user
repoList = fetch(f"https://api.github.com/users/{targetUser}/repos")
if isinstance(repoList,dict):
    try:
        if repoList["message"] == "Not Found":
            print("target user not found on Github")
    except:
        pass

for repo in repoList:
    if repo["name"] == targetRepo: ## if target repo
        pages = float(repo["forks_count"])/ 10 ## divide list of forks into small pages
        for l in range(1, int(ceil(pages)) + 1): ## iterate for each page
            forks = fetch(f'https://api.github.com/repositories/{repo["id"]}/forks?page={l}')
            for fork in forks: ## for each fork
                branches = fetch(f'https://api.github.com/repos/{fork["full_name"]}/branches')
                if(isinstance(branches,dict)):
                    try:
                        if branches["message"] == "Not Found":
                            print("\nOwner of a fork seems to have deleted his account, skipping to next fork\n")
                            continue
                    except:
                        pass
                for branch in branches: ## for each branch
                    #print(f'https://api.github.com/repos/{fork["full_name"]}/compare/{targetUser}:{branch["name"]}...{branch["name"]}')
                    result = fetch(f'https://api.github.com/repos/{fork["full_name"]}/compare/{targetUser}:{branch["name"]}...{branch["name"]}')
                    if(isinstance(result,dict)):
                        try:
                            if result["message"] == "Not Found":
                                continue ## branch with same name couldn't be found on original repo, skipping
                        except:
                            pass
##Below line ,if u want to compare any branch of fork with master branch of original repo
#result = fetch(f'https://api.github.com/repos/{fork["full_name"]}/compare/{targetUser}:master...{branch["name"]}')
                    if result["total_commits"] > 0 and result["ahead_by"] > 0: ## The fork has some new commits and is ahead of original repo
                        branches_ahead += 1
                        curl = f'https://github.com/{fork["full_name"]}/commits/{branch["name"]}'
                        d = f'{fork["full_name"]}:{branch["name"]} ahead by {result["ahead_by"]} at {curl}'
                        ahead_list.append(d)
        for i in range(len(ahead_list)):
            print(ahead_list[i])
            print("")
