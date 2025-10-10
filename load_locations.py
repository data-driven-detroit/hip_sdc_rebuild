"""
Load the tables that handle the locations:
    - location: The table that has location names, geoids and geometries
    - location_type: The type of geography that we're creating -- this can be
      the classic census types, or custom types as well
    - location_type_parent_location_types: The many to many table that links 
      location_types to any type they might be contained within.
"""

from pathlib import Path
import tomllib
from sqlalchemy import text, create_engine
import geopandas as gpd
import pandas as pd
from hip_sdc_rebuild import get_engine

WORKING_DIR = Path(__file__).parent
SOURCE_GEO_TABLE = "etl.geographies" # data database in edw
DESTINATION_DB = "sdc_production"


def location_types(source_db, target_db, load=True):
    print("Loading location types")
    table = pd.read_csv(WORKING_DIR / "shared" / "location_type.csv")

    if load:
        (
            table.to_sql("location_type", target_db, index=False, if_exists="append")
        )

    return table


def locations(loc_types, source_db, target_db, load=True):
    print("Loading locations")

    stmt = text(f"""
    SELECT
        geoid AS id,
        geo_type,
        name,
        ST_SETSRID(ST_SIMPLIFY(geometry, 0.0004), ST_SRID(geometry)) AS geometry,
        NULL AS color
    FROM {SOURCE_GEO_TABLE}
    WHERE 
        start_date <= DATE '2023-01-01'
        AND end_date >= DATE '2023-01-01';
    """)

    locations = gpd.read_postgis(stmt, source_db, geom_col="geometry")
    merged = locations.merge(
        loc_types.rename(columns={"id": "location_type_id", "name": "geo_type"}), 
        on="geo_type"
    )
    
    if load:
        (
            merged[["id", "name", "geometry", "color", "location_type_id"]]
            .to_crs("EPSG:4326")
            .to_postgis("location", target_db, if_exists="append", index=False)
        )

    return locations


def location_parents(loc_types, target_db, load=True):
    print("Loading location parents")
    table = pd.read_csv(WORKING_DIR / "shared" / "location_type_parent_location_types.csv")


    if load:
        table.to_sql("location_type_parent_location_types", target_db, index=False, if_exists="replace")

    return table


def main():
    source_db = get_engine(WORKING_DIR)
    target_db = get_engine(WORKING_DIR, DESTINATION_DB)


    # Before starting clear the target_db
    stmts = [
         text("""DELETE FROM location CASCADE;"""),
         text("""DELETE FROM location_type CASCADE;"""),
         text("""DELETE FROM location_type_parent_location_types CASCADE;"""),
    ]

    with target_db.connect() as db:
        for stmt in stmts:
            db.execute(stmt)

        db.commit()

    loc_types = location_types(source_db, target_db, load=True)
    locs = locations(loc_types, source_db, target_db, load=True)
    relationships = location_parents(loc_types, target_db, load=True)

if __name__ == "__main__":
    main()
