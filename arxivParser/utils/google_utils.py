import os
import pickle
import base64
import re
import email
import warnings
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow


# If modifying these SCOPES, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


def get_gmail_service():
    creds = None
    # Check if the token.pickle file exists
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If no valid credentials are available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Load the credentials from the downloaded JSON file
            flow = Flow.from_client_secrets_file(
                os.environ.get('GOOGLE_CREDENTIALS_PATH'),
                SCOPES,
                redirect_uri='urn:ietf:wg:oauth:2.0:oob')

            auth_url, _ = flow.authorization_url(prompt='consent')
            print('Please go to this URL and authorize the app:')
            print(auth_url)

            # Ask the user to enter the authorization code from the URL
            code = input('Enter the authorization code: ')
            flow.fetch_token(code=code)
            creds = flow.credentials

            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

    service = build('gmail', 'v1', credentials=creds)
    return service


def list_emails(n):
    service = get_gmail_service()
    # Call the Gmail API
    results = service.users().messages().list(userId='me', labelIds=['INBOX']).execute()
    messages = results.get('messages', [])
    return messages[:n]


def list_email_subjects(n):
    service = get_gmail_service()
    results = service.users().messages().list(userId='me', labelIds=['INBOX'], q="is:unread").execute()
    messages = results.get('messages', [])

    if not messages:
        raise Exception('No messages found.')
    else:
        subjects = []
        for message in messages[:n]:
            msg = service.users().messages().get(userId='me', id=message['id'], format='metadata', metadataHeaders=['Subject']).execute()
            subject = next(header['value'] for header in msg['payload']['headers'] if header['name'] == 'Subject')
            subjects.append(subject)


def get_email_content(n):
    service = get_gmail_service()
    results = service.users().messages().list(userId='me', labelIds=['INBOX']).execute()
    messages = results.get('messages', [])

    if not messages:
        print('No messages found.')
    else:
        for message in messages[:n]:
            msg = service.users().messages().get(userId='me', id=message['id'], format='full').execute()
            headers = msg['payload']['headers']
            from_header = next((item['value'] for item in headers if item['name'] == 'From'), None)
            if 'no-reply@arxiv.org' in from_header:
                data = msg['payload']['body']['data']
                content = base64.urlsafe_b64decode(data.encode('ASCII')).decode('utf-8')
                yield content


def get_arxiv_content(n, verbose=False):
    for email in get_email_content(n):
        papers = email.split("------------------------------------------------------------------------------")
        for paper in papers:
            desc = paper.split("\\")
            if len(desc) == 7:
                try:
                    _, _, header, _, abstract, _, doi = desc

                    header_fields = {
                        'arxiv': r"arXiv:(\S+)",
                        'date': r"Date: (.+?)\s+\(",
                        'title': r"Title: (.+)",
                        'authors': r"Authors: (.+)",
                        'categories': r"Categories: (.+)"
                    }
                    #TODO: It fails if ANY of fields is not found. Check if we can ignore some fields
                    extracted_data = {field: re.search(pattern, header).group(1).strip() for field, pattern in header_fields.items()}

                    abstract = abstract.replace("\r\n","").strip()

                    url_pattern = r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*'(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
                    doi = re.findall(url_pattern, doi)[0]
                except Exception as e:
                    url_pattern = r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*'(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
                    doi = re.findall(url_pattern, doi)[0]
                    if verbose:
                        warnings.warn(f"Error extracting data from email: {e}\nDOI: {doi}\n")
                    extracted_data = {}
                    extracted_data['title'] = None
                    extracted_data['authors'] = None
                    extracted_data['categories'] = None
                    abstract = None
                    data = None
                    doi = None
                    continue

                yield {
                    "title": extracted_data['title'],
                    "authors": extracted_data['authors'],
                    "categories": extracted_data['categories'],
                    "abstract": abstract,
                    "doi": doi,
                    "date": extracted_data['date'],
                }
