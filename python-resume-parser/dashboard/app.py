"""
Streamlit Dashboard for Resume Parser & ATS Scoring System
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import os
from datetime import datetime
from typing import Dict, List, Optional

# Configure page
st.set_page_config(
    page_title="Resume Parser & ATS Dashboard",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration
API_BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .score-excellent { color: #28a745; font-weight: bold; }
    .score-good { color: #ffc107; font-weight: bold; }
    .score-poor { color: #dc3545; font-weight: bold; }
    .sidebar-header {
        font-size: 1.5rem;
        color: #333;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

def make_api_request(endpoint: str, method: str = "GET", data: Dict = None, files: Dict = None) -> Optional[Dict]:
    """Make API request to backend"""
    try:
        url = f"{API_BASE_URL}/api/v1{endpoint}"
        
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            if files:
                response = requests.post(url, data=data, files=files)
            else:
                response = requests.post(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url)
        else:
            return None
            
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        st.error(f"Connection Error: {str(e)}")
        return None

def format_score(score: float) -> str:
    """Format and color score based on value"""
    if score >= 0.7:
        return f'<span class="score-excellent">{score:.1%}</span>'
    elif score >= 0.4:
        return f'<span class="score-good">{score:.1%}</span>'
    else:
        return f'<span class="score-poor">{score:.1%}</span>'

def main():
    """Main dashboard application"""
    
    # Initialize API base URL
    if 'api_base_url' not in st.session_state:
        st.session_state['api_base_url'] = API_BASE_URL
    
    # Header
    st.markdown('<h1 class="main-header">📄 Resume Parser & ATS Dashboard</h1>', unsafe_allow_html=True)
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown('<div class="sidebar-header">🧭 Navigation</div>', unsafe_allow_html=True)
        
        # Check for page in session state (for navigation from other pages)
        default_page = st.session_state.get('page', "🏠 Dashboard Overview")
        
        page = st.selectbox(
            "Select Page",
            [
                "🏠 Dashboard Overview",
                "📤 Upload Resume", 
                "📝 Upload Job Description",
                "👤 Candidate List",
                "🔍 Resume Viewer",
                "📊 ATS Scoring",
                "💡 Suggestions",
                "📈 Analytics"
            ],
            index=0 if default_page not in [
                "🏠 Dashboard Overview", "📤 Upload Resume", "📝 Upload Job Description",
                "👤 Candidate List", "🔍 Resume Viewer", "📊 ATS Scoring", 
                "💡 Suggestions", "📈 Analytics"
            ] else [
                "🏠 Dashboard Overview", "📤 Upload Resume", "📝 Upload Job Description",
                "👤 Candidate List", "🔍 Resume Viewer", "📊 ATS Scoring", 
                "💡 Suggestions", "📈 Analytics"
            ].index(default_page)
        )
        
        # Update session state
        st.session_state['page'] = page
        
        st.markdown("---")
        
        # API Health Check
        health_check = make_api_request("/health")
        if health_check:
            st.success("✅ Backend Connected")
            if health_check.get('version'):
                st.caption(f"API Version: {health_check['version']}")
        else:
            st.error("❌ Backend Disconnected")
            st.caption(f"Trying to connect to: {API_BASE_URL}")
    
    # Import page functions
    from pages.upload_resume import show_upload_resume
    from pages.scoring import show_ats_scoring  
    from pages.suggestions import show_suggestions
    from pages.additional_pages import (
        show_upload_job_description, 
        show_candidate_list, 
        show_resume_viewer, 
        show_analytics
    )
    
    # Route to appropriate page
    if page == "🏠 Dashboard Overview":
        show_dashboard_overview()
    elif page == "📤 Upload Resume":
        show_upload_resume()
    elif page == "📝 Upload Job Description":
        show_upload_job_description()
    elif page == "👤 Candidate List":
        show_candidate_list()
    elif page == "🔍 Resume Viewer":
        show_resume_viewer()
    elif page == "📊 ATS Scoring":
        show_ats_scoring()
    elif page == "💡 Suggestions":
        show_suggestions()
    elif page == "📈 Analytics":
        show_analytics()

def show_dashboard_overview():
    """Dashboard overview page"""
    
    st.header("📊 Dashboard Overview")
    
    # Get dashboard data
    dashboard_data = make_api_request("/dashboard-data")
    
    if not dashboard_data:
        st.error("Unable to load dashboard data")
        return
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Resumes",
            value=dashboard_data.get("total_resumes", 0),
            delta=None
        )
    
    with col2:
        avg_score = dashboard_data.get("average_score", 0.0)
        st.metric(
            label="Average ATS Score",
            value=f"{avg_score:.1%}",
            delta=None
        )
    
    with col3:
        recent_activity = dashboard_data.get("recent_activity", [])
        st.metric(
            label="Recent Scores",
            value=len(recent_activity),
            delta=None
        )
    
    with col4:
        top_resumes = dashboard_data.get("top_performing_resumes", [])
        best_score = max([r.get("score", 0) for r in top_resumes], default=0)
        st.metric(
            label="Best Score",
            value=f"{best_score:.1%}",
            delta=None
        )
    
    # Score Distribution Chart
    st.subheader("📈 Score Distribution")
    
    score_dist = dashboard_data.get("score_distribution", {})
    if score_dist:
        fig = px.bar(
            x=list(score_dist.keys()),
            y=list(score_dist.values()),
            labels={"x": "Score Range", "y": "Number of Resumes"},
            title="ATS Score Distribution"
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    # Two columns for additional info
    col1, col2 = st.columns(2)
    
    with col1:
        # Top Missing Skills
        st.subheader("🔍 Most Common Missing Skills")
        missing_skills = dashboard_data.get("common_missing_skills", [])
        
        if missing_skills:
            df_skills = pd.DataFrame(missing_skills)
            fig = px.bar(
                df_skills.head(10),
                x="frequency",
                y="skill",
                orientation="h",
                title="Top Missing Skills"
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No missing skills data available")
    
    with col2:
        # Top Performing Resumes
        st.subheader("🏆 Top Performing Resumes")
        
        if top_resumes:
            for i, resume in enumerate(top_resumes[:5], 1):
                score = resume.get("score", 0)
                name = resume.get("name", "Unknown")
                filename = resume.get("filename", "")
                
                with st.container():
                    st.markdown(f"""
                    **{i}. {name}**  
                    📄 {filename}  
                    🎯 Score: {format_score(score)}
                    """, unsafe_allow_html=True)
                    st.markdown("---")
        else:
            st.info("No scored resumes available")
    
    # Recent Activity
    st.subheader("🕒 Recent Activity")
    
    if recent_activity:
        df_activity = pd.DataFrame(recent_activity)
        df_activity["timestamp"] = pd.to_datetime(df_activity["timestamp"])
        df_activity = df_activity.sort_values("timestamp", ascending=False)
        
        st.dataframe(
            df_activity[["name", "filename", "score", "timestamp"]].head(10),
            use_container_width=True
        )
    else:
        st.info("No recent activity")

if __name__ == "__main__":
    main()