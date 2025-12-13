import json
from pathlib import Path
from pymongo import MongoClient
import streamlit as st

def get_client():
    uri = st.secrets["mongo"]["uri"]
    return MongoClient(uri)

def load_json_to_collection(json_path, collection_name, db=None):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if db is None:
        db = get_client().get_default_database()
    if isinstance(data, list):
        if data:
            db[collection_name].insert_many(data)
    else:
        db[collection_name].insert_one(data)

def main():
    db = get_client().get_default_database()
    base = Path(__file__).parent
    for fname, coll in [("ingredients.json","ingredients"), ("recipes.json","recipes")]:
        path = base / fname
        if path.exists():
            load_json_to_collection(path, coll, db)
            print(f"Loaded {path} into {coll}")
        else:
            print(f"Skipping missing {path}")

if __name__ == "__main__":
    main()
