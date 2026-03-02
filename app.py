"""
A/B Test Data Simulator
Helps students generate realistic simulated datasets for A/B testing exercises.
"""

import streamlit as st
import pandas as pd
import numpy as np
from faker import Faker
import io

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
st.caption("Define your experiment and download simulated data as CSVs.")

# ── 1 · Treatment variable ──────────────────────────────────────────────────
st.subheader("1 · A/B Test Variable (0/1)")
ab_col = st.text_input("Variable name", value="")

# ── 2 · Dependent variable ──────────────────────────────────────────────────
st.subheader("2 · Dependent Variable")
dv_col = st.text_input("Variable name", value="", key="dv_name")
dv_type = st.radio("Type", ["Binary (0/1)", "Numeric (continuous)"], horizontal=True)

if dv_type == "Numeric (continuous)":
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
                ["Numeric", "Binary (0/1)", "Categorical"],
                index=["Numeric", "Binary (0/1)", "Categorical"].index(cov["type"]),
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
    n = int(np.random.default_rng().integers(40_000, 60_001))

    # Randomised effect size between -0.5 and 0.5
    effect_size = rng.uniform(-0.5, 0.5)

    # Treatment assignment (balanced 50/50)
    assignment = rng.integers(0, 2, n)
    df = pd.DataFrame({ab_col: assignment})

    # Dependent variable
    if dv_type == "Numeric (continuous)":
        base = rng.uniform(dv_min, dv_max, n)
        shift = np.where(assignment == 1, effect_size, 0.0)
        df[dv_col] = np.round(base + shift, 2)
    else:
        base_prob = 0.10
        probs = np.where(
            assignment == 1,
            np.clip(base_prob + effect_size, 0.01, 0.99),
            base_prob,
        )
        df[dv_col] = rng.binomial(1, probs)

    # Custom covariates
    for cov in st.session_state.covariates:
        name = cov["name"].strip()
        if not name:
            continue
        if cov["type"] == "Numeric":
            df[name] = np.round(rng.uniform(float(cov["min"]), float(cov["max"]), n), 2)
        elif cov["type"] == "Binary (0/1)":
            df[name] = rng.integers(0, 2, n)
        elif cov["type"] == "Categorical":
            cats = [c.strip() for c in cov["categories"].split(",") if c.strip()]
            if cats:
                df[name] = rng.choice(cats, n)

    # Auto-generated realistic covariates (Faker-powered)
    Faker.seed(random_seed)
    df["age"] = rng.integers(18, 76, n)
    df["gender"] = rng.choice(["Male", "Female", "Non-binary"], n, p=[0.48, 0.48, 0.04])
    df["region"] = [fake.state() for _ in range(n)]
    df["device"] = rng.choice(["Mobile", "Desktop", "Tablet"], n, p=[0.55, 0.35, 0.10])
    df["signup_days_ago"] = rng.integers(1, 731, n)
    df["sessions_last_30d"] = rng.poisson(12, n)

    df.insert(0, "id", range(1, n + 1))
    return df


# ── Generate & display ───────────────────────────────────────────────────────
if st.button("Simulate Data", type="primary", use_container_width=True):
    with st.spinner("Simulating…"):
        st.session_state["generated_data"] = generate_data()

if "generated_data" in st.session_state:
    data = st.session_state["generated_data"]
    st.success(f"**{len(data):,}** rows  ×  **{len(data.columns)}** columns")

    tab_preview, tab_stats = st.tabs(["Preview", "Summary"])
    with tab_preview:
        st.dataframe(data.head(100), use_container_width=True)
    with tab_stats:
        st.dataframe(
            data.groupby(ab_col).describe().T,
            use_container_width=True,
        )

    csv = io.StringIO()
    data.to_csv(csv, index=False)
    st.download_button(
        "⬇ Download CSV",
        csv.getvalue(),
        file_name="ab_test_data.csv",
        mime="text/csv",
        use_container_width=True,
    )
