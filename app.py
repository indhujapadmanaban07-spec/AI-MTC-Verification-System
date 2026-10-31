import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import uuid
import database
import extractor
import validator
import fraud_detector
import report_generator
import hashlib
import email_service
from dotenv import load_dotenv
import os
from datetime import datetime

# Load env variables (for GEMINI_API_KEY)
load_dotenv()

st.set_page_config(page_title="MTC Verification System", page_icon="🛡️", layout="wide")

# Initialize Context
database.init_db()

# --- Authentication State ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = ""
if 'login_time' not in st.session_state:
    st.session_state['login_time'] = ""

def render_auth_page():
    st.markdown("<h1 style='text-align: center;'>🔒 MTC Verification System Login</h1>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Login", "Register New User"])
    
    with tab1:
        st.subheader("Login to your account")
        with st.form("login_form"):
            login_user = st.text_input("Username")
            login_pass = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            
            if submitted:
                if database.verify_user(login_user, login_pass):
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = login_user
                    st.session_state['login_time'] = datetime.now().strftime("%Y-%m-%d %H:%M")
                    st.success("Logged in successfully!")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
                    
    with tab2:
        st.subheader("Register a new account")
        with st.form("register_form"):
            reg_user = st.text_input("Choose a Username")
            reg_email = st.text_input("Email Address")
            reg_pass = st.text_input("Choose a Password", type="password")
            reg_pass_confirm = st.text_input("Confirm Password", type="password")
            reg_submitted = st.form_submit_button("Register")
            
            if reg_submitted:
                if reg_pass != reg_pass_confirm:
                    st.error("Passwords do not match.")
                elif len(reg_pass) < 6:
                    st.error("Password must be at least 6 characters.")
                elif not reg_user or not reg_email:
                    st.error("All fields are required.")
                else:
                    success = database.register_user(reg_user, reg_pass, reg_email)
                    if success:
                        st.success("Registration successful! Please login.")
                    else:
                        st.error("Username already exists. Please choose another.")

if not st.session_state['logged_in']:
    render_auth_page()
    st.stop()

# App continues only if logged in...

# --- SIDEBAR ---
with st.sidebar:
    st.header("👤 User Profile")
    
    if st.session_state.get('logged_in'):
        st.markdown(f"### Welcome, {st.session_state['username']}!")
        
        # Get fresh counts from database
        user_certs = database.get_user_certificate_count(st.session_state['username'])
        total_sys_certs = database.get_total_certificate_count()
        
        # User stats card
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1E3A8A, #3B82F6); padding: 15px; border-radius: 10px; margin-bottom: 15px;">
            <div style="color: white; text-align: center;">
                <div style="font-size: 1.1rem;">📊 Your Stats</div>
                <div style="display: flex; justify-content: space-around; margin-top: 10px;">
                    <div>
                        <div style="font-size: 1.5rem; font-weight: bold;">{user_certs}</div>
                        <div style="font-size: 0.8rem;">My Certs</div>
                    </div>
                    <div>
                        <div style="font-size: 1.5rem; font-weight: bold;">{total_sys_certs}</div>
                        <div style="font-size: 0.8rem;">Total</div>
                    </div>
                </div>
                <div style="font-size: 0.8rem; margin-top: 10px; opacity: 0.9;">
                    Logged in: {st.session_state.get('login_time', 'Unknown')}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state['logged_in'] = False
            st.session_state['username'] = ""
            st.session_state['login_time'] = ""
            st.rerun()
    
    st.divider()
    
    # Navigation
    st.markdown("### 📍 Navigation")
    page = st.radio(
        "Go to",
        ["Dashboard", "Upload & Verify", "Supplier Trust", "Material Passport"],
        label_visibility="collapsed"
    )

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
        border-top: 4px solid #4F46E5;
        transition: transform 0.2s;
        margin-bottom: 15px;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }
    .metric-card.total-certs { border-top-color: #1E3A8A; }
    .metric-card.my-certs { border-top-color: #10B981; }
    .metric-card.compliance { border-top-color: #8B5CF6; }
    .metric-card.alerts { border-top-color: #EF4444; }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1F2937;
    }
    .metric-label {
        color: #6B7280;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .alert-card {
        background-color: #FEF2F2;
        border-left: 4px solid #EF4444;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    .pass-card {
        background-color: #F0FDF4;
        border-left: 4px solid #22C55E;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    .welcome-header {
        background: linear-gradient(135deg, #1E3A8A, #3B82F6);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# --- PAGE RENDERING ---
if page == "Dashboard":
    st.markdown('<div class="welcome-header"><h1>📊 Dashboard</h1></div>', unsafe_allow_html=True)
    
    # Welcome message
    user_name = st.session_state.get('username', 'User')
    user_count = database.get_user_certificate_count(user_name)
    st.markdown(f"### 👋 Welcome back, **{user_name}!**")
    st.markdown(f"You've verified **{user_count}** certificates so far.")
    st.markdown("---")
    
    stats = database.get_dashboard_stats()
    
    # Metric Cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f'''
        <div class="metric-card total-certs">
            <div class="metric-label">📄 Total Certificates</div>
            <div class="metric-value">{stats["total"]}</div>
        </div>''', unsafe_allow_html=True)
    
    with col2:
        st.markdown(f'''
        <div class="metric-card my-certs">
            <div class="metric-label">🙋 My Certificates</div>
            <div class="metric-value">{user_count}</div>
        </div>''', unsafe_allow_html=True)
    
    with col3:
        st.markdown(f'''
        <div class="metric-card compliance">
            <div class="metric-label">📈 Compliance Rate</div>
            <div class="metric-value">{stats["avg_compliance"]:.1f}%</div>
        </div>''', unsafe_allow_html=True)
    
    with col4:
        st.markdown(f'''
        <div class="metric-card alerts">
            <div class="metric-label">⚠️ Fraud Alerts</div>
            <div class="metric-value">{stats["risk_count"]}</div>
        </div>''', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Recent Activity
    st.subheader(f"🕒 Recent Activity - {user_name}")
    recent_df = database.get_user_recent_certificates(user_name, limit=5)
    
    if not recent_df.empty:
        display_cols = []
        for col in ['material_id', 'supplier_name', 'material_grade', 'compliance_score', 'status', 'upload_date']:
            if col in recent_df.columns:
                display_cols.append(col)
            elif col == 'status' and 'Status' in recent_df.columns:
                display_cols.append('Status')
            elif col == 'upload_date' and 'upload_date' in recent_df.columns:
                display_cols.append('upload_date')
        
        st.dataframe(recent_df[display_cols], use_container_width=True, hide_index=True)
    else:
        st.info("📌 No recent activity. Upload a certificate to get started!")
    
    st.markdown("---")
    
    # Charts
    col_chart1, col_chart2 = st.columns(2)
    
    df_certs = stats["certs_df"]
    if not df_certs.empty and 'status' in df_certs.columns:
        with col_chart1:
            st.subheader("📊 Compliance Status")
            status_counts = df_certs['status'].value_counts().reset_index()
            status_counts.columns = ['status', 'count']
            fig1 = px.pie(status_counts, values='count', names='status', 
                          color='status', color_discrete_map={'Pass':'#10B981', 'Fail':'#EF4444'},
                          hole=0.4)
            fig1.update_layout(showlegend=True)
            st.plotly_chart(fig1, use_container_width=True)
        
        with col_chart2:
            st.subheader("📈 Average Compliance")
            fig2 = go.Figure(go.Indicator(
                mode="gauge+number",
                value=stats["avg_compliance"],
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Overall Compliance %"},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "#10B981" if stats["avg_compliance"] > 80 else "#3B82F6"},
                    'steps': [
                        {'range': [0, 50], 'color': "#FEE2E2"},
                        {'range': [50, 80], 'color': "#FEF3C7"},
                        {'range': [80, 100], 'color': "#D1FAE5"}
                    ]
                }
            ))
            fig2.update_layout(height=300)
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("📊 No system-wide data available yet.")

elif page == "Upload & Verify":
    st.title("📤 Upload & Verify MTC")
    st.markdown("Upload a Material Test Certificate (PDF or Image) to automatically extract, validate, and check for fraud.")
    
    uploaded_file = st.file_uploader("Choose a file", type=['pdf', 'png', 'jpg', 'jpeg'])
    
    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
        file_hash = hashlib.sha256(file_bytes).hexdigest()
        file_type = 'pdf' if uploaded_file.name.endswith('.pdf') else 'image'
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("📄 Document Preview")
            if file_type == 'image':
                st.image(uploaded_file, use_container_width=True)
            else:
                st.info(f"📑 PDF uploaded: **{uploaded_file.name}** ({len(file_bytes)/1024:.1f} KB)")
            
            if st.button("🔍 Verify Certificate", type="primary", use_container_width=True):
                
                # Check for duplicate
                existing = database.get_certificate_by_hash(file_hash)
                if existing:
                    st.warning(f"⚠️ This document was already verified as **{existing['material_id']}**")
                
                # Process
                with st.spinner("1️⃣ Extracting data with AI..."):
                    extracted = extractor.extract_mtc_data(file_bytes, file_type)
                
                if "error" in extracted and "fallback" not in extracted:
                    st.error(f"Extraction failed: {extracted['error']}")
                else:
                    if "fallback" in extracted:
                        st.warning("⚠️ Using fallback mode (Gemini API unavailable)")
                        extracted = extracted["fallback"]
                    
                    with st.spinner("2️⃣ Validating against ASTM standards..."):
                        validation = validator.validate_mtc_data(extracted)
                    
                    with st.spinner("3️⃣ Checking for fraud..."):
                        fraud = fraud_detector.analyze_for_fraud(extracted)
                    
                    # Results
                    is_pass = validation["is_compliant"] and not fraud["is_fraud_risk"]
                    status = "Pass" if is_pass else "Fail"
                    
                    material_id = f"MTC-{uuid.uuid4().hex[:8].upper()}"
                    
                    # 🔴 DEBUG: Show extracted data
                    st.info("🔍 EXTRACTED DATA FROM GEMINI:")
                    st.json(extracted)
                    
                    record = {
                        "material_id": material_id,
                        "supplier_name": extracted.get("supplier_name", "Unknown"),
                        "material_grade": extracted.get("material_grade", "Unknown"),
                        "heat_number": extracted.get("heat_number", "Unknown"),
                        "yield_strength": extracted.get("yield_strength", 0),
                        "tensile_strength": extracted.get("tensile_strength", 0),
                        "compliance_score": validation["valid_score"],
                        "status": status,
                        "is_fraud_risk": fraud["is_fraud_risk"],
                        "risk_alerts": "; ".join(fraud["alerts"]),
                        "file_hash": file_hash,
                        "verified_by": st.session_state.get('username', 'Unknown')  # Current user
                    }
                    
                    # 🔴 DEBUG: Show what's being saved
                    st.info(f"🔍 SAVING TO DATABASE - Supplier: '{record['supplier_name']}'")
                    
                    # ✅ SAVE TO DATABASE
                    database.add_certificate(record)
                    
                    # Store in session for display
                    st.session_state['last_result'] = {
                        "extracted": extracted,
                        "validation": validation,
                        "fraud": fraud,
                        "record": record
                    }
                    st.success("✅ Verification complete! Certificate saved.")
                    st.rerun()
        
        with col2:
            if 'last_result' in st.session_state:
                res = st.session_state['last_result']
                
                st.subheader("📋 Verification Results")
                
                # Status
                status_color = "#10B981" if res['record']['status'] == "Pass" else "#EF4444"
                st.markdown(f"<h2 style='text-align: center; color: {status_color};'>{res['record']['status']}</h2>", unsafe_allow_html=True)
                
                # Key info
                st.markdown(f"**Material ID:** `{res['record']['material_id']}`")
                st.markdown(f"**Compliance Score:** **{res['record']['compliance_score']:.1f}%**")
                st.markdown(f"**Supplier:** {res['record']['supplier_name']}")
                st.markdown(f"**Grade:** {res['record']['material_grade']}")
                st.markdown(f"**Heat Number:** {res['record']['heat_number']}")
                
                # Reasoning
                with st.expander("🔍 Compliance Reasoning", expanded=True):
                    for reason in res['validation']['reasoning']:
                        if "✅" in reason:
                            st.markdown(f'<div class="pass-card">{reason}</div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div class="alert-card">{reason}</div>', unsafe_allow_html=True)
                
                # Fraud alerts
                if res['fraud']['alerts']:
                    with st.expander("🚨 Fraud Alerts", expanded=True):
                        for alert in res['fraud']['alerts']:
                            st.markdown(f'<div class="alert-card">⚠️ {alert}</div>', unsafe_allow_html=True)
                
                # DOWNLOAD REPORT
                st.markdown("---")
                st.subheader("📥 Download Report")
                
                if st.button("📥 Generate PDF Report", use_container_width=True):
                    with st.spinner("Creating PDF report..."):
                        try:
                            # Generate PDF
                            pdf_path = report_generator.generate_pdf_report(
                                res['record'],
                                res['fraud'],
                                res['validation']
                            )
                            
                            # Check if file exists
                            if os.path.exists(pdf_path):
                                # Read file as bytes
                                with open(pdf_path, "rb") as f:
                                    pdf_bytes = f.read()
                                
                                # Get filename
                                file_name = os.path.basename(pdf_path)
                                
                                # Show download button
                                st.download_button(
                                    "📄 Click Here to Download PDF",
                                    pdf_bytes,
                                    file_name=file_name,
                                    mime="application/octet-stream",
                                    key=f"download_{res['record']['material_id']}"
                                )
                            else:
                                st.error("Could not create PDF file. Using text fallback.")
                                # Fallback text report
                                report_text = f"""
MTC VERIFICATION REPORT
{'='*50}
Material ID: {res['record']['material_id']}
Status: {res['record']['status']}
Compliance Score: {res['record']['compliance_score']:.1f}%
Supplier: {res['record']['supplier_name']}
Material Grade: {res['record']['material_grade']}
Heat Number: {res['record']['heat_number']}
Verified By: {res['record']['verified_by']}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}

VALIDATION RESULTS:
{chr(10).join(res['validation']['reasoning'])}

FRAUD ALERTS:
{chr(10).join(res['fraud']['alerts']) if res['fraud']['alerts'] else 'No fraud detected'}
"""
                                st.download_button(
                                    "📄 Download Text Report",
                                    report_text,
                                    file_name=f"report_{res['record']['material_id']}.txt",
                                    mime="text/plain"
                                )
                                
                        except Exception as e:
                            st.error(f"Error generating report: {str(e)}")
                            # Simple text fallback
                            simple_text = f"Material ID: {res['record']['material_id']}\nStatus: {res['record']['status']}\nScore: {res['record']['compliance_score']}%"
                            st.download_button(
                                "📄 Download Simple Report",
                                simple_text,
                                file_name=f"report_{res['record']['material_id']}.txt"
                            )

elif page == "Supplier Trust":
    st.title("🏭 Supplier Trust Scores")
    
    suppliers_df = database.get_all_suppliers()
    
    if not suppliers_df.empty:
        def color_risk(val):
            if val >= 80:
                return "background-color: #10B981; color: white"
            elif val >= 50:
                return "background-color: #F59E0B; color: white"
            else:
                return "background-color: #EF4444; color: white"
        
        if 'trust_score' in suppliers_df.columns:
            styled_df = suppliers_df.style.map(color_risk, subset=['trust_score'])
            st.dataframe(styled_df, use_container_width=True)
        else:
            st.dataframe(suppliers_df, use_container_width=True)
        
        if 'name' in suppliers_df.columns and 'trust_score' in suppliers_df.columns:
            fig = px.bar(suppliers_df, x='name', y='trust_score',
                         color='trust_score',
                         color_continuous_scale=['#EF4444', '#F59E0B', '#10B981'],
                         title="Supplier Trust Scores")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No supplier data available yet.")

elif page == "Material Passport":
    st.title("📘 Digital Material Passport")
    st.markdown("Traceability view for all verified and passed materials.")
    
    certs_df = database.get_all_certificates()
    
    if not certs_df.empty:
        status_col = 'status' if 'status' in certs_df.columns else 'Status'
        if status_col in certs_df.columns:
            passed_df = certs_df[certs_df[status_col] == 'Pass']
            
            if not passed_df.empty:
                display_cols = []
                for col in ['material_id', 'supplier_name', 'material_grade', 'compliance_score', status_col, 'upload_date']:
                    if col in passed_df.columns:
                        display_cols.append(col)
                
                st.dataframe(passed_df[display_cols], use_container_width=True, hide_index=True)
                
                if 'material_id' in passed_df.columns:
                    selected = st.selectbox("Select Material ID to view full passport", 
                                           passed_df['material_id'].tolist())
                    
                    if selected:
                        cert = passed_df[passed_df['material_id'] == selected].iloc[0]
                        
                        st.markdown("---")
                        st.subheader(f"📋 Passport: {selected}")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**Material Grade:** {cert.get('material_grade', 'N/A')}")
                            st.markdown(f"**Supplier:** {cert.get('supplier_name', 'N/A')}")
                            st.markdown(f"**Heat Number:** {cert.get('heat_number', 'N/A')}")
                        with col2:
                            st.markdown(f"**Compliance Score:** {cert.get('compliance_score', 0):.1f}%")
                            st.markdown(f"**Verified:** {cert.get('upload_date', 'N/A')}")
                            st.markdown(f"**Status:** ✅ PASS")
            else:
                st.info("No passed certificates found.")
        else:
            st.info("Certificate data format issue.")
    else:
        st.info("No certificates in database yet.")