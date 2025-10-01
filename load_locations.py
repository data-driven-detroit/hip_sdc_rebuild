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


WORKING_DIR = Path(__file__).parent
SOURCE_GEO_TABLE = "geographies"


def get_engine(dbname=None):
    with open(WORKING_DIR / "config.toml", "rb") as f:
        config = tomllib.load(f)

    name = dbname or config["db"]["name"]
    user = config["db"]["user"]
    password = config["db"]["password"]
    host = config["db"]["host"]
    port = config["db"]["port"]

    return create_engine(f"postgresql+psycopg://{user}:{password}@{host}:{port}/{name}")


def location_types(source_db, target_db, load=True):
    print("Loading location types")

    stmt = text(f"""
    SELECT 
        ROW_NUMBER() OVER (ORDER BY geo_type) AS id, 
        geo_type,
        ROW_NUMBER() OVER (ORDER BY geo_type) AS sort_order
    FROM (
        SELECT DISTINCT geo_type
        FROM {SOURCE_GEO_TABLE}
    ) geotypes;
    """)

    loc_types = pd.read_sql(stmt, source_db)
    
    if load:
        (
            loc_types
            .rename(columns={"geo_type": "name"})
            .to_sql("location_type", target_db, index=False, if_exists="append")
        )

    return loc_types


def locations(loc_types, source_db, target_db, load=True):
    print("Loading locations")

    stmt = text("""
    SELECT
        geoid AS id,
        geo_type,
        name,
        ST_SETSRID(ST_SIMPLIFY(geometry, 0.001), ST_SRID(geometry)) AS geometry,
        NULL AS color
    FROM geographies
    WHERE 
        start_date <= DATE '2023-01-01'
        AND end_date >= DATE '2023-01-01';
    """)

    locations = gpd.read_postgis(stmt, source_db, geom_col="geometry")
    merged = locations.merge(loc_types.rename(columns={"id": "location_type_id"}), on="geo_type")
    
    if load:
        (
            merged[["id", "name", "geometry", "color", "location_type_id"]]
            .to_crs("EPSG:4326")
            .to_postgis("location", target_db, if_exists="append", index=False)
        )

    return locations


def location_parents(loc_types, target_db, load=True):
    print("Loading location parents")
    parent_config = pd.read_csv(WORKING_DIR / "conf" / "location_type_relationships.csv")

    merged = (
        parent_config
        .merge(
            loc_types.rename(
                columns={"geo_type": "child_type", "id": "from_locationtype_id"}
            ), 
            on="child_type"
        )
        .merge(
            loc_types.rename(
                columns={"geo_type": "parent_type", "id": "to_locationtype_id"}
            ), 
            on="parent_type"
        )
        .assign(id=lambda df: range(len(df)))
    )

    if load:
        (
            merged[["id", "from_locationtype_id", "to_locationtype_id"]]
            .to_sql("location_type_parent_location_types", target_db, index=False, if_exists="replace")
        )

    return merged


def main():
    source_db = get_engine()
    target_db = get_engine("sdc_test")


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
