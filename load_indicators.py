from pathlib import Path
import tomllib
from sqlalchemy import text, create_engine
import pandas as pd
from hip_sdc_rebuild import get_engine


WORKING_DIR = Path(__file__).parent
SOURCE_GEO_TABLE = "etl.geographies" # data database in edw
DESTINATION_DB = "sdc_production"


def clear_tables(destination_db):
    stmts = [
         # text("""DELETE FROM section CASCADE;"""),
         # text("""DELETE FROM category CASCADE;"""),
         # text("""DELETE FROM indicator_data_visual CASCADE;"""),
         # text("""DELETE FROM indicator CASCADE;"""),
         text("""DELETE FROM indicator_filter_type CASCADE;"""),
         text("""DELETE FROM indicator_filter_option CASCADE;"""),
         # text("""DELETE FROM indicator_source CASCADE;"""),
    ]

    with destination_db.connect() as db:
        for stmt in stmts:
            db.execute(stmt)

        db.commit()


def load_sections(destination_db):
    print("Loading sections")
    table = pd.read_csv(WORKING_DIR / "sdc" / "section.csv")
    table.to_sql("section", destination_db, index=False, if_exists="append")


def load_categories(destination_db):
    print("Loading categories")
    table = pd.read_csv(WORKING_DIR / "sdc" / "category.csv")
    table.to_sql("category", destination_db, index=False, if_exists="append")


def load_indicators(destination_db):
    print("Loading indicators")
    table = pd.read_csv(WORKING_DIR / "sdc" / "indicator.csv")
    table.to_sql("indicator", destination_db, index=False, if_exists="append")

def load_visuals(destination_db):
    print("Loading visuals")
    table = pd.read_csv(WORKING_DIR / "sdc" / "indicator_data_visual.csv")

    table["start_date"] = pd.to_datetime(table["start_date"])
    table["end_date"] = pd.to_datetime(table["end_date"])

    table.to_sql("indicator_data_visual", destination_db, index=False, if_exists="append")

def load_filter_types(destination_db):
    print("Loading filter types")
    table = pd.read_csv(WORKING_DIR / "sdc" / "indicator_filter_type.csv")
    table.to_sql("indicator_filter_type", destination_db, index=False, if_exists="append")


def load_filter_options(destination_db):
    print("Loading filter options")
    table = pd.read_csv(WORKING_DIR / "sdc" / "indicator_filter_option.csv")
    table.to_sql("indicator_filter_option", destination_db, index=False, if_exists="append")


def load_indicator_filter_types(destination_db):
    print("Loading indicator-indicator_filter_types")
    table = pd.read_csv(WORKING_DIR / "sdc" / "indicator_indicator_filter_type.csv")
    table.to_sql("indicator_indicator_filter_types", destination_db, index=False, if_exists="append")


def load_sources(destination_db):
    print("Loading sources")
    table = pd.read_csv(WORKING_DIR / "sdc" / "indicator_source.csv")
    table.to_sql("indicator_source", destination_db, index=False, if_exists="append")


def main():
    destination_db = get_engine(WORKING_DIR, DESTINATION_DB)

    clear_tables(destination_db)

    # load_sections(destination_db)
    # load_categories(destination_db)
    # load_indicators(destination_db)
    # load_sources(destination_db)
    # load_visuals(destination_db)
    load_filter_types(destination_db)
    load_filter_options(destination_db)

    # Not required by the site, but useful for creating dummy data.
    load_indicator_filter_types(destination_db)


if __name__ == "__main__":
    main()
