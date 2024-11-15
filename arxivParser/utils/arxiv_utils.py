import requests
from xml.etree import ElementTree

CATEGORIES = ["cs.AI", "cs.CL", "cs.CV", "cs.LG", "cs.NE", "cs.FL", "cs.GT", "stat.ML", "physics.chem-ph"]

def search_arxiv_by_category(category, max_results=10):
    url = "http://export.arxiv.org/api/query"
    params = {
        "search_query": f"cat:{category}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "lastUpdatedDate",
        "sortOrder": "descending",
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        raise Exception(f"Failed to fetch data: {response.status_code}")

    # Parse the XML response
    root = ElementTree.fromstring(response.content)
    papers = []

    for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
        paper = {
            "title": entry.find("{http://www.w3.org/2005/Atom}title").text.strip(),
            "abstract": entry.find("{http://www.w3.org/2005/Atom}summary").text.strip(),
            "authors": [
                author.find("{http://www.w3.org/2005/Atom}name").text.strip()
                for author in entry.findall("{http://www.w3.org/2005/Atom}author")
            ],
            "categories": [
                category.get("term")
                for category in entry.findall("{http://www.w3.org/2005/Atom}category")
            ],
            "date": entry.find("{http://www.w3.org/2005/Atom}published").text.strip(),
            "doi": entry.find("{http://www.w3.org/2005/Atom}id").text.strip(),
        }
        papers.append(paper)

    return papers

def search_all_arxiv_categories(max_results=10):
    all_papers = []

    for category in CATEGORIES:
        papers = search_arxiv_by_category(category, max_results)
        all_papers.extend(papers)

    return all_papers

# Example usage
if __name__ == "__main__":
    cat = "physics.flu-dyn"
    results = get_arxiv_content(cat)

    for idx, paper in enumerate(results, 1):
        print(f"{idx}. {paper['title']}")
        print(f"   Authors: {', '.join(paper['authors'])}")
        print(f"   Categories: {', '.join(paper['categories'])}")
        # print(f"   Abstract: {paper['abstract']}\n")
        print(f"   DOI: {paper['doi']}")
        print(f"   Date: {paper['date']}")

