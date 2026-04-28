import streamlit as st
import pandas as pd
import plotly.express as px
import time

# 1. PAGE CONFIGURATION
st.set_page_config(
    page_title="UNODC ROSA | Financial Dashboard",
    page_icon="🇺🇳",
    layout="wide"
)

# 2. BRANDING & STYLE
st.markdown("""
    <style>
    .main { background-color: #f1f5f9; }
    h1 { color: #005bbb; font-family: 'Segoe UI', sans-serif; }
    .stMetric { background-color: white; padding: 15px; border-radius: 10px; border: 1px solid #e2e8f0; }
    .db-status { font-size: 0.8rem; color: #64748b; }
    </style>
    """, unsafe_allow_html=True)

# 3. DATA LOADING & DATABASE SIMULATION
# World Bank Contract Data (Public Dataset)
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR736Gpr790GywODZRdnzD0l6FNsNtjbQLpU5-9iFE3YxbJEwloLdSnt-6rMPyk7rLV3ZwSF4CigHNa/pub?output=csv"

@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = [c.strip() for c in df.columns]
        return df
    except Exception as e:
        return None

df = load_data()

if df is not None:
    # 4. TOP HEADER & DB STATUS
    col_title, col_status = st.columns([3, 1])
    with col_title:
        st.title("🇺🇳 UNODC Regional Office for South Asia")
        st.subheader("Financial Procurement Tracker & Contract Management")
    with col_status:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("🟢 **Database Status: Connected**")
        st.markdown("<span class='db-status'>Source: World Bank Global Financial Repository</span>", unsafe_allow_html=True)

    st.info("Prototype: Synchronized with World Bank Contract Data via Google Sheets API")

    # 5. KPIS / METRICS
    m1, m2, m3, m4 = st.columns(4)
    
    with m1:
        st.metric("Total Records", len(df))
    
    with m2:
        # Find amount column
        amt_col = next((c for c in df.columns if any(kw in c for kw in ['Amount', 'Value', 'USD'])), None)
        if amt_col:
            total_val = pd.to_numeric(df[amt_col], errors='coerce').sum()
            st.metric("Total Value", f"${total_val:,.0f}")
        else:
            st.metric("Total Value", "$0")

    with m3:
        # Find status/review column
        status_col = next((c for c in df.columns if any(kw in c for kw in ['Status', 'Review'])), None)
        pending_count = 0
        if status_col:
            pending_count = len(df[df[status_col].str.contains('Prior|Pending', na=False, case=False)])
        st.metric("Review Actions", pending_count)
        
    with m4:
        st.metric("Region", "South Asia")

    st.markdown("---")

    # 6. FILTERS & CONTENT
    col_a, col_b = st.columns([2, 1])

    with col_a:
        st.write("### 📋 Contract Award Details")
        search = st.text_input("Search by Supplier, Country, or Description", "")
        
        if search:
            display_df = df[df.apply(lambda row: search.lower() in row.astype(str).str.lower().values, axis=1)]
        else:
            display_df = df
        
        st.dataframe(display_df, use_container_width=True, height=400)
        
        csv = display_df.to_csv(index=False).encode('utf-8')
        st.download_button(label="📥 Download CSV", data=csv, file_name='unodc_report.csv', mime='text/csv')

    with col_b:
        st.write("### 📊 Breakdown")
        cat_col = next((c for c in df.columns if any(kw in c for kw in ['Method', 'Status', 'Review'])), None)
        
        if cat_col:
            counts = df[cat_col].value_counts().reset_index()
            counts.columns = [cat_col, 'Count']
            fig = px.pie(counts, values='Count', names=cat_col, hole=0.4)
            fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig, use_container_width=True)

    # 7. ACTION CENTER
    st.write("---")
    st.write("### ⚡ Management Action Center")
    c1, c2 = st.columns(2)
    with c1:
        supplier_col = next((c for c in df.columns if 'Supplier' in c), df.columns[0])
        target = st.selectbox("Select Project", df[supplier_col].unique())
    with c2:
        decision = st.radio("Action", ["Approve", "Clarify", "Reject"], horizontal=True)
    
    if st.button("Submit Decision"):
        with st.spinner("Processing..."):
            time.sleep(1) 
            st.success(f"SUCCESS: {decision} recorded for {target}.")
            st.code(f"EXEC sp_UpdateStatus @Project='{target}', @Status='{decision}'", language="sql")
else:
    st.error("Application configuration error: Data source unreachable.")
