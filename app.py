import streamlit as st
import pandas as pd
import requests
from PIL import Image
from io import BytesIO
import ast
import random

# =========================
# Load dataset
# =========================
file_path = "categorized_reviews_output.csv"
laptop_df = pd.read_csv(file_path)
laptop_df.columns = laptop_df.columns.str.strip()

# --- Extract GB values ---
def extract_gb(value):
    try:
        if isinstance(value, str) and "gigabyte" in value.lower():
            # e.g., "16 gigabytes" / "16 gigabyte"
            parts = value.lower().split()
            for p in parts:
                if p.isdigit():
                    return int(p)
        elif isinstance(value, str) and "gb" in value:
            # e.g., "16GB" or "16 GB"
            return int(value.split("GB")[0].strip())
    except:
        return None
    return value

laptop_df["RAM"] = laptop_df.get("systemMemoryRam", pd.Series([None]*len(laptop_df))).apply(extract_gb)
laptop_df["Storage"] = laptop_df.get("totalStorageCapacity", pd.Series([None]*len(laptop_df))).apply(extract_gb)

# Ensure columns exist to avoid KeyErrors later
for col in [
    "Detected_Categories","ReviewsN","imageURLs","titleStandard","ratingAvgDisplay",
    "ratingNum","price","screenSize","storageType","processorSpeedBase",
    "systemMemoryRam","productURL","ratingAvg"
]:
    if col not in laptop_df.columns:
        laptop_df[col] = None

# =========================
# Page Setup
# =========================
st.set_page_config(layout="wide")

# =========================
# Top Bar (HTML)
# =========================
st.markdown("""
<style>
.top-bar {
    background-color: #232f3e;
    color: white;
    padding: 10px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.search-box input {
    width: 100%;
    padding: 5px;
}
.product-title {
    font-size: 18px;
    font-weight: bold;
    margin-bottom: 5px;
}
.product-detail {
    font-size: 14px;
    margin-bottom: 4px;
}
.price-block {
    font-size: 20px;
    color: #B12704;
    font-weight: bold;
    margin-top: 8px;
    margin-bottom: 8px;
}
.review-box {
    background-color: #f6f6f6;
    padding: 10px;
    border-radius: 5px;
    margin-top: 10px;
    margin-bottom: 10px;
}
.scroll-container {
    display: flex;
    overflow-x: auto;
    gap: 10px;
}
.toolbar-row {
    padding: 6px 0 4px 0;
}
.toolbar-label {
    font-weight: 600;
    margin-right: 6px;
}
</style>
<div class="top-bar">
    <div><b>Vacos.de</b></div>
    <div class="search-box"><input type="text" placeholder="Search (disabled in study version)" disabled></div>
    <div>Delivering to Essen 45127 | EN | Account & Lists | Orders | 🛒</div>
</div>
""", unsafe_allow_html=True)

# =========================
# Inline toolbar
# =========================
tb1, tb2, tb3 = st.columns([2.5, 3.5, 1.5])
with tb3:
    if "purpose" not in st.session_state:
        st.session_state.purpose = "All"
    st.markdown("<div class='toolbar-row'><span class='toolbar-label'>🎯 Purpose</span></div>", unsafe_allow_html=True)

    purpose_options = ["All", "student", "creative", "professional", "gaming", "personal", "travel", "none"]
    st.session_state.purpose = st.selectbox(
        "Purpose",
        purpose_options,
        index=purpose_options.index(st.session_state.purpose) if st.session_state.purpose in purpose_options else 0,
        label_visibility="collapsed",
        key="purpose_select_top"
    )

category_filter = st.session_state.purpose

# =========================
# Bottom-right floating button
# =========================
st.markdown("""
<style>
.fixed-bottom-right {
    position: fixed;
    bottom: 30px;
    right: 30px;
    background-color: #ff914d;
    color: white;
    padding: 10px 20px;
    border-radius: 8px;
    font-weight: bold;
    box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    text-align: center;
    z-index: 9999;
}
.fixed-bottom-right:hover { background-color: #e67300; }
</style>
<a href="https://www.soscisurvey.de/prodpurp/index.php?i=ZO8Z3FJQ09XL&rnd=UITP" target="_self">
    <div class="fixed-bottom-right">Next ➡️</div>
</a>
""", unsafe_allow_html=True)

# =========================
# Sidebar: Filters (locked)
# =========================
st.sidebar.header("Filter by (locked):")
st.sidebar.markdown("🔒 The filters below are visible but disabled for this study.")
st.sidebar.slider("Max Price", 50, 1500, 1000, disabled=True)
st.sidebar.slider("Minimum Rating", 0.0, 5.0, 3.0, 0.1, disabled=True)
st.sidebar.slider("Minimum RAM (GB)", 2, 32, 4, disabled=True)

# =========================
# Filtering by review purpose
# =========================
if category_filter == "All":
    filtered_df = laptop_df.copy()
else:
    # broad contains, case-insensitive
    filtered_df = laptop_df[laptop_df["Detected_Categories"].astype(str).str.contains(category_filter, case=False, na=False)].copy()
    st.info(f"Showing laptops reviewed for the purpose: **{category_filter.capitalize()}**")

# =========================
# Ranking by match count then rating
# =========================
def count_matching_reviews(row, category):
    if category == "All":
        return 0
    raw = str(row.get("Detected_Categories", "")).lower()
    # Normalize separators to ||
    normalized = raw.replace(",", "||").replace("|", "||")
    # Split and compare by substring containment for robustness
    cats = [c.strip() for c in normalized.split("||") if c.strip()]
    # exact token match first; if not present, accept substring matches
    exact = sum(1 for c in cats if c == category.lower())
    if exact:
        return exact
    return sum(1 for c in cats if category.lower() in c)

filtered_df["category_match_count"] = filtered_df.apply(lambda row: count_matching_reviews(row, category_filter), axis=1)

# if ratingAvg might be missing or non-numeric, coerce for sorting
filtered_df["ratingAvg_num"] = pd.to_numeric(filtered_df.get("ratingAvg", pd.Series([None]*len(filtered_df))), errors="coerce").fillna(0)

filtered_df = filtered_df.sort_values(by=["category_match_count", "ratingAvg_num"], ascending=[False, False])

# =========================
# Pagination
# =========================
st.sidebar.write(f"Filtered results: {len(filtered_df)} laptops")
items_per_page = 20
total_items = len(filtered_df)
total_pages = (total_items - 1) // items_per_page + 1

if "page" not in st.session_state:
    st.session_state.page = 1

prev_col, next_col = st.sidebar.columns(2)
with prev_col:
    if st.button("⬅️ Previous") and st.session_state.page > 1:
        st.session_state.page -= 1
with next_col:
    if st.button("Next ➡️") and st.session_state.page < total_pages:
        st.session_state.page += 1

page = st.session_state.page
start_idx = (page - 1) * items_per_page
end_idx = start_idx + items_per_page
current_df = filtered_df.iloc[start_idx:end_idx]
st.sidebar.markdown(f"**Page {page} of {total_pages}**")

# =========================
# Product List Header
# =========================
st.markdown("## Laptop Results")

# =========================
# Render Product Cards
# =========================
for _, row in current_df.iterrows():
    col1, col2, col3 = st.columns([1, 2, 2])

    # --- Column 1: Images ---
    with col1:
        try:
            img_urls = []
            if isinstance(row["imageURLs"], str) and row["imageURLs"].strip():
                try:
                    # try parsing Python-literal-style lists
                    img_urls = ast.literal_eval(row["imageURLs"])
                    if not isinstance(img_urls, list):
                        img_urls = []
                except Exception:
                    # try splitting by common separators
                    img_urls = [u.strip() for u in row["imageURLs"].split("||") if u.strip()]
            if img_urls:
                st.markdown("<div class='scroll-container'>", unsafe_allow_html=True)
                for img_url in img_urls:
                    try:
                        resp = requests.get(img_url, timeout=6)
                        resp.raise_for_status()
                        st.image(Image.open(BytesIO(resp.content)), width=120)
                    except:
                        st.markdown("<div class='product-detail'>[Image not available]</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='product-detail'>[No image]</div>", unsafe_allow_html=True)
        except:
            st.markdown("<div class='product-detail'>[Invalid image format]</div>", unsafe_allow_html=True)

    # --- Column 2: Product Info ---
    with col2:
        st.markdown(f"<div class='product-title'>{row.get('titleStandard', 'No Title') or 'No Title'}</div>", unsafe_allow_html=True)
        rating_display = row.get('ratingAvgDisplay', '-') or '-'
        rating_num = row.get('ratingNum', '0') or '0'
        st.markdown(f"<div class='product-detail'>⭐ {rating_display}/5 ({rating_num} reviews)</div>", unsafe_allow_html=True)
        st.markdown("<div class='product-detail'><b>Limited time deal</b></div>", unsafe_allow_html=True)
        price_display = row.get('price', '-') if pd.notna(row.get('price', '-')) else '-'
        st.markdown(f"<div class='price-block'>€{price_display}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='product-detail'><b>Display Size:</b> {row.get('screenSize', '-') or '-'}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='product-detail'><b>Hard disk:</b> {row.get('storageType', '-') or '-'}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='product-detail'><b>CPU Speed:</b> {row.get('processorSpeedBase', '-') or '-'}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='product-detail'><b>Memory:</b> {row.get('systemMemoryRam', '-') or '-'}</div>", unsafe_allow_html=True)
        st.link_button("Add to basket", row.get("productURL", "#") or "#")

    # --- Column 3: Reviews (highlight selected purpose) ---
    with col3:
        reviews_all = row.get("ReviewsN", "")
        cats_all = row.get("Detected_Categories", "")
        snippets = []

        if isinstance(reviews_all, str) and reviews_all.strip():
            review_list = [r.strip() for r in reviews_all.split("||")]
            # normalize separators to handle commas or pipes in category string
            raw = str(cats_all)
            normalized = raw.replace(",", "||").replace("|", "||")
            category_list = [c.strip().lower() for c in normalized.split("||")] if isinstance(raw, str) else []

            for review, cat in zip(review_list, category_list):
                if category_filter == "All":
                    snippets.append((review, ""))  # show all reviews unstyled
                else:
                    # substring match to catch multi-label category strings
                    if category_filter.lower() in cat:
                        snippets.append((review, "font-weight:700;color:blue;"))
                    else:
                        # include non-matching reviews but unstyled, if you want ALL visible:
                        # snippets.append((review, ""))  # uncomment to always show all
                        pass

            # Fallback: if a specific category was chosen and no reviews matched, show a few general ones
            if category_filter != "All" and not snippets:
                snippets = [(rv, "") for rv in review_list[:5]]

        if snippets:
            st.markdown("<div class='review-box'><b>What users say:</b>", unsafe_allow_html=True)
            for snip, style in snippets[:5]:
                st.markdown(f"<div class='product-detail' style='{style}'>• {snip}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")

# =========================
# Download Button
# =========================
st.download_button(
    label="Download Filtered CSV",
    data=filtered_df.drop(columns=["ratingAvg_num"], errors="ignore").to_csv(index=False).encode('utf-8'),
    file_name="filtered_laptops.csv",
    mime="text/csv"
)
