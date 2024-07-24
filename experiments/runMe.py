import os
from dotenv import load_dotenv
load_dotenv()

import pandas as pd

import sys
sys.path.append("../arxivParser")


from Paper import ArxivPaper
from NotionPage import NotionPage
from google_utils import get_arxiv_content
from notion_utils import (create_page, 
                          get_page_by_doi,
                          get_all_curated_pages,
                          )
from lm_utils import get_LM
from github_utils import open_issue_on_repo

def main():
    papers=[]
    for n in get_arxiv_content(15):
        if n['title']:
            papers.append(ArxivPaper(
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

    # Process papers
    sci_lm = get_LM(data=train_df, pipeline="scientific-classifier")
    arch_lm = get_LM(data=train_df, pipeline="lm-classifier")

    for paper in papers:
        arch_pred = arch_lm(title=paper.title, abstract=paper.abstract)
        sci_pred = sci_lm(title=paper.title, abstract=paper.abstract)
        keywords = ["chemistry", "chemical", "material", "synthesis", "reaction", "biology", "protein", "gene", "genoma"]
        is_scientific = [word in paper.abstract.lower() for word in keywords]
        if not any(is_scientific):
            continue
        if sci_pred.is_lm_paper.lower() == "yes" and arch_pred.is_lm_paper.lower() == "yes":
            print(f"Paper: {paper.title}\nAuthors: {paper.authors}\nAbstract: {paper.abstract}\nLink: {paper.doi}\nReasoning: {arch_pred.rationale}")
            decision = input("Do you want to open an issue for this paper? (y/N): ")
            decision = decision.lower() if decision.lower() in ["y", "n"] else "n"
            if decision == "y":
                # Create issue on GitHub
                open_issue_on_repo(os.environ.get('GITHUB_REPO'), f"New paper: {paper.title}", f"Paper: {paper.title}\n\nAuthors: {paper.authors}\n\nAbstract: {paper.abstract}\n\nLink: {paper.doi}\n\nReasoning: {arch_pred.rationale}")

    # Create notion pages

    # Populate db
    # for paper in papers:
    #     if not get_page_by_doi(paper.doi):
    #         create_page(paper.as_dict())

if __name__ == "__main__":
    main()