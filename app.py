"""
A/B Test Data Simulator
Helps students generate realistic simulated datasets for A/B testing exercises.
"""

import streamlit as st
import pandas as pd
import numpy as np
from faker import Faker
import io
import zipfile

fake = Faker()

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="A/B Test Data Simulator",
    page_icon="👾",
    layout="centered",
)

st.markdown(
    """
    <style>
    .block-container {max-width: 720px; padding-top: 2rem;}
    h1 {font-size: 1.8rem !important;}
    h3 {font-size: 1.15rem !important; margin-top: 1.2rem !important;}
    .stDownloadButton > button {width: 100%;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("👾 A/B Test Data Simulator")
st.caption("Define your experiment and download simulated data.")

# ── 1 · Treatment variable ──────────────────────────────────────────────────
st.subheader("1 · A/B Test Variable")
ab_col = st.text_input("Variable name", value="", key="ab_col")

# ── 2 · Dependent variable ──────────────────────────────────────────────────
st.subheader("2 · Dependent Variable")
dv_col = st.text_input("Variable name", value="", key="dv_name")
dv_type = st.radio("Type", ["Binary", "Numeric"], horizontal=True)

if dv_type == "Numeric":
    c1, c2 = st.columns(2)
    with c1:
        dv_min = st.number_input("Min", value=0.0, step=1.0)
    with c2:
        dv_max = st.number_input("Max", value=100.0, step=1.0)

# ── 3 · Custom covariates ───────────────────────────────────────────────────
st.subheader("3 · Custom Covariates")

if "covariates" not in st.session_state:
    st.session_state.covariates = []

if st.button("＋  Add covariate", use_container_width=True):
    st.session_state.covariates.append(
        {"name": "", "type": "Numeric", "min": 0.0, "max": 100.0, "categories": "A, B, C"}
    )

for i, cov in enumerate(st.session_state.covariates):
    with st.container(border=True):
        cols = st.columns([3, 2, 1])
        with cols[0]:
            cov["name"] = st.text_input("Name", value=cov["name"], key=f"cn_{i}")
        with cols[1]:
            cov["type"] = st.selectbox(
                "Type",
                ["Numeric", "Binary", "Categorical"],
                index=["Numeric", "Binary", "Categorical"].index(cov["type"]),
                key=f"ct_{i}",
            )
        with cols[2]:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("✕", key=f"cd_{i}"):
                st.session_state.covariates.pop(i)
                st.rerun()

        if cov["type"] == "Numeric":
            r1, r2 = st.columns(2)
            with r1:
                cov["min"] = st.number_input("Min", value=cov["min"], key=f"cmin_{i}")
            with r2:
                cov["max"] = st.number_input("Max", value=cov["max"], key=f"cmax_{i}")
        elif cov["type"] == "Categorical":
            cov["categories"] = st.text_input(
                "Categories (comma-separated)", value=cov["categories"], key=f"cc_{i}"
            )

st.divider()

# ── Fixed generation parameters (hidden from user) ──────────────────────────
random_seed = 42

# ══════════════════════════════════════════════════════════════════════════════
# DATA GENERATION
# ══════════════════════════════════════════════════════════════════════════════

def generate_data() -> pd.DataFrame:
    rng = np.random.default_rng(random_seed)
    n = int(rng.integers(40_000, 60_001))

    # Treatment assignment
    _treatment_values = np.array(['v_A', 'version_A', 'version_A', 'ver_A', 'v_B', 'version_B', 'version_B', 'ver_B', None], dtype=object)
    assignment = rng.choice(_treatment_values, size=n)
    df = pd.DataFrame({ab_col: assignment})

    # Auto-generated covariates
    df["user_reg_name"] = [fake.name() for _ in range(n)]
    df["age"] = rng.integers(18, 75, n)
    df["gender"] = rng.choice(["Male", "Female", "Non-binary", None], n, p=[0.48, 0.48, 0.03, 0.01])
    df["user_country_of_origin"] = np.array([rng.choice([fake.country_code(), 'NL', 'nl', None], p=[0.5, 0.2, 0.2, 0.1]) for _ in range(n)])
    df["user_registration_date"] = pd.to_datetime("2006-01-01") + pd.to_timedelta(rng.integers(0, 365*20, n), unit="D")
    df["device"] = [fake.user_agent() for _ in range(n)]

    # Custom covariates
    for cov in st.session_state.covariates:
        name = cov["name"].strip()
        if not name:
            continue
        if cov["type"] == "Numeric":
            df[name] = np.round(rng.uniform(float(cov["min"]), float(cov["max"]), n), 2)
        elif cov["type"] in ["Binary", "Binary (0/1)"]:
            df[name] = rng.integers(0, 2, n)
        elif cov["type"] == "Categorical":
            cats = [c.strip() for c in cov.get("categories","").split(",") if c.strip()]
            if cats:
                df[name] = rng.choice(cats, n)

    # Effect scaling 
    if dv_type == "Numeric":
        dv_range = dv_max - dv_min
    else:
        dv_range = 1
        
    total_shift = np.zeros(n)

    # Treatment effect
    treatment_direction = rng.choice([-1, 1])
    treatment_shift = np.where(np.isin(assignment, ['v_A', 'version_A', 'ver_A']),
                               treatment_direction * (0.25 * dv_range * rng.uniform(0.5, 1.0, n)), 0.0)
    total_shift += treatment_shift

    # Age effect
    age_direction = rng.choice([-1, 1])
    age_scaled = (df["age"] - df["age"].mean()) / df["age"].std()
    age_effect = age_direction * age_scaled * (0.12 * dv_range * rng.uniform(0.5, 1.0, n))
    total_shift += age_effect

    # Gender effect
    gender_direction = rng.choice([-1, 1])
    gender_effect = np.where(df["gender"] == "Male", gender_direction * 0.08 * dv_range * rng.uniform(0.5, 1.0, n), 0.0)
    total_shift += gender_effect

    # Custom covariate effects
    for cov in st.session_state.covariates:
        name = cov["name"].strip()
        if not name:
            continue
        cov_direction = rng.choice([-1, 1])
        if cov["type"] == "Numeric":
            val_scaled = (df[name] - df[name].mean()) / df[name].std()
            total_shift += cov_direction * val_scaled * (0.1 * dv_range * rng.uniform(0.5, 1.0, n))
        elif cov["type"] in ["Binary","Binary (0/1)"]:
            total_shift += cov_direction * df[name] * (0.05 * dv_range * rng.uniform(0.5, 1.0, n))
        elif cov["type"] == "Categorical":
            cats = df[name].dropna().unique()
            cat_effect = {c: cov_direction * 0.05 * dv_range * rng.uniform(0.5, 1.0) for c in cats}
            total_shift += df[name].map(cat_effect).fillna(0.0)

    # Dependent variable 
    if dv_type == "Numeric":
        base = rng.normal(0, 1, n)  # normal base
        y_temp = base + total_shift
        # center DV to mid-range and scale
        y_temp = y_temp - y_temp.mean() + (dv_min + dv_max)/2
        df[dv_col] = np.round(np.clip(y_temp, dv_min, dv_max), 2)
    else:  # Binary DV
        linear_pred = total_shift
        linear_pred_centered = linear_pred - linear_pred.mean()
        prob = 1 / (1 + np.exp(-linear_pred_centered))
        df[dv_col] = rng.binomial(1, prob)

    df.insert(0, "id", range(1, n+1))
    return df

# ── Generate & display ───────────────────────────────────────────────────────
if st.button("Simulate Data", type="primary", use_container_width=True):
    if not ab_col.strip() or not dv_col.strip():
        st.error("Please enter names for both the A/B test variable and the dependent variable.")
    else:
        with st.spinner("Simulating…"):
            st.session_state["generated_data"] = generate_data()

if "generated_data" in st.session_state:
    data = st.session_state["generated_data"]
    st.success(f"**{len(data):,}** rows  ×  **{len(data.columns)}** columns")

    #splitting data in independent data and dependent data
    data1= data[["id", ab_col]]
    data2= data.drop(columns=[ab_col])
    data2.rename(columns={"id": "ID"}, inplace=True) #change id column name for one of the files

    st.markdown("""
    <style>
    [data-testid="stElementToolbar"] {
        display: none;
    }
    </style>
    """, unsafe_allow_html=True)
    st.subheader("Preview")
    st.dataframe(data.head(100), use_container_width=True)

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        # Pickle first DataFrame
        buf1 = io.BytesIO()
        data1.to_pickle(buf1)
        zf.writestr("treatment_vars.pkl", buf1.getvalue())
    
        # Pickle second DataFrame
        buf2 = io.BytesIO()
        data2.to_pickle(buf2)
        zf.writestr("outcome_and_control_vars.pkl", buf2.getvalue())
    
    # Move cursor to start
    zip_buffer.seek(0)
    
    # Download button
    st.download_button(
        label="⬇ Download data",
        data=zip_buffer,
        file_name="ab_test_data.zip",
        mime="application/zip",
        use_container_width=True
    )
