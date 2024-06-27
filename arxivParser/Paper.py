class Paper:
    def __init__(self, 
                 title, 
                 authors, 
                 categories, 
                 abstract, 
                 doi, 
                 date
                 ):
        self.title = title
        self.authors = authors
        self.categories = categories.split()
        self.abstract = abstract
        self.doi = doi
        self.date = date

    def as_dict(self):
        return self.__dict__
        return {
            'title': self.title,
            'authors': self.authors,
            'categories': self.categories,
            'abstract': self.abstract,
            'doi': self.doi,
            'date': self.date
        }

    def __str__(self):
        return f"Paper: {self.authors}. {self.title}. {self.categories}. {self.doi}. {self.date}"
    
    def __repr__(self):
        return self.__str__()
    

class ArxivPaper(Paper):
    def __str__(self):
        return f"ArXiv Paper: {self.authors}. {self.title}. {self.categories}. {self.doi}. {self.date}"
