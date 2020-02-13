import requests
from requests.auth import HTTPBasicAuth
import json
from math import ceil
import time
import sys
import platform
import subprocess
## My GitHub Username and Password
username = ''
password = ''
targetUser = '' ## GitHub username of target user
targetRepo = '' ## GitHub Repo to target
if not username:
    username = input('Enter your github username: ')
if not password:
    password = input('Enter your github password(to authenticate with github api): ')
if not targetUser:
    targetUser = input('Enter user to target: ')
if not targetRepo:
    targetRepo = input('Enter repo to target: ')

## Other global variables
apicalls = 0
apicalls_left = 0
apicalls_reset = None
branches_ahead = 0
ahead_list = []

## command to clear terminal screen
clearScreen = "cls" if platform.system().lower()=="windows" else "clear"
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

## clear screen at beginning      
subprocess.call(clearScreen)
print("(screen has been cleared)")
print(f'targeted {targetUser}/{targetRepo}')
## Check number of repos of target user
aboutUser = fetch(f"https://api.github.com/users/{targetUser}")
try:
    if aboutUser["message"] == "Not Found":
        print("target user not found on Github")
        sys.exit()
except:
    pass

repoPages = ceil(aboutUser["public_repos"]/ 30) ##api shows only 30 results per page, so get no. of pages and  loop through them
for repoPageNum in range(1, repoPages + 1):
    ## try and get repo list of target user
    repoList = fetch(f"https://api.github.com/users/{targetUser}/repos?page={repoPageNum}")
    try:
        if repoList["message"] == "Not Found":
            print("target user not found on Github")
            sys.exit()
    except:
        pass

    for repo in repoList:
        if repo["name"] == targetRepo: ## if target repo
            forkPages = 1+int(repo["forks_count"]/ 30) ##api shows only 30 results per page, so get no. of pages and  loop through them
            for forkPageNum in range(1, forkPages + 1): ## iterate for each page
                forks = fetch(f'https://api.github.com/repositories/{repo["id"]}/forks?page={forkPageNum}')
                for fork in forks: ## for each fork
                    print(f'scanning fork: {fork["full_name"]}')
                    branches = fetch(f'https://api.github.com/repos/{fork["full_name"]}/branches')
                    try:
                        if branches["message"] == "Not Found":
                            #print("\nOwner of a fork seems to have deleted his account, skipping to next fork\n")
                            continue
                    except:
                        pass
                    for branch in branches: ## for each branch
                        isNewBranch = '' ## any branch in fork which isn't in original repo
                        result = fetch(f'https://api.github.com/repos/{fork["full_name"]}/compare/{targetUser}:{branch["name"]}...{branch["name"]}')
                        try:
                            if result["message"] == "Not Found":
                                ## branch with same name couldn't be found on original repo, so comparing with master
                                try:
                                    result = fetch(f'https://api.github.com/repos/{fork["full_name"]}/compare/{targetUser}:master...{branch["name"]}')
                                    #print("\nComparing with master branch of original repo cause same named branch couldn't be found\n")
                                    isNewBranch = '(new branch)'
                                except:
                                    continue ## branch in fork couldn't be compared, continuing to next branch
                        except:
                            pass
                        if result["total_commits"] > 0 and result["ahead_by"] > 0: ## The fork has some new commits and is ahead of original repo
                        #if result["total_commits"] > 0 and result["ahead_by"] > 0 and result["behind_by"] == 0: ##swap with above line to see forks strictly ahead
                            branches_ahead += 1
                            forkUrl = f'https://github.com/{fork["full_name"]}/commits/{branch["name"]} {isNewBranch}'
                            d = f'Ahead by {result["ahead_by"]}: {forkUrl}'
                            ahead_list.append(d)
            subprocess.call(clearScreen) ## clear screen before printing results
            print(f'forks in total: {repo["forks_count"]}')
            print(f'branches ahead: {branches_ahead}')
            print(f'api calls left: {int(apicalls_left)}')
            print(f'api limit will reset by: {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(float(apicalls_reset)))}')
            if ahead_list:
                print("")
            for i in range(len(ahead_list)):
                print(ahead_list[i])
            sys.exit() ## target repo has been scanned, so exit :)
