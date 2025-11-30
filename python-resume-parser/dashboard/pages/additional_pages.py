"""
Additional dashboard pages (Job Description, Candidate List, Resume Viewer, Analytics)
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Optional

def show_upload_job_description():
    """Job description upload and management page"""
    
    st.header("📝 Job Description Management")
    st.markdown("Upload and manage job descriptions for consistent resume scoring.")
    
    # Upload new job description
    st.subheader("📤 Upload New Job Description")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        job_title = st.text_input("Job Title", placeholder="Software Engineer")
    with col2:
        company = st.text_input("Company Name", placeholder="Tech Corp")
    
    job_description = st.text_area(
        "Job Description",
        height=300,
        placeholder="Paste the complete job description here...",
        help="Include requirements, responsibilities, qualifications, and desired skills"
    )
    
    if st.button("💾 Save Job Description", type="primary"):
        if len(job_description) < 50:
            st.error("Job description must be at least 50 characters long")
        else:
            save_job_description(job_title, company, job_description)
    
    st.markdown("---")
    
    # List existing job descriptions
    st.subheader("📚 Saved Job Descriptions")
    show_saved_job_descriptions()

def save_job_description(title: str, company: str, description: str):
    """Save job description to backend"""
    
    try:
        response = requests.post(
            f"{st.session_state.get('api_base_url', 'http://localhost:8000')}/api/v1/upload_jd",
            params={
                "job_description": description,
                "title": title or "Untitled Position",
                "company": company
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            st.success(f"✅ Job description '{title}' saved successfully!")
            st.rerun()  # Refresh to show in the list
        else:
            st.error(f"❌ Failed to save job description: {response.text}")
            
    except Exception as e:
        st.error(f"❌ Error saving job description: {str(e)}")

def show_saved_job_descriptions():
    """Display saved job descriptions"""
    
    try:
        response = requests.get(
            f"{st.session_state.get('api_base_url', 'http://localhost:8000')}/api/v1/job-descriptions"
        )
        
        if response.status_code == 200:
            job_descriptions = response.json()
            
            if job_descriptions:
                for jd in job_descriptions:
                    with st.expander(f"{jd['title']} - {jd.get('company', 'Unknown Company')}"):
                        st.write(f"**Created:** {jd['created_at']}")
                        st.write(f"**ID:** {jd['id']}")
                        
                        if st.button(f"Use for Scoring", key=f"use_{jd['id']}"):
                            st.session_state['selected_job_description'] = jd
                            st.session_state['page'] = "📊 ATS Scoring"
                            st.rerun()
            else:
                st.info("No saved job descriptions yet")
                
    except Exception as e:
        st.error(f"Error loading job descriptions: {str(e)}")

def show_candidate_list():
    """Candidate management and overview page"""
    
    st.header("👤 Candidate List")
    st.markdown("Manage and compare candidates across different positions.")
    
    # Get all resumes
    try:
        response = requests.get(
            f"{st.session_state.get('api_base_url', 'http://localhost:8000')}/api/v1/resumes?page_size=100"
        )
        
        if response.status_code == 200:
            data = response.json()
            resumes = data.get('resumes', [])
            
            if not resumes:
                st.info("No candidates found. Upload some resumes to get started!")
                return
            
            # Search and filter
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                search_term = st.text_input("🔍 Search candidates", placeholder="Name, email, or filename...")
            
            with col2:
                sort_by = st.selectbox("Sort by", ["Created Date", "Name", "Email"])
            
            with col3:
                sort_order = st.selectbox("Order", ["Descending", "Ascending"])
            
            # Filter resumes
            if search_term:
                filtered_resumes = [
                    r for r in resumes 
                    if search_term.lower() in (r.get('name', '') + r.get('email', '') + r.get('filename', '')).lower()
                ]
            else:
                filtered_resumes = resumes
            
            # Sort resumes
            if sort_by == "Name":
                filtered_resumes.sort(key=lambda x: x.get('name', ''), reverse=(sort_order == "Descending"))
            elif sort_by == "Email":
                filtered_resumes.sort(key=lambda x: x.get('email', ''), reverse=(sort_order == "Descending"))
            else:  # Created Date
                filtered_resumes.sort(key=lambda x: x.get('created_at', ''), reverse=(sort_order == "Descending"))
            
            # Display candidates
            st.subheader(f"📋 Candidates ({len(filtered_resumes)} found)")
            
            for resume in filtered_resumes:
                with st.container():
                    col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 1, 1])
                    
                    with col1:
                        name = resume.get('name', 'Unknown')
                        st.write(f"**{name}**")
                        st.caption(f"📄 {resume['filename']}")
                    
                    with col2:
                        email = resume.get('email', 'N/A')
                        phone = resume.get('phone', 'N/A')
                        st.write(f"📧 {email}")
                        st.caption(f"📞 {phone}")
                    
                    with col3:
                        created_date = resume.get('created_at', '').split('T')[0]
                        st.write(f"📅 {created_date}")
                    
                    with col4:
                        if st.button("👁️ View", key=f"view_{resume['id']}"):
                            st.session_state['current_resume_id'] = resume['id']
                            st.session_state['page'] = "🔍 Resume Viewer"
                            st.rerun()
                    
                    with col5:
                        if st.button("📊 Score", key=f"score_{resume['id']}"):
                            st.session_state['current_resume_id'] = resume['id']
                            st.session_state['page'] = "📊 ATS Scoring"
                            st.rerun()
                    
                    st.markdown("---")
                    
        else:
            st.error("Failed to load candidates")
            
    except Exception as e:
        st.error(f"Error loading candidates: {str(e)}")

def show_resume_viewer():
    """Detailed resume viewer page"""
    
    st.header("🔍 Resume Viewer")
    
    # Get resume ID from session state or let user select
    current_resume_id = st.session_state.get('current_resume_id')
    
    if not current_resume_id:
        # Let user select
        try:
            response = requests.get(
                f"{st.session_state.get('api_base_url', 'http://localhost:8000')}/api/v1/resumes?page_size=50"
            )
            
            if response.status_code == 200:
                data = response.json()
                resumes = data.get('resumes', [])
                
                if not resumes:
                    st.warning("No resumes available")
                    return
                
                resume_options = {
                    f"{r.get('name', 'Unknown')} ({r['filename']})": r['id']
                    for r in resumes
                }
                
                selected_display = st.selectbox("Select Resume to View", list(resume_options.keys()))
                current_resume_id = resume_options[selected_display]
            
        except Exception as e:
            st.error(f"Error loading resumes: {str(e)}")
            return
    
    # Load full resume data
    try:
        response = requests.get(
            f"{st.session_state.get('api_base_url', 'http://localhost:8000')}/api/v1/resumes/{current_resume_id}"
        )
        
        if response.status_code == 200:
            resume_data = response.json()
            display_full_resume(resume_data)
        else:
            st.error(f"Failed to load resume: {response.text}")
            
    except Exception as e:
        st.error(f"Error loading resume: {str(e)}")

def display_full_resume(resume_data: Dict):
    """Display complete resume information"""
    
    st.subheader(f"📄 {resume_data['filename']}")
    
    # Quick actions
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Score Resume"):
            st.session_state['current_resume_id'] = resume_data['id']
            st.session_state['page'] = "📊 ATS Scoring"
            st.rerun()
    
    with col2:
        if st.button("💡 Get Suggestions"):
            st.session_state['current_resume_id'] = resume_data['id']
            st.session_state['page'] = "💡 Suggestions"
            st.rerun()
    
    with col3:
        if st.button("🔄 Reparse Resume"):
            reparse_resume(resume_data['id'])
    
    # Display resume sections (reuse the display function from upload_resume.py)
    from pages.upload_resume import display_parsed_resume
    display_parsed_resume(resume_data)

def reparse_resume(resume_id: str):
    """Reparse an existing resume"""
    
    with st.spinner("Reparsing resume..."):
        try:
            response = requests.post(
                f"{st.session_state.get('api_base_url', 'http://localhost:8000')}/api/v1/resumes/{resume_id}/reparse"
            )
            
            if response.status_code == 200:
                st.success("✅ Resume reparsed successfully!")
                st.rerun()
            else:
                st.error(f"❌ Failed to reparse: {response.text}")
                
        except Exception as e:
            st.error(f"❌ Error reparsing: {str(e)}")

def show_analytics():
    """Analytics and insights page"""
    
    st.header("📈 Analytics & Insights")
    st.markdown("Deep insights into your recruitment pipeline and resume trends.")
    
    # Get dashboard data
    dashboard_data = requests.get(
        f"{st.session_state.get('api_base_url', 'http://localhost:8000')}/api/v1/dashboard-data"
    ).json()
    
    # Get additional analytics
    skills_analysis = requests.get(
        f"{st.session_state.get('api_base_url', 'http://localhost:8000')}/api/v1/analytics/skills-analysis"
    ).json()
    
    # Key metrics overview
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Resumes", dashboard_data.get('total_resumes', 0))
    
    with col2:
        st.metric("Avg Score", f"{dashboard_data.get('average_score', 0):.1%}")
    
    with col3:
        st.metric("Unique Technical Skills", skills_analysis.get('total_unique_technical_skills', 0))
    
    with col4:
        st.metric("Unique Soft Skills", skills_analysis.get('total_unique_soft_skills', 0))
    
    # Skills analysis charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔧 Most Common Technical Skills")
        tech_skills = skills_analysis.get('most_common_technical_skills', [])
        
        if tech_skills:
            df_tech = pd.DataFrame(tech_skills)
            fig = px.bar(
                df_tech.head(10),
                x='count',
                y='skill',
                orientation='h',
                title="Top Technical Skills"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("💼 Most Common Soft Skills")
        soft_skills = skills_analysis.get('most_common_soft_skills', [])
        
        if soft_skills:
            df_soft = pd.DataFrame(soft_skills)
            fig = px.bar(
                df_soft.head(10),
                x='count',
                y='skill',
                orientation='h',
                title="Top Soft Skills"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Score distribution
    st.subheader("📊 Score Distribution Analysis")
    
    score_dist = dashboard_data.get('score_distribution', {})
    if score_dist:
        # Create more detailed visualization
        df_scores = pd.DataFrame([
            {'Range': k, 'Count': v} for k, v in score_dist.items()
        ])
        
        fig = px.histogram(
            df_scores,
            x='Range',
            y='Count',
            title="ATS Score Distribution",
            color='Range'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Score insights
        total_scored = sum(score_dist.values())
        if total_scored > 0:
            high_scores = score_dist.get('0.8-1.0', 0) + score_dist.get('0.6-0.8', 0)
            high_score_pct = (high_scores / total_scored) * 100
            
            if high_score_pct >= 60:
                st.success(f"🎉 Great! {high_score_pct:.1f}% of resumes score well (>60%)")
            elif high_score_pct >= 40:
                st.warning(f"⚠️ {high_score_pct:.1f}% of resumes score well. Room for improvement.")
            else:
                st.error(f"❌ Only {high_score_pct:.1f}% of resumes score well. Consider coaching candidates.")
    
    # Missing skills analysis
    st.subheader("🔍 Skills Gap Analysis")
    
    missing_skills = dashboard_data.get('common_missing_skills', [])
    if missing_skills:
        df_missing = pd.DataFrame(missing_skills)
        
        fig = px.treemap(
            df_missing.head(15),
            values='frequency',
            names='skill',
            title="Most Common Missing Skills"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Insights
        top_missing = missing_skills[0]['skill'] if missing_skills else "N/A"
        st.info(f"💡 **Insight:** '{top_missing}' is the most commonly missing skill. Consider creating targeted training or sourcing.")
    
    # Export functionality
    st.subheader("📥 Export Data")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Export Skills Report"):
            st.download_button(
                "Download Skills Report",
                data=pd.DataFrame(skills_analysis.get('most_common_technical_skills', [])).to_csv(),
                file_name="skills_report.csv",
                mime="text/csv"
            )
    
    with col2:
        if st.button("Export Score Analysis"):
            st.download_button(
                "Download Score Analysis",
                data=pd.DataFrame(dashboard_data.get('score_distribution', {})).to_csv(),
                file_name="score_analysis.csv", 
                mime="text/csv"
            )
    
    with col3:
        if st.button("Export Dashboard Data"):
            st.download_button(
                "Download Dashboard Data",
                data=str(dashboard_data),
                file_name="dashboard_data.json",
                mime="application/json"
            )