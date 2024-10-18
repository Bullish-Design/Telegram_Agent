# database.py

from sqlmodel import SQLModel, Session, create_engine

DATABASE_URL = "sqlite:///database.db"
engine = create_engine(DATABASE_URL, echo=False)


def init_db():
    """
    Initializes the database by creating all tables.
    """
    SQLModel.metadata.create_all(engine)


def get_session():
    """
    Creates a new database session.

    Returns:
        Session: A new SQLModel session.
    """
    return Session(engine)
