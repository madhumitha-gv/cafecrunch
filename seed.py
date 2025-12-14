import json
from pathlib import Path
from pymongo import MongoClient
import streamlit as st

def get_client():
    # Prefer a URI that already includes the database if you store one.
    mongo_cfg = st.secrets.get("mongo", {})
    uri = mongo_cfg.get("uri_with_db") or mongo_cfg.get("uri")
    if not uri:
        raise KeyError("Missing st.secrets['mongo']['uri'] (or 'uri_with_db')")
    return MongoClient(uri)


def get_db():
    """Return the target database explicitly.

    Recommended: set st.secrets['mongo']['db'] = 'Cafe_crunch_db' (or your DB name).
    If not set, falls back to the default DB encoded in the URI (if any).
    """
    client = get_client()
    mongo_cfg = st.secrets.get("mongo", {})
    db_name = mongo_cfg.get("db")
    return client[db_name] if db_name else client.get_default_database()

def load_json_to_collection(json_path, collection_name, db=None, *, key_field=None, drop_first=False):
    """Load JSON data into MongoDB.

    - If data is a list, upsert each document.
    - If data is a dict, insert one document.

    Params:
      key_field: if provided, uses this field for upsert matching. If not provided, uses _id when present.
      drop_first: if True, clears the collection before loading.
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if db is None:
        db = get_db()

    coll = db[collection_name]

    if drop_first:
        coll.delete_many({})

    if isinstance(data, list):
        for doc in data:
            if not isinstance(doc, dict):
                continue
            # Choose match key for upsert
            if key_field and key_field in doc:
                match = {key_field: doc[key_field]}
            elif "_id" in doc:
                match = {"_id": doc["_id"]}
            else:
                # If no key, fall back to insert
                coll.insert_one(doc)
                continue

            coll.replace_one(match, doc, upsert=True)
    else:
        # single document
        coll.insert_one(data)

def main():
    db = get_db()
    base = Path(__file__).parent

    # Use consistent, idempotent upserts for list-based JSON files
    to_load = [
        ("ingredients.json", "ingredients", "ingredient_id"),
        ("recipes.json", "recipes", "_id"),
        ("inventory.json", "inventory", "ingredient_id"),
    ]

    for fname, coll, key_field in to_load:
        path = base / fname
        if path.exists():
            load_json_to_collection(path, coll, db, key_field=key_field)
            print(f"Loaded {path} into {coll}")
        else:
            print(f"Skipping missing {path}")

if __name__ == "__main__":
    main()
