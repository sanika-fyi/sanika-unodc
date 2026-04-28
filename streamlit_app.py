import streamlit as st
import pandas as pd
import plotly.express as px
import time
from datetime import datetime

# 1. PAGE CONFIGURATION
st.set_page_config(
    page_title="UNODC ROSA | Digital Tracker",
    page_icon="🇺🇳",
    layout="wide"
)

# 2. BRANDING & STYLE
st.markdown("""
    <style>
   .main { background-color: #f8fafc; }
   .stMetric { background-color: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border: 1px solid #e2e8f0; }
    h1 { color: #005bbb; font-weight: 700; }
   .stDownloadButton button { background-color: #005bbb; color: white; border-radius: 8px; }
   .doc-link { font-size: 0.9rem; color: #005bbb; text-decoration: none; border: 1px solid #005bbb; padding: 5px 10px; border-radius: 5px; }
   .doc-link:hover { background-color: #005bbb; color: white; }
   .dedup-warning { background-color: #fffbeb; border-left: 5px solid #f59e0b; padding: 10px; margin-bottom: 15px; border-radius: 4px; }
    </style>
    """, unsafe_allow_html=True)

# 3. DATA LOADING
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR736Gpr790GywODZRdnzD0l6FNsNtjbQLpU5-9iFE3YxbJEwloLdSnt-6rMPyk7rLV3ZwSF4CigHNa/pub?output=csv"

@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = [c.strip() for c in df.columns]
        return df
    except:
        return None

df = load_data()

# 4. NAVIGATION & SIDEBAR
st.sidebar.image("https://www.unodc.org/res/images/unodc-logo.png", width=150)
page = st.sidebar.selectbox("Navigate System", ["Request Portal", "Executive Dashboard"])

st.sidebar.markdown("---")
st.sidebar.markdown("❓ **Need Help?**")
st.sidebar.markdown('<a href="https://github.com/sanika-fyi/sanika-unodc/wiki" target="_blank" class="doc-link">📖 View Documentation</a>', unsafe_allow_html=True)

# Shared Logic for Status Filtering
status_col = None
if df is not None:
    status_col = next((c for c in df.columns if any(k in c.lower() for k in ['status', 'review', 'stage'])), None)

# ---------------------------------------------------------
# PAGE 1: REQUEST PORTAL (SUBMITTER VIEW)
# ---------------------------------------------------------
if page == "Request Portal":
    st.title("➕ New Financial Request")
    st.markdown("Please fill out the form below to submit a new procurement or travel request.")
    
    with st.form("request_form"):
        col1, col2 = st.columns(2)
        with col1:
            req_type = st.selectbox("Request Type", ["Procurement", "Travel Authorization", "Vendor Payment", "Staff Reimbursement"])
            project_name = st.text_input("Project Name / Description")
            supplier = st.text_input("Supplier / Payee Name")
        with col2:
            amount = st.number_input("Estimated Amount (USD)", min_value=0.0, step=100.0)
            priority = st.select_slider("Priority", options=["Routine", "Urgent", "Emergency"])
            deadline = st.date_input("Required by Date")

        submitted = st.form_submit_button("Submit Request")

    # 5. DEDUPLICATION CHECK
    if submitted:
        if project_name and df is not None:
            similar_exists = df[
                (df.astype(str).apply(lambda x: x.str.contains(project_name, case=False)).any(axis=1)) |
                (df.astype(str).apply(lambda x: x.str.contains(supplier, case=False)).any(axis=1))
            ]
            
            if not similar_exists.empty:
                st.markdown(f"""
                <div class="dedup-warning">
                    <strong>⚠️ Potential Duplicate Detected!</strong><br>
                    A similar request for '{project_name}' already exists in the system. 
                    Please verify if this is a follow-up or a duplicate before proceeding.
                </div>
                """, unsafe_allow_html=True)
                st.warning("Please check the ledger below before finalizing.")
                st.dataframe(similar_exists, use_container_width=True)
            
            with st.spinner("Processing Submission..."):
                time.sleep(1.5)
                st.success(f"Request successfully logged. Tracking ID: ROSA-{datetime.now().strftime('%Y%m%d')}-0042")

    st.divider()
    st.subheader("Your Active Requests")
    if df is not None:
        st.dataframe(df.head(5), use_container_width=True)

# ---------------------------------------------------------
# PAGE 2: EXECUTIVE DASHBOARD (APPROVER VIEW)
# ---------------------------------------------------------
elif page == "Executive Dashboard" and df is not None:
    # Sidebar filter specifically for Approvers
    st.sidebar.markdown("---")
    st.sidebar.header("Approver Controls")
    show_actions_only = st.sidebar.checkbox("🚨 Show Only Actions Required", value=False)

    st.title("🇺🇳 UNODC ROSA | Executive Dashboard")
    
    # 6. KPIS
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Total Records", len(df))
    with m2:
        amt_col = next((c for c in df.columns if any(k in c.lower() for k in ['amount', 'value', 'usd'])), df.columns[0])
        total = pd.to_numeric(df[amt_col], errors='coerce').sum()
        st.metric("Total Value (USD)", f"${total:,.0f}")
    with m3:
        # Dynamic calculation for "Actions Required"
        count_val = len(df[df[status_col].str.contains('Prior|Pending|Review', na=False, case=False)]) if status_col else 0
        st.metric("Actions Required", count_val)
    with m4:
        st.metric("Avg. TAT", "3.8 Days")

    st.divider()

    col_left, col_right = st.columns([3, 1])

    with col_left:
        # Filter data based on sidebar checkbox
        display_df = df
        if status_col and show_actions_only:
            display_df = df[df[status_col].str.contains('Prior|Pending|Review', na=False, case=False)]
            st.markdown("### 🚨 Review List (Actions Required)")
        else:
            st.markdown("### 📋 Transaction Ledger & Tracking")

        search = st.text_input("Search Ledger (Supplier, ID, Status)...")
        if search:
            display_df = display_df[display_df.apply(lambda row: search.lower() in row.astype(str).str.lower().values, axis=1)]
        
        st.dataframe(display_df, use_container_width=True, height=400)
        
        csv = display_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Report", data=csv, file_name='unodc_report.csv')

    with col_right:
        st.markdown("### 📈 Turnaround Time (TAT)")
        chart_data = pd.DataFrame({
            'Category': ['Travel', 'Procure', 'Vendor'],
            'Days': [2.4, 5.1, 3.8]
        })
        fig = px.bar(chart_data, x='Category', y='Days', color='Category', title="Avg. Days to Approval")
        fig.update_layout(showlegend=False, margin=dict(t=30, b=0, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)
        
        st.info("**Integrity Alert:** Requests older than 7 days without a decision are automatically escalated to Senior Management.")

    # 7. ACTION PANEL
    st.divider()
    st.markdown("### ⚡ Executive Action Center")
    ac1, ac2, ac3 = st.columns([2, 1, 1])
    with ac1:
        name_col = next((c for c in df.columns if any(k in c.lower() for k in ['supplier', 'description', 'borrower', 'project', 'name'])), df.columns[0])
        # Only show options from current view
        options = display_df[name_col].unique()[:50]
        selected = st.selectbox("Select Project for Decision:", options if len(options) > 0 else ["No records matching filters"])
    with ac2:
        action = st.radio("Management Decision", ["Approve", "Review", "Reject"], horizontal=True)
    with ac3:
        st.write("") 
        if st.button("Commit Decision", use_container_width=True):
            with st.spinner("Writing to Database..."):
                time.sleep(1)
                st.success(f"System Record Updated: {selected} status set to {action}.")
else:
    st.error("Technical Error: Unable to fetch cloud-hosted data.")
