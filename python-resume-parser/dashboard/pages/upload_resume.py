"""
Resume upload page functionality
"""

import streamlit as st
import requests
from typing import Dict, Optional
import time

def show_upload_resume():
    """Upload and parse resume page"""
    
    st.header("📤 Upload Resume")
    st.markdown("Upload a PDF resume to extract structured information using our AI-powered parser.")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a PDF resume",
        type=['pdf'],
        help="Maximum file size: 10MB"
    )
    
    if uploaded_file is not None:
        # Display file info
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("File Name", uploaded_file.name)
        with col2:
            file_size = len(uploaded_file.getvalue())
            st.metric("File Size", f"{file_size / 1024:.1f} KB")
        with col3:
            st.metric("File Type", uploaded_file.type)
        
        # Parse button
        if st.button("🚀 Parse Resume", type="primary"):
            
            with st.spinner("Parsing resume... This may take a few seconds."):
                
                # Prepare file for upload
                files = {
                    'file': (uploaded_file.name, uploaded_file.getvalue(), 'application/pdf')
                }
                
                try:
                    # Make API request
                    response = requests.post(
                        f"{st.session_state.get('api_base_url', 'http://localhost:8000')}/api/v1/parse_resume",
                        files=files
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        # Success message
                        st.success("✅ Resume parsed successfully!")
                        
                        # Store result in session state
                        st.session_state['last_parsed_resume'] = result
                        
                        # Display parsed information
                        display_parsed_resume(result)
                        
                    else:
                        st.error(f"❌ Failed to parse resume: {response.text}")
                        
                except Exception as e:
                    st.error(f"❌ Error uploading resume: {str(e)}")
    
    # Show recent uploads
    show_recent_uploads()

def display_parsed_resume(result: Dict):
    """Display parsed resume information"""
    
    st.subheader("📋 Parsed Information")
    
    # Contact Information
    with st.expander("👤 Contact Information", expanded=True):
        contact = result.get('contact_info', {})
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Name:** {contact.get('name', 'Not found')}")
            st.write(f"**Email:** {contact.get('email', 'Not found')}")
        with col2:
            st.write(f"**Phone:** {contact.get('phone', 'Not found')}")
            st.write(f"**Location:** {contact.get('location', 'Not found')}")
        
        if contact.get('linkedin'):
            st.write(f"**LinkedIn:** {contact['linkedin']}")
    
    # Skills
    with st.expander("💼 Skills", expanded=True):
        skills = result.get('skills', {})
        
        if skills.get('technical'):
            st.write("**Technical Skills:**")
            st.write(", ".join(skills['technical']))
        
        if skills.get('soft'):
            st.write("**Soft Skills:**")
            st.write(", ".join(skills['soft']))
        
        if skills.get('certifications'):
            st.write("**Certifications:**")
            st.write(", ".join(skills['certifications']))
    
    # Experience
    with st.expander("💼 Work Experience"):
        experience = result.get('experience', [])
        
        for i, exp in enumerate(experience, 1):
            st.write(f"**{i}. {exp.get('title', 'Position')} at {exp.get('company', 'Company')}**")
            if exp.get('start_date') or exp.get('end_date'):
                st.write(f"Duration: {exp.get('start_date', '')} - {exp.get('end_date', '')}")
            
            if exp.get('details'):
                for detail in exp['details'][:3]:  # Show first 3 details
                    st.write(f"• {detail}")
            st.write("---")
    
    # Education
    with st.expander("🎓 Education"):
        education = result.get('education', [])
        
        for i, edu in enumerate(education, 1):
            st.write(f"**{i}. {edu.get('degree', 'Degree')} - {edu.get('institution', 'Institution')}**")
            if edu.get('field_of_study'):
                st.write(f"Field: {edu['field_of_study']}")
            if edu.get('gpa'):
                st.write(f"GPA: {edu['gpa']}")
            if edu.get('end_date'):
                st.write(f"Graduation: {edu['end_date']}")
            st.write("---")
    
    # Projects
    projects = result.get('projects', [])
    if projects:
        with st.expander("🚀 Projects"):
            for i, project in enumerate(projects, 1):
                st.write(f"**{i}. {project.get('name', 'Project')}**")
                if project.get('description'):
                    st.write(project['description'])
                st.write("---")
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Score This Resume"):
            st.session_state['current_resume_id'] = result['id']
            st.session_state['page'] = "📊 ATS Scoring"
            st.rerun()
    
    with col2:
        if st.button("💡 Get Suggestions"):
            st.session_state['current_resume_id'] = result['id']
            st.session_state['page'] = "💡 Suggestions"
            st.rerun()
    
    with col3:
        if st.button("📄 View Raw Text"):
            with st.expander("Raw Extracted Text", expanded=True):
                st.text_area(
                    "Raw Text",
                    value=result.get('raw_text', ''),
                    height=300,
                    disabled=True
                )

def show_recent_uploads():
    """Show recent uploads"""
    
    st.subheader("📚 Recent Uploads")
    
    try:
        # Get recent resumes
        response = requests.get(
            f"{st.session_state.get('api_base_url', 'http://localhost:8000')}/api/v1/resumes?page=1&page_size=5"
        )
        
        if response.status_code == 200:
            data = response.json()
            resumes = data.get('resumes', [])
            
            if resumes:
                for resume in resumes:
                    with st.container():
                        col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                        
                        with col1:
                            st.write(f"**{resume.get('name', 'Unknown')}**")
                            st.write(f"📄 {resume['filename']}")
                        
                        with col2:
                            st.write(f"📧 {resume.get('email', 'N/A')}")
                        
                        with col3:
                            created_at = resume.get('created_at', '')
                            if created_at:
                                date = created_at.split('T')[0]
                                st.write(f"📅 {date}")
                        
                        with col4:
                            if st.button(f"View", key=f"view_{resume['id']}"):
                                st.session_state['current_resume_id'] = resume['id']
                                st.session_state['page'] = "🔍 Resume Viewer"
                                st.rerun()
                        
                        st.markdown("---")
            else:
                st.info("No resumes uploaded yet")
        else:
            st.error("Failed to load recent uploads")
            
    except Exception as e:
        st.error(f"Error loading recent uploads: {str(e)}")

# Set API base URL in session state if not set
if 'api_base_url' not in st.session_state:
    import os
    st.session_state['api_base_url'] = os.getenv("BACKEND_URL", "http://localhost:8000")