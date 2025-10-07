import streamlit as st
import pandas as pd
import ast

# =========================
# Load dataset (Excel)
# =========================
FILE_PATH = "converted_with_positive_category_texts.xlsx"
laptop_df = pd.read_excel(FILE_PATH)
laptop_df.columns = laptop_df.columns.str.strip()

# Ensure key columns exist (based on Excel)
def ensure_cols(df, cols):
    for c in cols:
        if c not in df.columns:
            df[c] = None
    return df

required_cols = [
    "source","imageURLs","productURL","reviewURL","sku","brand","model",
    "modelNumber","title","price","ratingAvgDisplay","ratingNum","ratingAvg",
    "questionNum","batteryLife","titleStandard",
    # review fields
    "ReviewsN","reviewStudent","reviewProfessional","reviewGaming",
    "reviewCreative","reviewTravel","reviewPersonal"
]
laptop_df = ensure_cols(laptop_df, required_cols)

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
# Inline toolbar (Purpose control near search)
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
# Bottom-right floating button to SoSci
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
# Sidebar: Filters (locked for study)
# =========================
st.sidebar.header("Filter by (locked):")
st.sidebar.markdown("🔒 The filters below are visible but disabled for this study.")
st.sidebar.slider("Max Price", 50, 1500, 1000, disabled=True)
st.sidebar.slider("Minimum Rating", 0.0, 5.0, 3.0, 0.1, disabled=True)
st.sidebar.slider("Minimum RAM (GB)", 2, 32, 4, disabled=True)

# =========================
# Purpose → column mapping
# =========================
purpose_to_col = {
    "student": "reviewStudent",
    "professional": "reviewProfessional",
    "gaming": "reviewGaming",
    "creative": "reviewCreative",
    "travel": "reviewTravel",
    "personal": "reviewPersonal"
}
selected_review_col = purpose_to_col.get(category_filter.lower(), None)

# =========================
# Filter rows by purpose availability
# =========================
if category_filter in ("All", "none"):
    filtered_df = laptop_df.copy()
else:
    filtered_df = laptop_df[
        laptop_df[selected_review_col].astype(str).str.strip().ne("")
    ].copy()
    st.info(f"Showing laptops with reviews for: **{category_filter.capitalize()}**")

# =========================
# Ranking by number of snippets then rating
# =========================
def count_snips(cell):
    if not isinstance(cell, str) or not cell.strip():
        return 0
    return len([s for s in cell.split("||") if s.strip()])

if selected_review_col and category_filter not in ("All", "none"):
    filtered_df["category_match_count"] = filtered_df[selected_review_col].apply(count_snips)
else:
    filtered_df["category_match_count"] = filtered_df["ReviewsN"].apply(count_snips)

filtered_df["ratingAvg_num"] = pd.to_numeric(filtered_df.get("ratingAvg", 0), errors="coerce").fillna(0)
filtered_df = filtered_df.sort_values(by=["category_match_count", "ratingAvg_num"], ascending=[False, False])

# =========================
# Pagination
# =========================
st.sidebar.write(f"Filtered results: {len(filtered_df)} laptops")
items_per_page = 20
total_items = len(filtered_df)
total_pages = max(1, (total_items - 1) // items_per_page + 1)

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

    # --- Column 1: Images (multi-image horizontal scroll, HTML-based) ---
# --- Column 1: Image (single) ---
    with col1:
        first_url = None
        cell = row.get("imageURLs", "")

        if isinstance(cell, str) and cell.strip():
            try:
                # Try list-like string: '["url1","url2"]'
                parsed = ast.literal_eval(cell)
                if isinstance(parsed, list) and len(parsed) > 0:
                    first_url = str(parsed[0]).strip()
            except Exception:
                # Fallback: split by ||
                parts = [u.strip() for u in cell.split("||") if u.strip()]
                if parts:
                    first_url = parts[0]

        if first_url:
            st.image(first_url, width=160)  # adjust width as you like
            # Optional: link below the image
            st.markdown(f"<a href='{first_url}' target='_blank'>Open image</a>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='product-detail'>[No image]</div>", unsafe_allow_html=True)


    # --- Column 2: Product Info ---
    with col2:
        title_std = row.get("titleStandard") or row.get("title") or "No Title"
        st.markdown(f"<div class='product-title'>{title_std}</div>", unsafe_allow_html=True)

        rating_display = row.get('ratingAvgDisplay', '-') or '-'
        rating_num = row.get('ratingNum', '0') or '0'
        st.markdown(f"<div class='product-detail'>⭐ {rating_display}/5 ({rating_num} reviews)</div>", unsafe_allow_html=True)

        st.markdown("<div class='product-detail'><b>Limited time deal</b></div>", unsafe_allow_html=True)
        price_display = "-" if pd.isna(row.get('price')) else row.get('price')
        st.markdown(f"<div class='price-block'>€{price_display}</div>", unsafe_allow_html=True)

        for label, key in [("Brand", "brand"), ("Model", "model"), ("Battery life", "batteryLife")]:
            val = row.get(key, "-")
            val = "-" if (pd.isna(val) or val is None or str(val).strip() == "") else val
            st.markdown(f"<div class='product-detail'><b>{label}:</b> {val}</div>", unsafe_allow_html=True)

        st.link_button("Add to basket", row.get("productURL", "#") or "#")

    # --- Column 3: Reviews (neutral styling per fairness recommendation) ---
    with col3:
        snippets = []
        if category_filter in ("All", "none"):
            cell = row.get("ReviewsN", "")
            if isinstance(cell, str) and cell.strip():
                for snip in [s for s in cell.split("||") if s.strip()]:
                    snippets.append((snip.strip(), ""))  # unstyled
        else:
            cell = row.get(selected_review_col, "")
            if isinstance(cell, str) and cell.strip():
                for snip in [s for s in cell.split("||") if s.strip()]:
                    snippets.append((snip.strip(), ""))  # keep neutral styling

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
