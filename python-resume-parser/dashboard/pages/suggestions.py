"""
Resume improvement suggestions page
"""

import streamlit as st
import requests
import plotly.express as px
from typing import Dict, List

def show_suggestions():
    """Resume suggestions page"""
    
    st.header("💡 Resume Improvement Suggestions")
    st.markdown("Get AI-powered suggestions to improve your resume's ATS compatibility.")
    
    # Get current resume ID from session state or let user select
    current_resume_id = st.session_state.get('current_resume_id')
    
    if not current_resume_id:
        # Let user select a resume
        resumes = get_available_resumes()
        if not resumes:
            st.warning("No resumes available. Please upload a resume first.")
            return
        
        resume_options = {
            f"{r.get('name', 'Unknown')} ({r['filename']})": r['id']
            for r in resumes
        }
        
        selected_resume_display = st.selectbox(
            "Select Resume for Suggestions",
            options=list(resume_options.keys())
        )
        
        current_resume_id = resume_options[selected_resume_display]
    
    # Job description input
    st.subheader("📝 Job Description")
    
    # Check if we have a job description from previous scoring
    current_jd = st.session_state.get('current_job_description', '')
    
    job_description = st.text_area(
        "Job Description",
        value=current_jd,
        height=200,
        placeholder="Paste the job description here to get targeted suggestions..."
    )
    
    # Generate suggestions button
    if st.button("🧠 Generate Suggestions", type="primary", disabled=len(job_description) < 50):
        if len(job_description) < 50:
            st.error("Please provide a job description (at least 50 characters)")
        else:
            generate_suggestions(current_resume_id, job_description)

def generate_suggestions(resume_id: str, job_description: str):
    """Generate and display suggestions"""
    
    with st.spinner("Analyzing resume and generating suggestions..."):
        
        # Prepare request
        request_data = {
            "resume_id": resume_id,
            "job_description": job_description
        }
        
        try:
            response = requests.post(
                f"{st.session_state.get('api_base_url', 'http://localhost:8000')}/api/v1/suggestions",
                json=request_data
            )
            
            if response.status_code == 200:
                result = response.json()
                display_suggestions(result)
            else:
                st.error(f"❌ Failed to generate suggestions: {response.text}")
                
        except Exception as e:
            st.error(f"❌ Error generating suggestions: {str(e)}")

def display_suggestions(result: Dict):
    """Display suggestions with priorities and actionable items"""
    
    st.success("✅ Suggestions Generated!")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Suggestions",
            result.get('total_suggestions', 0)
        )
    
    with col2:
        st.metric(
            "High Priority",
            result.get('high_priority_count', 0)
        )
    
    with col3:
        st.metric(
            "Medium Priority", 
            result.get('medium_priority_count', 0)
        )
    
    with col4:
        st.metric(
            "Low Priority",
            result.get('low_priority_count', 0)
        )
    
    # Priority distribution chart
    if result.get('total_suggestions', 0) > 0:
        priority_data = {
            'Priority': ['High', 'Medium', 'Low'],
            'Count': [
                result.get('high_priority_count', 0),
                result.get('medium_priority_count', 0),
                result.get('low_priority_count', 0)
            ]
        }
        
        fig = px.pie(
            values=priority_data['Count'],
            names=priority_data['Priority'],
            title="Suggestions by Priority",
            color_discrete_map={
                'High': '#dc3545',
                'Medium': '#ffc107', 
                'Low': '#28a745'
            }
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Critical Issues
    critical_keywords = result.get('missing_critical_keywords', [])
    formatting_issues = result.get('formatting_issues', [])
    
    if critical_keywords or formatting_issues:
        st.subheader("🚨 Critical Issues")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if critical_keywords:
                st.error("**Missing Critical Keywords:**")
                for keyword in critical_keywords[:10]:
                    st.write(f"• {keyword}")
            
        with col2:
            if formatting_issues:
                st.error("**Formatting Issues:**")
                for issue in formatting_issues:
                    st.write(f"• {issue}")
    
    # Detailed Suggestions
    suggestions = result.get('suggestions', [])
    
    if suggestions:
        st.subheader("📋 Detailed Suggestions")
        
        # Group suggestions by priority
        high_priority = [s for s in suggestions if s['priority'] == 'high']
        medium_priority = [s for s in suggestions if s['priority'] == 'medium']
        low_priority = [s for s in suggestions if s['priority'] == 'low']
        
        # High Priority Suggestions
        if high_priority:
            with st.expander("🔴 High Priority Suggestions", expanded=True):
                for i, suggestion in enumerate(high_priority, 1):
                    display_suggestion_card(suggestion, i, "🔴")
        
        # Medium Priority Suggestions  
        if medium_priority:
            with st.expander("🟡 Medium Priority Suggestions", expanded=True):
                for i, suggestion in enumerate(medium_priority, 1):
                    display_suggestion_card(suggestion, i, "🟡")
        
        # Low Priority Suggestions
        if low_priority:
            with st.expander("🟢 Low Priority Suggestions", expanded=False):
                for i, suggestion in enumerate(low_priority, 1):
                    display_suggestion_card(suggestion, i, "🟢")
    
    # Action Plan
    st.subheader("📋 Action Plan")
    
    action_plan_text = generate_action_plan(suggestions)
    st.markdown(action_plan_text)
    
    # Download suggestions
    if st.button("📥 Download Suggestions Report"):
        report = generate_suggestions_report(result)
        st.download_button(
            label="Download Report",
            data=report,
            file_name=f"resume_suggestions_{result['resume_id'][:8]}.md",
            mime="text/markdown"
        )

def display_suggestion_card(suggestion: Dict, index: int, icon: str):
    """Display individual suggestion card"""
    
    with st.container():
        st.markdown(f"""
        {icon} **{index}. {suggestion['title']}**
        
        **Type:** {suggestion['type'].title()}
        
        **Description:** {suggestion['description']}
        """)
        
        # Keywords to add
        keywords = suggestion.get('keywords_to_add', [])
        if keywords:
            st.info(f"**Keywords to add:** {', '.join(keywords[:5])}")
        
        st.markdown("---")

def generate_action_plan(suggestions: List[Dict]) -> str:
    """Generate prioritized action plan"""
    
    if not suggestions:
        return "No specific actions needed at this time."
    
    plan = """
    ## 🎯 Recommended Action Plan
    
    Follow these steps in order for maximum impact:
    
    ### Phase 1: Critical Fixes (Do First)
    """
    
    high_priority = [s for s in suggestions if s['priority'] == 'high']
    for i, suggestion in enumerate(high_priority[:3], 1):
        plan += f"\n{i}. **{suggestion['title']}** - {suggestion['description'][:100]}..."
    
    plan += """
    
    ### Phase 2: Important Improvements (Do Next)
    """
    
    medium_priority = [s for s in suggestions if s['priority'] == 'medium']
    for i, suggestion in enumerate(medium_priority[:3], 1):
        plan += f"\n{i}. **{suggestion['title']}** - {suggestion['description'][:100]}..."
    
    plan += """
    
    ### Phase 3: Nice-to-Have Enhancements (Time Permitting)
    """
    
    low_priority = [s for s in suggestions if s['priority'] == 'low']
    for i, suggestion in enumerate(low_priority[:2], 1):
        plan += f"\n{i}. **{suggestion['title']}** - {suggestion['description'][:100]}..."
    
    return plan

def generate_suggestions_report(result: Dict) -> str:
    """Generate downloadable suggestions report"""
    
    report = f"""
# Resume Improvement Suggestions Report

**Resume ID:** {result['resume_id']}
**Generated:** {result.get('created_at', 'Unknown')}

## Summary

- **Total Suggestions:** {result.get('total_suggestions', 0)}
- **High Priority:** {result.get('high_priority_count', 0)}
- **Medium Priority:** {result.get('medium_priority_count', 0)}
- **Low Priority:** {result.get('low_priority_count', 0)}

## Critical Issues

### Missing Critical Keywords
{chr(10).join(f"- {kw}" for kw in result.get('missing_critical_keywords', []))}

### Formatting Issues
{chr(10).join(f"- {issue}" for issue in result.get('formatting_issues', []))}

## Detailed Suggestions

"""
    
    suggestions = result.get('suggestions', [])
    
    for priority in ['high', 'medium', 'low']:
        priority_suggestions = [s for s in suggestions if s['priority'] == priority]
        if priority_suggestions:
            report += f"\n### {priority.title()} Priority\n\n"
            
            for i, suggestion in enumerate(priority_suggestions, 1):
                report += f"**{i}. {suggestion['title']}**\n\n"
                report += f"{suggestion['description']}\n\n"
                
                if suggestion.get('keywords_to_add'):
                    report += f"*Keywords to add: {', '.join(suggestion['keywords_to_add'])}*\n\n"
                
                report += "---\n\n"
    
    return report

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