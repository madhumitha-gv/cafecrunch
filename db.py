import streamlit as st
from pymongo import MongoClient
from pymongo.collection import Collection
from typing import Any, Dict, List, Optional, Tuple

@st.cache_resource
def get_client() -> MongoClient:
    return MongoClient(st.secrets["MONGO_URI"], serverSelectionTimeoutMS=6000)

def get_db():
    return get_client()[st.secrets.get("DB_NAME", "CafeCrunch")]

def colls() -> Tuple[Collection, Collection]:
    db = get_db()
    ing = db[st.secrets.get("INGREDIENTS_COLL", "ingredients")]
    rec = db[st.secrets.get("RECIPES_COLL", "recipes")]
    return ing, rec

# ---------- Reads ----------
def list_recipes(category=None, temperature=None, size_range=None, only_ok=True, limit=300):
    _, recipes = colls()
    q: Dict[str, Any] = {}
    if category and category != "All":
        q["category"] = category
    if temperature and temperature != "All":
        q["temperature"] = temperature
    if size_range:
        q["size_ml"] = {"$gte": int(size_range[0]), "$lte": int(size_range[1])}
    if only_ok:
        q["recipe_ok"] = True
    return list(recipes.find(q, {"composition": 0}).sort("name", 1).limit(limit))

def get_recipe(recipe_id: str) -> Optional[Dict[str, Any]]:
    _, recipes = colls()
    return recipes.find_one({"_id": recipe_id})

def list_ingredients(limit=2000):
    ing, _ = colls()
    return list(ing.find({}).sort("name", 1).limit(limit))

def ingredient_map() -> Dict[str, Dict[str, Any]]:
    ing, _ = colls()
    return {d["_id"]: d for d in ing.find({})}

# ---------- Writes ----------
def update_recipe_defaults(recipe_id: str, patch: Dict[str, Any]) -> int:
    _, recipes = colls()
    res = recipes.update_one(
        {"_id": recipe_id},
        {"$set": {f"defaults.{k}": v for k, v in patch.items()}}
    )
    return res.modified_count

def upsert_ingredient(doc: Dict[str, Any]) -> None:
    ing, _ = colls()
    ing.replace_one({"_id": doc["_id"]}, doc, upsert=True)

def delete_ingredient(ingredient_id: str) -> int:
    ing, _ = colls()
    return ing.delete_one({"_id": ingredient_id}).deleted_count

# ---------- Dashboard aggregations ----------
def agg_counts_category_temp():
    _, recipes = colls()
    return list(recipes.aggregate([
        {"$group": {"_id": {"category": "$category", "temperature": "$temperature"}, "count": {"$sum": 1}}},
        {"$sort": {"_id.category": 1, "_id.temperature": 1}},
    ]))

def agg_milk_popularity():
    _, recipes = colls()
    return list(recipes.aggregate([
        {"$match": {"options.milks": {"$exists": True}}},
        {"$unwind": "$options.milks"},
        {"$group": {"_id": "$options.milks", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]))

def agg_ingredient_usage_topn(n=10):
    _, recipes = colls()
    return list(recipes.aggregate([
        {"$unwind": "$composition"},
        {"$group": {"_id": "$composition.ingredient_id", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": int(n)},
    ]))

def agg_calories_topn(n=10):
    _, recipes = colls()
    pipeline = [
        {"$unwind": "$composition"},
        {"$lookup": {
            "from": st.secrets.get("INGREDIENTS_COLL", "ingredients"),
            "localField": "composition.ingredient_id",
            "foreignField": "_id",
            "as": "ing"
        }},
        {"$unwind": "$ing"},
        {"$addFields": {
            "factor": {
                "$cond": [
                    {"$gt": ["$composition.amount_ml", None]},
                    {"$divide": ["$composition.amount_ml", "$ing.unit_ml"]},
                    {
                        "$cond": [
                            {"$gt": ["$composition.amount_pumps", None]},
                            "$composition.amount_pumps",
                            {"$cond": [
                                {"$gt": ["$composition.amount_shots", None]},
                                "$composition.amount_shots",
                                0
                            ]}
                        ]
                    }
                ]
            }
        }},
        {"$group": {
            "_id": "$name",
            "calories_kcal": {"$sum": {"$multiply": ["$ing.nutrition_per_unit.calories", "$factor"]}},
            "sugar_g": {"$sum": {"$multiply": ["$ing.nutrition_per_unit.sugar_g", "$factor"]}},
            "caffeine_mg": {"$sum": {"$multiply": ["$ing.nutrition_per_unit.caffeine_mg", "$factor"]}},
        }},
        {"$project": {
            "_id": 0,
            "name": "$_id",
            "calories_kcal": {"$round": ["$calories_kcal", 1]},
            "sugar_g": {"$round": ["$sugar_g", 1]},
            "caffeine_mg": {"$round": ["$caffeine_mg", 1]},
        }},
        {"$sort": {"calories_kcal": -1}},
        {"$limit": int(n)},
    ]
    return list(recipes.aggregate(pipeline))

