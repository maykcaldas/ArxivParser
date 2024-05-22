import os
import pytz
from notion_client import Client
from datetime import datetime


def get_notion_service():
    return Client(auth=os.environ.get('NOTION_SECRET'))


def update_page(page_id, properties, database_id=os.environ.get('NOTION_DATABASE_ID')):
    notion = get_notion_service()
    notion.pages.update(
        page_id=page_id,
        properties=properties
    )

def query_database(query, database_id=os.environ.get('NOTION_DATABASE_ID')):
    notion = get_notion_service()
    return notion.databases.query(
        **{
            "database_id": database_id,
            **query
        }
    )


def set_page_curated(page_id, database_id=os.environ.get('NOTION_DATABASE_ID')):
    notion = get_notion_service()
    notion.pages.update(
        page_id=page_id,
        properties={
            "Curated": {
                "checkbox": True
            }
        }
    )
    print("Page updated successfully.")



def get_all_pages(database_id=os.environ.get('NOTION_DATABASE_ID')):
    return query_database({}, database_id=database_id)


def get_all_arxiv_pages(database_id=os.environ.get('NOTION_DATABASE_ID')):
    return query_database({
        "filter": {
            "property": "Paper",
            "url": {
                "contains": "arxiv"
            }
        }
    }, database_id=database_id)['results']


def get_all_curated_pages(database_id=os.environ.get('NOTION_DATABASE_ID')):
    return query_database({
        "filter": {
            "property": "Curated",
            "checkbox": {
                "equals": True
            }
        }
    }, database_id=database_id)['results']


def get_page_by_url(url, database_id=os.environ.get('NOTION_DATABASE_ID')):
    return query_database({
        "filter": {
            "property": "Paper",
            "url": {
                "equals": url
            }
        }
    }, database_id=database_id)['results']


def get_page_by_doi(doi, database_id=os.environ.get('NOTION_DATABASE_ID')):
    return query_database({
        "filter": {
                "property": "DOI",
                "title": {
                    "equals": doi
                }
        }
    }, database_id=database_id)['results']


def create_page(data, database_id=os.environ.get('NOTION_DATABASE_ID')):
    notion = get_notion_service()
    
    date_format = "%a, %d %b %Y %H:%M:%S %Z"
    date_obj = datetime.strptime(data['date'], date_format)
    date_obj = date_obj.replace(tzinfo=pytz.UTC)  # Ensure the datetime is timezone-aware
    iso_date = date_obj.isoformat()

    # Creating a new page in the database
    new_page = notion.pages.create(parent={"database_id": database_id}, properties={
        "DOI": {
            "title": [
                {"text": {"content": data['doi']}}
            ]
        },
        "Title": {
            "rich_text": [
                {"text": {"content": data['title']}}
            ]
        },
        "Categories": {
            "multi_select": [
                {"name": category} for category in data['categories']
            ]
        },
        "Authors": {
            "rich_text": [
                {"text": {"content": data['authors']}}
            ]
        },
        "Abstract": {
            "rich_text": [
                {"text": {"content": data['abstract']}}
            ]
        },
        "Date": {
            "date": {"start": iso_date}
        },
        # "Architecture": {
        #     "multi_select": [
        #         {"name": architecture} for architecture in data['architecture']
        #     ]
        # },
        # "Checked": {
        #     "checkbox": False
        # }
        # "Paper": {
        #     "url": data['paper']
        # },
        # "Repository": {
        #     "url": data['repository']
        # },
        # "Tags": {
        #     "multi_select": [
        #         {"name": tag['name']} for tag in data['tags']
        #     ]
        # },
        # "Parameters": {
        #     "rich_text": [
        #         {"text": {"content": data['parameters']}}
        #     ]
        # },
        # "Dataset": {
        #     "rich_text": [
        #         {"text": {"content": data['dataset']}}
        #     ]
        # },
        # "Task": {
        #     "multi_select": [
        #         {"name": task['name']} for task in data['task']
        #     ]
        # },
        # "Notes": {
        #     "rich_text": [
        #         {"text": {"content": data['notes']}}
        #     ]
        # },
    })

    print("Page created successfully.")



######################################################
#
############## Deprecated functions #################
#
######################################################

def create_notion_entry(entry, database_id=os.environ.get('NOTION_DATABASE_ID')):
    notion = get_notion_service()
    
    # date_format = "%a, %d %b %Y %H:%M:%S %Z"
    # date_obj = datetime.strptime(entry['date'], date_format)
    # date_obj = date_obj.replace(tzinfo=pytz.UTC)  # Ensure the datetime is timezone-aware
    # iso_date = date_obj.isoformat()

    # Creating a new page in the database
    new_page = notion.pages.create(parent={"database_id": database_id}, properties={
        "Title": {
            "rich_text": [
                {"text": {"content": entry['title'][6:]}}
            ]
        },
        "DOI": {
            "title": [
                {"text": {"content": entry['paper']}}
            ]
        },
        "Abstract": {
            "rich_text": [
                {"text": {"content": entry['abstract'].split(":")[1]}}
            ]
        },
        "Architecture": {
            "multi_select": [
                {"name": architecture} for architecture in entry['architecture']
            ]
        },
        "Date": {
            "date": {"start": entry['date']}
        },
        "Tags": {
            "multi_select": [
                {"name": tag['name']} for tag in entry['tags']
            ]
        },
        "Parameters": {
            "rich_text": [
                {"text": {"content": entry['parameters']}}
            ]
        },
        "Dataset": {
            "rich_text": [
                {"text": {"content": entry['dataset']}}
            ]
        },
        "Task": {
            "multi_select": [
                {"name": task['name']} for task in entry['task']
            ]
        },
        "Paper": {
            "url": entry['paper']
        },
        "Repository": {
            "url": entry['repository']
        },
        "Notes": {
            "rich_text": [
                {"text": {"content": entry['notes']}}
            ]
        },
        "Curated": {
            "checkbox": True
        }
    })

    print("Page created successfully.")


def update_arxiv_papers():
    '''
    This function gets arxiv urls and updates the database with the title and abstract of the paper.
    This is not used in the app workflow, but is useful for porting data from one database to another.
    '''
    db_id = os.environ.get('OLD_NOTION_DATABASE_ID')

    import requests
    import bs4 as bs

    pages = get_all_pages(db_id)['results']
    for paper in pages:
        url = paper['properties']['Paper']['url']
        if not url or not 'arxiv' in url:
            continue
        paper_id = get_page_id_by_url(url, database_id=db_id)

        response = requests.get(url)
        soup = bs.BeautifulSoup(response.text, 'html.parser')
        with open('test.html', 'w') as f:
            f.write(soup.prettify())
        try:
            title = soup.find('h1', class_='title mathjax').text
            abstract = soup.find('blockquote', class_='abstract mathjax').text
        except:
            continue
        update_page(paper_id, {
            "Title": {
                "rich_text": [
                    {"text": {"content": title}}
                ]
            },
            "Abstract": {
                "rich_text": [
                    {"text": {"content": abstract}}
                ]
            }
        }, db_id)

def old():
    ...
    # Getting training data
    # db_id = '497c9ac09b994b37af4a5fb43137bfb3' 
    # pages  = get_all_arxiv_pages(db_id)['results']
    # print(f"Retrieved {len(pages)} pages from the database")

    # for page in pages:
    #     title = page['properties']['Title']['rich_text'][0]['plain_text']
    #     abstract = page['properties']['Abstract']['rich_text'][0]['plain_text']
    #     architecture = [p['name'] for p in page['properties']['Architecture']['multi_select']]
    #     date = page['properties']['Date']['date']['start']
    #     tags = page['properties']['Tags']['multi_select']
    #     parameters = page['properties']['Parameters']['rich_text'][0]['plain_text'] if page['properties']['Parameters']['rich_text'] else ""
    #     dataset = page['properties']['Dataset']['rich_text'][0]['plain_text'] if page['properties']['Dataset']['rich_text'] else ""
    #     task = page['properties']['Task']['multi_select']
    #     paper = page['properties']['Paper']['url']
    #     repository = page['properties']['Repository']['url']
    #     notes = page['properties']['Notes']['rich_text'][0]['plain_text'] if page['properties']['Notes']['rich_text'] else ""

    #     papers.append(NotionEntry(
    #         title=title,
    #         abstract=abstract,
    #         architecture=architecture,
    #         date=date,
    #         tags=tags,
    #         parameters=parameters,
    #         dataset=dataset,
    #         task=task,
    #         paper=paper,
    #         repository=repository,
    #         notes=notes
    #     ))

    # print(f"Retrieved {len(papers)} papers from the database")
    # for paper in papers:
    #     if not get_page_by_doi(paper.paper)['results']:
    #         create_notion_entry(paper.as_dict())