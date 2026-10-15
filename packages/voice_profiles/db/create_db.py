
from packages.voice_profiles.db.database import engine
from packages.voice_profiles.db.models import Base

def create_db_and_tables():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    create_db_and_tables()
