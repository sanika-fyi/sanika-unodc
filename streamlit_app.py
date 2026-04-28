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
   .main { background-color: #f8fafc; }
   .stMetric { background-color: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border: 1px solid #e2e8f0; }
    h1 { color: #005bbb; font-weight: 700; }
   .stDownloadButton button { background-color: #005bbb; color: white; border-radius: 8px; }
   .doc-link { font-size: 0.9rem; color: #005bbb; text-decoration: none; border: 1px solid #005bbb; padding: 5px 10px; border-radius: 5px; }
   .doc-link:hover { background-color: #005bbb; color: white; }
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

if df is not None:
    # 4. SIDEBAR
    st.sidebar.image("https://www.unodc.org/res/images/unodc-logo.png", width=150)
    
    st.sidebar.header("System Navigation")
    # THE DOCUMENTATION LINK
    st.sidebar.markdown("---")
    st.sidebar.markdown("❓ **Stuck or Need Help?**")
    st.sidebar.markdown('<a href="https://github.com/sanika-fyi/sanika-unodc/wiki" target="_blank" class="doc-link">📖 View Documentation</a>', unsafe_allow_html=True)
    st.sidebar.markdown("---")

    # Workflow Control
    st.sidebar.header("Workflow Control")
    status_col = next((c for c in df.columns if any(k in c.lower() for k in ['status', 'review', 'stage'])), None)
    
    if status_col:
        show_actions_only = st.sidebar.checkbox("🚨 Show Only Actions Required", value=False)
        if show_actions_only:
            filter_mask = df[status_col].str.contains('Prior|Pending|Review', na=False, case=False)
            display_df = df[filter_mask]
        else:
            display_df = df
    else:
        display_df = df

    # 5. HEADER
    st.title("🇺🇳 UNODC Regional Office for South Asia")
    st.subheader("Financial Request & Procurement Tracking System")
    st.caption("Live Prototype | Phase 1: Operational Visibility Layer")

    # 6. KPIS
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Total Records", len(df))
    with m2:
        amt_col = next((c for c in df.columns if any(k in c.lower() for k in ['amount', 'value', 'usd'])), df.columns[0])
        total = pd.to_numeric(df[amt_col], errors='coerce').sum()
        st.metric("Total Value (USD)", f"${total:,.0f}")
    with m3:
        if status_col:
            count_val = len(df[df[status_col].str.contains('Prior|Pending|Review', na=False, case=False)])
        else:
            count_val = 0
        st.metric("Actions Required", count_val)
    with m4:
        st.metric("Regional Office", "New Delhi (ROSA)")

    st.divider()

    # 7. MAIN CONTENT
    col_left, col_right = st.columns([3, 1])

    with col_left:
        title_text = "🚨 Review List (Actions Required)" if (status_col and show_actions_only) else "📋 Full Transaction Ledger"
        st.markdown(f"### {title_text}")
        
        search = st.text_input("Search Ledger (Supplier, Country, or ID)...")
        if search:
            display_df = display_df[display_df.apply(lambda row: search.lower() in row.astype(str).str.lower().values, axis=1)]
        
        st.dataframe(display_df, use_container_width=True, height=450)
        
        csv = display_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export Current View to CSV", data=csv, file_name='unodc_action_report.csv')

    with col_right:
        st.markdown("### 📊 Status Distribution")
        cat_col = next((c for c in df.columns if any(kw in c.lower() for kw in ['status', 'method', 'type'])), None)
        if cat_col:
            fig = px.pie(df, names=cat_col, hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), showlegend=True)
            st.plotly_chart(fig, use_container_width=True)
        
        st.info("**Integrity Note:** This interface centralizes data from multiple units to eliminate manual tracking overhead.")

    # 8. ACTION PANEL
    st.divider()
    st.markdown("### ⚡ Executive Action Center")
    ac1, ac2, ac3 = st.columns([2, 1, 1])
    with ac1:
        # UPDATED: Looking for Supplier, Description or Name instead of ID
        name_col = next((c for c in df.columns if any(k in c.lower() for k in ['supplier', 'description', 'borrower', 'project', 'name'])), df.columns[0])
        options = display_df[name_col].unique()
        selected = st.selectbox("Select Project/Supplier for Decision:", options if len(options) > 0 else ["No records found"])
    with ac2:
        action = st.radio("Management Decision", ["Approve", "Review", "Reject"], horizontal=True)
    with ac3:
        st.write("") 
        if st.button("Commit to Database", use_container_width=True):
            with st.spinner("Updating Central Ledger..."):
                time.sleep(1)
                st.success(f"Success: {selected} updated to {action}.")
                st.balloons()
else:
    st.error("Technical Error: Unable to fetch cloud-hosted data.")
