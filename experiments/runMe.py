import os
from dotenv import load_dotenv
load_dotenv()

import dspy
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
from sql_utils import get_session, get_all_papers
from lm_utils import get_LM
from github_utils import open_issue_on_repo

def main():
    papers=[]
    for n in get_arxiv_content(15):
        if n['title']:
            papers.append(ArxivPaper(
                title=n['title'],
                abstract=n['abstract'],
                authors=n['authors'],
                categories=n['categories'],
                date=n['date'],
                doi=n['doi'],
            ))
    print(f"Found {len(papers)} papers.")

    # Getting training data
    with get_session() as session:
        data = get_all_papers(session)
    dois = [x.doi for x in data]
    titles = [x.title for x in data]
    abstracts = [x.abstract for x in data]
    labels = ["yes" if x.is_sci_llm else "no" for x in data]

    train_df = pd.DataFrame({'doi': dois, 'title': titles, 'abstract': abstracts, 'label': labels})
    
    # TODO: Add architecture to the training data and use an LLM to predict it for new papers
    # train_df['architecture'] = train_df['architecture'].apply(lambda x: ",".join([e['name'] for e in x if x]))
    
    print(f"Retrieved {len(train_df)} pages from the database for training")

    # Process papers
    lm, sci_lm = get_LM(data=None, pipeline=("chain-of-thought-classifier", "scientific"))
    lm, arch_lm = get_LM(data=None, pipeline=("chain-of-thought-classifier", "lm"))

    to_curate = []
    for paper in papers:
        with dspy.context(lm=lm):
            is_lm = arch_lm(title=paper.title, abstract=paper.abstract)
            is_sci = sci_lm(title=paper.title, abstract=paper.abstract)
        keywords = ["chemistry", "chemical", "material", "synthesis", "reaction", "biology", "protein", "gene", "genoma"]
        is_scientific = [word in paper.abstract.lower() for word in keywords]

        if not any(is_scientific):
            continue
        
        if is_sci.answer.lower() == "yes" and is_lm.answer.lower() == "yes":
            print(f"Paper: {paper.title}\nAuthors: {paper.authors}\nAbstract: {paper.abstract}\nLink: {paper.doi}\nReasoning: {is_lm.rationale}")
            decision = input("Do you want to open an issue for this paper? (y/N): ")
            decision = decision.lower() if decision.lower() in ["y", "n"] else "n"
            if decision == "y":
                # Create issue on GitHub
                open_issue_on_repo(os.environ.get('GITHUB_REPO'), f"New paper: {paper.title}", f"Paper: {paper.title}\n\nAuthors: {paper.authors}\n\nAbstract: {paper.abstract}\n\nLink: {paper.doi}\n\nReasoning: {is_lm.rationale}")

    
    # Create notion pages and populate db

    # Populate db
    # for paper in papers:
    #     create_page(paper.as_dict())

if __name__ == "__main__":
    main()