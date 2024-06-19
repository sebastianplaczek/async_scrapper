from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    Boolean,
    Sequence,
    inspect,
    DateTime,
    MetaData,
)
from sqlalchemy import inspect, create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()


class Offers(Base):
    __tablename__ = "offers"
    id = Column(Integer, Sequence("user_id_seq"), primary_key=True)
    link = Column(String(255))
    type = Column(String(20))
    title = Column(String(255))
    address = Column(String(255))
    price = Column(Float)
    price_per_m = Column(Float)
    rooms = Column(Integer)
    size = Column(Float)
    active = Column(Boolean)
    create_date = Column(DateTime, default=datetime.now())
    seller = Column(String(255))
    seller_type = Column(String(255))
    filled = Column(Boolean, default=0)
    page = Column(Integer)
    bumped = Column(Boolean)
    offer_loc_id = Column(Integer)
    n_scrap = Column(Integer)


class OffersLoc(Base):
    __tablename__ = "offers_loc"
    id = Column(Integer, Sequence("user_id_seq"), primary_key=True)
    lat = Column(Float)
    lon = Column(Float)
    city = Column(String(50))
    municipality = Column(String(100))
    county = Column(String(100))
    vivodeship = Column(String(50))
    postcode = Column(String(10))
    link = Column(String(255))
    create_date = Column(DateTime, default=datetime.now())
    address = Column(String(255))


class NominatimApi(Base):
    __tablename__ = "NominatimApi"
    id = Column(Integer, Sequence("user_id_seq"), primary_key=True)
    link = Column(String(500))
    status_code = Column(Integer)
    create_date = Column(DateTime, default=datetime.now())
    empty = Column(Boolean)
    offer_id = Column(Integer)


class OtodomWebsite(Base):
    __tablename__ = "OtodomWebsite"
    id = Column(Integer, Sequence("user_id_seq"), primary_key=True)
    type = Column(String(20))
    link = Column(String(255))
    active = Column(Boolean)
    num_pages = Column(Integer)
    create_date = Column(DateTime, default=datetime.now())

class ScrapInfo(Base):
    __tablename__="scrapinfo"
    id = Column(Integer, Sequence("user_id_seq"), primary_key=True)
    create_date = Column(DateTime, default=datetime.now())
    active = Column(Boolean,default=True)


engine = create_engine("mysql+pymysql://normal:qwerty123@localhost:3307/scrapper_db",
    pool_size=10,          # Domyślnie 5
    max_overflow=20,       # Domyślnie 10
    pool_timeout=30,       # Domyślnie 30 sekund
    pool_recycle=1800      # Recykluj połączenia co 30 minut
)


# Funkcja do sprawdzania i tworzenia tabel, jeśli nie istnieją


def create_tables_and_columns_if_not_exists(engine, base):
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    metadata = MetaData(bind=engine)
    tables_to_create = []

    # Loop through all table classes
    for table_class in base.__subclasses__():
        if hasattr(table_class, "__tablename__"):
            table_name = table_class.__tablename__
            if table_name not in existing_tables:
                tables_to_create.append(table_class.__table__)
            else:
                # Check for missing columns
                table = table_class.__table__
                existing_columns = {
                    col["name"] for col in inspector.get_columns(table_name)
                }
                for column in table.columns:
                    if column.name not in existing_columns:
                        column_type = column.type.compile(engine.dialect)
                        with engine.connect() as conn:
                            conn.execute(
                                f"ALTER TABLE {table_name} ADD COLUMN {column.name} {column_type}"
                            )

    # Create any new tables
    if tables_to_create:
        base.metadata.create_all(engine, tables=tables_to_create)


# Utwórz tabele tylko jeśli nie istnieją
create_tables_and_columns_if_not_exists(engine, Base)

# Utworzenie sesji
Session = sessionmaker(bind=engine)
