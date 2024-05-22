import os
from dotenv import load_dotenv
load_dotenv()

import pandas as pd
from Paper import Paper
from NotionPage import NotionPage
from google_utils import get_arxiv_content
from notion_utils import (create_page, 
                          get_page_by_doi,
                          get_all_curated_pages,
                          )
from lm_utils import get_LM, ClassifierLM, ArchitectureLM

def main():
    papers=[]
    for n in get_arxiv_content(15):
        # print(n)
        if n['title']:
            papers.append(Paper(
                title=n['title'],
                authors=n['authors'],
                categories=n['categories'],
                abstract=n['abstract'],
                doi=n['doi'],
                date=n['date']
            ))
    print(f"Found {len(papers)} papers.")

    # Getting training data
    training_data = get_all_curated_pages()
    train_titles = [x['properties']['Title']['rich_text'][0]['plain_text'] for x in training_data]
    train_abstracts = [x['properties']['Abstract']['rich_text'][0]['plain_text'] for x in training_data]
    train_architectures = [x['properties']['Architecture']['multi_select'] for x in training_data]

    train_df = pd.DataFrame({'title': train_titles, 'abstract': train_abstracts, 'architecture': train_architectures})
    train_df['architecture'] = train_df['architecture'].apply(lambda x: ",".join([e['name'] for e in x if x]))
    print(f"Retrieved {len(train_df)} pages from the database for training")

    arch_lm = get_LM(trainset=train_df, pipeline=ArchitectureLM)

    for paper in papers[9:10]:
        print(paper.title)
        print(paper.abstract)
        pred = arch_lm(title=paper.title, abstract=paper.abstract)
        print(pred)
    # Process papers

    # Create notion pages

    # Populate db

    # for paper in papers:
    #     # print(paper)
    #     if not get_page_by_doi(paper.doi):
    #         create_page(paper.as_dict())

if __name__ == "__main__":
    main()