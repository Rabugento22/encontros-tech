from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from core.settings import settings

# connect_timeout evita que um banco inacessível pendure requisições (e as probes);
# pool_pre_ping descarta conexões obsoletas após o banco reiniciar
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"connect_timeout": 3},
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
