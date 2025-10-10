import tomllib
from sqlalchemy import create_engine

def get_engine(working_dir, dbname=None):
    with open(working_dir / "config.toml", "rb") as f:
        config = tomllib.load(f)

    name = dbname or config["db"]["name"]
    user = config["db"]["user"]
    password = config["db"]["password"]
    host = config["db"]["host"]
    port = config["db"]["port"]

    return create_engine(f"postgresql+psycopg://{user}:{password}@{host}:{port}/{name}")


