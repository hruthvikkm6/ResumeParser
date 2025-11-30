"""
ATS Scoring page functionality
"""

import streamlit as st
import requests
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, List, Optional

def show_ats_scoring():
    """ATS scoring page"""
    
    st.header("📊 ATS Scoring")
    st.markdown("Score resumes against job descriptions using AI-powered ATS algorithms.")
    
    # Get list of available resumes
    resumes = get_available_resumes()
    
    if not resumes:
        st.warning("No resumes available. Please upload a resume first.")
        return
    
    # Resume selection
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Create resume options
        resume_options = {
            f"{r.get('name', 'Unknown')} ({r['filename']})": r['id']
            for r in resumes
        }
        
        selected_resume_display = st.selectbox(
            "Select Resume to Score",
            options=list(resume_options.keys())
        )
        
        selected_resume_id = resume_options[selected_resume_display]
    
    with col2:
        # Scoring options
        use_sbert = st.checkbox(
            "Use SBERT (Advanced)",
            help="Use Sentence-BERT for enhanced semantic scoring"
        )
        
        custom_weights = st.checkbox(
            "Custom Weights",
            help="Customize section scoring weights"
        )
    
    # Custom weights configuration
    if custom_weights:
        st.subheader("⚖️ Scoring Weights")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            skills_weight = st.slider("Skills Weight", 0.0, 1.0, 0.4, 0.05)
        with col2:
            experience_weight = st.slider("Experience Weight", 0.0, 1.0, 0.35, 0.05)
        with col3:
            education_weight = st.slider("Education Weight", 0.0, 1.0, 0.25, 0.05)
        
        # Normalize weights
        total_weight = skills_weight + experience_weight + education_weight
        if total_weight != 1.0:
            st.warning(f"Weights sum to {total_weight:.2f}. They will be normalized to 1.0.")
            weights = {
                "skills": skills_weight / total_weight,
                "experience": experience_weight / total_weight,
                "education": education_weight / total_weight
            }
        else:
            weights = {
                "skills": skills_weight,
                "experience": experience_weight,
                "education": education_weight
            }
    else:
        weights = None
    
    # Job description input
    st.subheader("📝 Job Description")
    
    # Option to use saved JD or input new one
    use_saved_jd = st.radio(
        "Job Description Source",
        ["Enter New", "Use Saved"],
        horizontal=True
    )
    
    job_description = ""
    job_title = ""
    company = ""
    
    if use_saved_jd == "Use Saved":
        saved_jds = get_saved_job_descriptions()
        if saved_jds:
            selected_jd = st.selectbox(
                "Select Saved Job Description",
                options=saved_jds,
                format_func=lambda x: f"{x['title']} - {x.get('company', 'Unknown Company')}"
            )
            job_description = selected_jd['description']
            job_title = selected_jd['title']
            company = selected_jd.get('company', '')
        else:
            st.info("No saved job descriptions available.")
            use_saved_jd = "Enter New"
    
    if use_saved_jd == "Enter New":
        col1, col2 = st.columns([1, 1])
        with col1:
            job_title = st.text_input("Job Title", placeholder="Software Engineer")
        with col2:
            company = st.text_input("Company Name", placeholder="Tech Corp")
        
        job_description = st.text_area(
            "Job Description",
            height=200,
            placeholder="Paste the complete job description here...",
            help="Include requirements, responsibilities, and desired skills"
        )
    
    # Score button
    if st.button("🎯 Score Resume", type="primary", disabled=len(job_description) < 50):
        if len(job_description) < 50:
            st.error("Job description must be at least 50 characters long.")
        else:
            score_resume(selected_resume_id, job_description, job_title, company, use_sbert, weights)

def score_resume(resume_id: str, job_description: str, job_title: str, company: str, use_sbert: bool, weights: Optional[Dict]):
    """Score a resume against job description"""
    
    with st.spinner("Analyzing resume... This may take a moment."):
        
        # Prepare scoring request
        scoring_data = {
            "resume_id": resume_id,
            "job_description": job_description,
            "job_title": job_title or None,
            "company": company or None,
            "use_sbert": use_sbert
        }
        
        if weights:
            scoring_data["score_weights"] = weights
        
        try:
            # Make scoring request
            response = requests.post(
                f"{st.session_state.get('api_base_url', 'http://localhost:8000')}/api/v1/score_resume",
                json=scoring_data
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Display results
                display_scoring_results(result)
                
            else:
                st.error(f"❌ Scoring failed: {response.text}")
                
        except Exception as e:
            st.error(f"❌ Error during scoring: {str(e)}")

def display_scoring_results(result: Dict):
    """Display scoring results with visualizations"""
    
    st.success("✅ Scoring Complete!")
    
    # Overall Score
    overall_score = result.get('overall_score', 0)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Overall ATS Score",
            f"{overall_score:.1%}",
            delta=None
        )
    
    with col2:
        keyword_density = result.get('keyword_density', 0)
        st.metric(
            "Keyword Match",
            f"{keyword_density:.1%}",
            delta=None
        )
    
    with col3:
        matched_keywords = len(result.get('total_matched_keywords', []))
        st.metric(
            "Matched Keywords",
            matched_keywords,
            delta=None
        )
    
    with col4:
        missing_keywords = len(result.get('total_missing_keywords', []))
        st.metric(
            "Missing Keywords",
            missing_keywords,
            delta=None
        )
    
    # Score interpretation
    if overall_score >= 0.8:
        st.success("🎉 Excellent match! This resume is highly compatible with the job requirements.")
    elif overall_score >= 0.6:
        st.warning("👍 Good match! Some improvements could increase compatibility.")
    elif overall_score >= 0.4:
        st.warning("⚠️ Moderate match. Consider significant improvements.")
    else:
        st.error("❌ Poor match. Major revisions needed for better ATS compatibility.")
    
    # Section Scores Visualization
    st.subheader("📊 Section Breakdown")
    
    section_scores = result.get('section_scores', [])
    if section_scores:
        # Create radar chart for section scores
        fig = create_section_scores_chart(section_scores)
        st.plotly_chart(fig, use_container_width=True)
        
        # Section details table
        df_sections = pd.DataFrame([
            {
                'Section': section['section'].title(),
                'Score': f"{section['score']:.1%}",
                'Weight': f"{section['weight']:.1%}",
                'Matched Keywords': len(section.get('matched_keywords', [])),
                'Missing Keywords': len(section.get('missing_keywords', []))
            }
            for section in section_scores
        ])
        
        st.dataframe(df_sections, use_container_width=True)
    
    # Keywords Analysis
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("✅ Matched Keywords")
        matched = result.get('total_matched_keywords', [])
        if matched:
            # Display as tags
            matched_text = " • ".join(matched[:20])  # Show first 20
            st.success(matched_text)
            if len(matched) > 20:
                st.info(f"... and {len(matched) - 20} more")
        else:
            st.info("No matched keywords found")
    
    with col2:
        st.subheader("❌ Missing Keywords")
        missing = result.get('total_missing_keywords', [])
        if missing:
            missing_text = " • ".join(missing[:20])  # Show first 20
            st.error(missing_text)
            if len(missing) > 20:
                st.info(f"... and {len(missing) - 20} more")
        else:
            st.info("No missing keywords")
    
    # Action buttons
    st.subheader("🚀 Next Steps")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💡 Get Improvement Suggestions"):
            st.session_state['current_resume_id'] = result['resume_id']
            st.session_state['current_job_description'] = result.get('job_description', '')
            st.session_state['page'] = "💡 Suggestions"
            st.rerun()
    
    with col2:
        if st.button("📄 View Full Resume"):
            st.session_state['current_resume_id'] = result['resume_id']
            st.session_state['page'] = "🔍 Resume Viewer"
            st.rerun()
    
    with col3:
        if st.button("📊 Score Another Resume"):
            st.rerun()

def create_section_scores_chart(section_scores: List[Dict]):
    """Create radar chart for section scores"""
    
    sections = [s['section'].title() for s in section_scores]
    scores = [s['score'] for s in section_scores]
    weights = [s['weight'] for s in section_scores]
    
    fig = go.Figure()
    
    # Add score trace
    fig.add_trace(go.Scatterpolar(
        r=scores,
        theta=sections,
        fill='toself',
        name='Actual Score',
        line_color='blue'
    ))
    
    # Add perfect score reference
    fig.add_trace(go.Scatterpolar(
        r=[1.0] * len(sections),
        theta=sections,
        fill=None,
        name='Perfect Score',
        line=dict(color='gray', dash='dash'),
        showlegend=True
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1],
                tickformat='.0%'
            )),
        showlegend=True,
        title="Section Scores Radar Chart",
        height=500
    )
    
    return fig

def get_available_resumes() -> List[Dict]:
    """Get list of available resumes"""
    
    try:
        response = requests.get(
            f"{st.session_state.get('api_base_url', 'http://localhost:8000')}/api/v1/resumes?page_size=50"
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get('resumes', [])
        else:
            return []
            
    except Exception:
        return []

def get_saved_job_descriptions() -> List[Dict]:
    """Get saved job descriptions"""
    
    try:
        response = requests.get(
            f"{st.session_state.get('api_base_url', 'http://localhost:8000')}/api/v1/job-descriptions"
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return []
            
    except Exception:
        return []