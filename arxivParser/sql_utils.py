import logging
from sqlalchemy import create_engine, Column, String, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
from contextlib import contextmanager

# Configure logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

DATABASE_URL = "sqlite:///papers.db"
engine = create_engine(DATABASE_URL, echo=False)
Base = declarative_base()

class ArxivPaper(Base):
    __tablename__ = 'arxivpapers'
    
    # id = Column(Integer, primary_key=True, autoincrement=True)
    doi = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    abstract = Column(String, nullable=False)
    is_sci_llm = Column(Boolean, nullable=False)

Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)

@contextmanager
def get_session():
    session = Session()
    try:
        yield session
    finally:
        session.close()

# DB operations
def create_new_paper(session, doi, title, abstract, is_sci_llm):
    new_paper = ArxivPaper(doi=doi, title=title, abstract=abstract, is_sci_llm=is_sci_llm)
    # Check if the paper already exists
    if session.query(ArxivPaper).filter_by(doi=doi).first():
        print("Paper already exists.")
        return
    session.add(new_paper)
    session.commit()


def get_all_papers(session):
    return session.query(ArxivPaper).all()


if __name__ == "__main__":
    with get_session() as session:
        create_new_paper(session, "this doi", "Sample Paper", "This is a sample paper.", True)
        papers = get_all_papers(session)
        for p in papers:
            print(p.title, p.abstract)
