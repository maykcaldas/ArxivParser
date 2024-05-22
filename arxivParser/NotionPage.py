class NotionPage:
    def __init__(self, doi, title, abstract, architecture, date, paper, repository, notes="", tags="", parameters="", dataset="", task="", curated=False):
        self.title = title
        self.abstract = abstract
        self.architecture = architecture
        self.date = date
        self.tags = tags
        self.parameters = parameters
        self.dataset = dataset
        self.task = task
        self.paper = paper
        self.repository = repository
        self.notes = notes
        self.curated = curated
        self.doi = doi

    def as_dict(self):
        return self.__dict__

    def __str__(self):
        return f"Notion entry: {self.authors}. {self.title}. {self.categories}. {self.doi}. {self.date}"
    
    def __repr__(self):
        return self.__str__()
    