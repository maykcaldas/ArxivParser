import os
from github import Github
from github.Organization import Organization
from github import Auth

from dotenv import load_dotenv
load_dotenv()

def get_github_authentication():
    return Auth.Token(os.environ.get('GITHUB_ACCESS_TOKEN'))

def get_github_client():
    auth = get_github_authentication()
    return Github(auth=auth)

def open_issue_on_repo(repo_name, issue_title, issue_body):
    g = get_github_client()
    
    try:
        user = g.get_user()
        repo = g.get_repo(repo_name)

        repo.create_issue(title=issue_title, body=issue_body)
        g.close()
        print(f"Created issue on {repo_name} as {user.login}")
        
        return True
    except Exception as e:
        g.close()
        print(f"Error creating issue on {repo_name}: {e}")
        return False
