

import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st

# MongoDB Atlas
from pymongo import MongoClient
from pymongo.collection import Collection


# ----------------------------
# Page config
# ----------------------------
st.set_page_config(page_title="Inventory", page_icon="📦", layout="wide")


# ----------------------------
# Theme (match Dashboard)
# ----------------------------
COLORS = {
    "espresso": "#1B0E07",
    "dark_roast": "#3C2415",
    "mocha": "#5D4037",
    "caramel": "#C4873A",
    "latte": "#D4A574",
    "cream": "#F5E6D3",
    "paper": "#FBF6EE",
    "border": "#D7B98A",
    "sage": "#81C784",
    "berry": "#E57373",
    "gold": "#FFB300",
    "white": "#FFFFFF",
}

THEME_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Nunito:wght@400;600;700&display=swap');

html, body, [class*="css"] {{
  font-family: 'Nunito', sans-serif;
}}

.stApp {{
  background: radial-gradient(1200px 800px at 15% 10%, {COLORS['paper']} 0%, {COLORS['cream']} 60%, #F3E0C9 100%);
}}

.cc-title {{
  font-family: 'Playfair Display', serif;
  color: {COLORS['espresso']};
  letter-spacing: 0.2px;
  margin: 0.25rem 0 0.5rem 0;
  font-size: 1.8rem;
  font-weight: 700;
}}

.cc-sub {{
  color: {COLORS['mocha']};
  opacity: 0.9;
  margin-bottom: 1rem;
}}

.cc-card {{
  background: rgba(255,255,255,0.55);
  border: 1px solid rgba(215,185,138,0.65);
  border-radius: 16px;
  padding: 16px 18px;
  box-shadow: 0 8px 24px rgba(27,14,7,0.06);
}}

.cc-muted {{ opacity: 0.75; }}

.cc-pill {{
  display:inline-block;
  padding: 0.15rem 0.55rem;
  border-radius: 999px;
  border: 1px solid rgba(215,185,138,0.75);
  color: {COLORS['espresso']};
  font-size: 0.8rem;
  background: rgba(255,255,255,0.35);
}}

.cc-badge-low {{
  display:inline-block;
  padding: 0.15rem 0.55rem;
  border-radius: 999px;
  background: rgba(229,115,115,0.18);
  border: 1px solid rgba(229,115,115,0.45);
  color: {COLORS['espresso']};
  font-size: 0.8rem;
}}

.cc-badge-ok  {{
  display:inline-block;
  padding: 0.15rem 0.55rem;
  border-radius: 999px;
  background: rgba(129,199,132,0.16);
  border: 1px solid rgba(129,199,132,0.45);
  color: {COLORS['espresso']};
  font-size: 0.8rem;
}}

div[data-testid="stDataFrame"] {{
  background: rgba(255,255,255,0.40);
  border: 1px solid rgba(215,185,138,0.55);
  border-radius: 14px;
  padding: 10px;
}}

</style>
"""

st.markdown(THEME_CSS, unsafe_allow_html=True)


# ----------------------------
# Mongo helpers
# ----------------------------
@st.cache_resource(show_spinner=False)
def _get_mongo_client() -> MongoClient:
    """Create Mongo client.

    Supported secret/env keys (in priority order):
      - st.secrets['MONGODB_URI']
      - st.secrets['MONGO_URI']
      - st.secrets['mongo']['uri_with_db']
      - st.secrets['mongo']['uri']
      - env var MONGODB_URI
      - env var MONGO_URI

    IMPORTANT: add your URI to Streamlit secrets or env; don't hardcode it.
    """
    uri = None

    # secrets (top-level)
    if "MONGODB_URI" in st.secrets:
        uri = st.secrets["MONGODB_URI"]
    elif "MONGO_URI" in st.secrets:
        uri = st.secrets["MONGO_URI"]

    # secrets (nested)
    if not uri:
        mongo_cfg = st.secrets.get("mongo", {})
        uri = mongo_cfg.get("uri_with_db") or mongo_cfg.get("uri")

    # env vars
    if not uri:
        uri = os.getenv("MONGODB_URI") or os.getenv("MONGO_URI")

    if not uri:
        raise RuntimeError(
            "MongoDB URI not found. Set st.secrets['MONGO_URI'] (or st.secrets['mongo']['uri']) or env var MONGO_URI."
        )

    return MongoClient(uri)


def _get_collections(client: MongoClient) -> Tuple[Collection, Collection]:
    """Return (ingredients_collection, inventory_collection)."""
    # DB name (support your existing secrets.toml)
    db_name = (
        st.secrets.get("MONGODB_DB")
        or st.secrets.get("DB_NAME")
        or st.secrets.get("mongo", {}).get("db")
        or os.getenv("MONGODB_DB")
        or os.getenv("DB_NAME")
        or "cafecrunch"
    )
    db = client[db_name]

    # Collection names (support existing secrets.toml)
    ingredients_name = (
        st.secrets.get("COL_INGREDIENTS")
        or st.secrets.get("INGREDIENTS_COLL")
        or st.secrets.get("mongo", {}).get("ingredients_coll")
        or os.getenv("COL_INGREDIENTS")
        or os.getenv("INGREDIENTS_COLL")
        or "ingredients"
    )
    inventory_name = (
        st.secrets.get("COL_INVENTORY")
        or st.secrets.get("INVENTORY_COLL")
        or st.secrets.get("mongo", {}).get("inventory_coll")
        or os.getenv("COL_INVENTORY")
        or os.getenv("INVENTORY_COLL")
        or "inventory"
    )

    ingredients_col = db[ingredients_name]
    inventory_col = db[inventory_name]
    return ingredients_col, inventory_col


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


# ----------------------------
# Data loading
# ----------------------------

def load_ingredients(ingredients_col: Collection) -> List[Dict[str, Any]]:
    # Expect one doc per ingredient.
    # Minimal fields used: _id OR ingredient_id, name, unit/portion info.
    docs = list(ingredients_col.find({}))

    # Sort by name if present.
    def _name(d: Dict[str, Any]) -> str:
        return str(d.get("name") or d.get("ingredient_name") or d.get("ingredient_id") or d.get("_id") or "")

    docs.sort(key=_name)
    return docs


def load_inventory_docs(inventory_col: Collection) -> List[Dict[str, Any]]:
    """Load inventory.

    Supports two shapes:
    A) Recommended: one doc per ingredient ("ingredient_id" or _id)
    B) Legacy: a single doc with { items: { <ingredient_id>: {...} } }

    We normalize into a list of per-ingredient docs for the UI.
    """
    docs = list(inventory_col.find({}))

    # If it looks like legacy single-document schema, normalize it.
    if len(docs) == 1 and isinstance(docs[0].get("items"), dict):
        legacy = docs[0]
        out: List[Dict[str, Any]] = []
        for k, v in legacy["items"].items():
            if not isinstance(v, dict):
                continue
            item = {**v}
            item.setdefault("ingredient_id", v.get("ingredient_id", k))
            # Keep link to legacy container for updates if needed
            item["_legacy_container_id"] = legacy.get("_id")
            out.append(item)
        return out

    # Otherwise assume per-ingredient docs
    return docs


def inventory_index(inventory_docs: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    idx: Dict[str, Dict[str, Any]] = {}
    for d in inventory_docs:
        ing_id = str(d.get("ingredient_id") or d.get("_id") or "")
        if ing_id:
            idx[ing_id] = d
    return idx


# ----------------------------
# Write operations
# ----------------------------

def upsert_inventory_item(
    inventory_col: Collection,
    ingredient_id: str,
    patch: Dict[str, Any],
    txn: Optional[Dict[str, Any]] = None,
    legacy_container_id: Optional[Any] = None,
) -> None:
    """Upsert inventory for an ingredient.

    If legacy_container_id is provided, we update the nested path items.<ingredient_id>.
    Otherwise, we upsert one doc per ingredient.
    """

    if legacy_container_id is not None:
        # Legacy single-document update
        update: Dict[str, Any] = {"$set": {}}
        for k, v in patch.items():
            update["$set"][f"items.{ingredient_id}.{k}"] = v
        if txn:
            update.setdefault("$push", {})
            update["$push"][f"items.{ingredient_id}.transactions"] = txn

        inventory_col.update_one({"_id": legacy_container_id}, update, upsert=True)
        return

    # Recommended: one doc per ingredient
    update_doc: Dict[str, Any] = {"$set": {**patch, "ingredient_id": ingredient_id, "updated_at": _now_iso()}}
    if txn:
        update_doc["$push"] = {"transactions": txn}

    inventory_col.update_one({"ingredient_id": ingredient_id}, update_doc, upsert=True)


def compute_reorder_status(item: Dict[str, Any]) -> Tuple[bool, int]:
    """Return (is_low, recommended_qty).

    Rule: low if available < reorder_point.
    Recommendation: max(preferred_reorder_qty, par_level - available) if low.
    """
    on_hand = int(item.get("on_hand") or 0)
    reserved = int(item.get("reserved") or 0)
    available = int(item.get("available") or max(0, on_hand - reserved))
    reorder_point = int(item.get("reorder_point") or 0)
    par_level = int(item.get("par_level") or 0)
    pref = int(item.get("preferred_reorder_qty") or 0)

    is_low = available < reorder_point
    if not is_low:
        return False, 0

    needed_to_par = max(0, par_level - available) if par_level else 0
    reco = max(pref, needed_to_par) if (pref or needed_to_par) else max(0, reorder_point - available)
    return True, int(reco)


# ----------------------------
# UI
# ----------------------------

st.markdown('<div class="cc-title">📦 Inventory</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="cc-sub">Update on-hand quantities, thresholds, and keep a clean transaction history for future stocking analytics.</div>',
    unsafe_allow_html=True,
)

# Connection
try:
    client = _get_mongo_client()
    ingredients_col, inventory_col = _get_collections(client)
except Exception as e:
    st.error(str(e))
    st.stop()

# Load data
ingredients = load_ingredients(ingredients_col)
inventory_docs = load_inventory_docs(inventory_col)
inv_idx = inventory_index(inventory_docs)

# Build ingredient options
options: List[Tuple[str, str]] = []  # (id, label)
for ing in ingredients:
    ing_id = str(ing.get("ingredient_id") or ing.get("_id") or "")
    name = str(ing.get("name") or ing.get("ingredient_name") or ing_id)
    unit = ing.get("unit") or ing.get("stock_unit") or ing.get("portion_unit")
    label = f"{name} ({ing_id})" + (f" • {unit}" if unit else "")
    if ing_id:
        options.append((ing_id, label))

# Left: selector and editor
left, right = st.columns([1.1, 1.0], gap="large")

with left:
    st.markdown('<div class="cc-card">', unsafe_allow_html=True)
    st.markdown("**Edit inventory item**")

    if not options:
        st.warning("No ingredients found in the database. Add ingredients first.")
        st.markdown('</div>', unsafe_allow_html=True)
        st.stop()

    # Default selection: first low item if any, else first ingredient
    low_first_id: Optional[str] = None
    for ing_id, _label in options:
        item = inv_idx.get(ing_id, {})
        is_low, _reco = compute_reorder_status(item)
        if is_low:
            low_first_id = ing_id
            break

    default_id = low_first_id or options[0][0]

    selected_label = st.selectbox(
        "Ingredient",
        options=[lbl for _id, lbl in options],
        index=[i for i, (iid, _lbl) in enumerate(options) if iid == default_id][0],
    )

    selected_id = None
    for iid, lbl in options:
        if lbl == selected_label:
            selected_id = iid
            break

    assert selected_id is not None

    current = inv_idx.get(selected_id, {})
    legacy_container_id = current.get("_legacy_container_id")

    # Prefill values
    cur_on_hand = int(current.get("on_hand") or 0)
    cur_reserved = int(current.get("reserved") or 0)
    cur_available = int(current.get("available") or max(0, cur_on_hand - cur_reserved))
    cur_par = int(current.get("par_level") or 0)
    cur_rop = int(current.get("reorder_point") or 0)
    cur_pref = int(current.get("preferred_reorder_qty") or 0)
    cur_lead = int(current.get("lead_time_days") or 0)

    # Status chip
    is_low, reco_qty = compute_reorder_status({
        "on_hand": cur_on_hand,
        "reserved": cur_reserved,
        "available": cur_available,
        "par_level": cur_par,
        "reorder_point": cur_rop,
        "preferred_reorder_qty": cur_pref,
    })

    st.markdown(
        f"<span class='cc-pill'>Available: <b>{cur_available}</b></span> &nbsp; "
        + (f"<span class='cc-badge-low'>LOW • order ≈ <b>{reco_qty}</b></span>" if is_low else "<span class='cc-badge-ok'>OK</span>"),
        unsafe_allow_html=True,
    )

    st.divider()

    # Edit form
    with st.form("inv_edit_form", clear_on_submit=False):
        st.caption("Update counts and thresholds. A transaction log entry is written for quantity changes.")

        c1, c2, c3 = st.columns(3)
        with c1:
            new_on_hand = st.number_input("On hand", min_value=0, value=cur_on_hand, step=1)
        with c2:
            new_reserved = st.number_input("Reserved", min_value=0, value=cur_reserved, step=1)
        with c3:
            # available is derived; we show it but don't directly edit
            st.number_input("Available (derived)", min_value=0, value=max(0, int(new_on_hand) - int(new_reserved)), step=1, disabled=True)

        t1, t2, t3 = st.columns(3)
        with t1:
            new_par = st.number_input("Par level (target)", min_value=0, value=cur_par, step=1)
        with t2:
            new_rop = st.number_input("Reorder point", min_value=0, value=cur_rop, step=1)
        with t3:
            new_pref = st.number_input("Preferred reorder qty", min_value=0, value=cur_pref, step=1)

        lead = st.number_input("Lead time (days)", min_value=0, value=cur_lead, step=1)

        note = st.text_input("Note (optional)", value="")

        save = st.form_submit_button("Save changes", use_container_width=True)

        if save:
            new_available = max(0, int(new_on_hand) - int(new_reserved))

            patch = {
                "on_hand": int(new_on_hand),
                "reserved": int(new_reserved),
                "available": int(new_available),
                "par_level": int(new_par),
                "reorder_point": int(new_rop),
                "preferred_reorder_qty": int(new_pref),
                "lead_time_days": int(lead),
            }

            # Create transaction only if quantity changed
            txn = None
            delta = int(new_on_hand) - cur_on_hand
            if delta != 0:
                txn = {
                    "ts": _now_iso(),
                    "type": "adjust" if (note.strip() == "") else "adjust",
                    "qty_delta": int(delta),
                    "qty_after": int(new_on_hand),
                    "unit": str(current.get("stock_unit") or "unit"),
                    "ref": "UI-INVENTORY",
                    "note": note.strip(),
                }

            try:
                upsert_inventory_item(
                    inventory_col,
                    ingredient_id=selected_id,
                    patch=patch,
                    txn=txn,
                    legacy_container_id=legacy_container_id,
                )
                st.success("Saved ✅")
                st.rerun()
            except Exception as e:
                st.error(f"Save failed: {e}")

    st.markdown('</div>', unsafe_allow_html=True)


with right:
    st.markdown('<div class="cc-card">', unsafe_allow_html=True)
    st.markdown("**Stocking view**")
    st.caption("This is a lightweight ‘what needs attention now’ view. Deeper forecasting belongs in Dashboard Analytics.")

    # Build low-stock list
    low_rows: List[Dict[str, Any]] = []
    ok_count = 0
    for ing_id, label in options:
        item = inv_idx.get(ing_id, {})

        on_hand = int(item.get("on_hand") or 0)
        reserved = int(item.get("reserved") or 0)
        available = int(item.get("available") or max(0, on_hand - reserved))
        rop = int(item.get("reorder_point") or 0)
        par = int(item.get("par_level") or 0)
        pref = int(item.get("preferred_reorder_qty") or 0)
        lead = int(item.get("lead_time_days") or 0)

        is_low, reco = compute_reorder_status({
            "on_hand": on_hand,
            "reserved": reserved,
            "available": available,
            "reorder_point": rop,
            "par_level": par,
            "preferred_reorder_qty": pref,
        })

        if is_low:
            low_rows.append({
                "ingredient_id": ing_id,
                "name": label.split("(")[0].strip(),
                "available": available,
                "reorder_point": rop,
                "par_level": par,
                "recommended_order_qty": reco,
                "lead_time_days": lead,
            })
        else:
            ok_count += 1

    if low_rows:
        st.warning(f"{len(low_rows)} items are below reorder point.")
        st.dataframe(
            low_rows,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.success("All items look stocked right now.")

    


# Footer hint
st.caption(
    "Tip: If you want clean analytics later, keep a transaction log (receive/use/adjust) instead of overwriting counts silently."
)