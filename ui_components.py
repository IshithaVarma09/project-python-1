import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date

def calculate_stress_level(pending_tasks_df, subjects_df):
    """
    Calculates a simple rule-based stress level based on pending tasks and unprepared exams.
    Returns: score (0-100), label (Low, Moderate, High), advice (str)
    """
    stress_score = 0
    
    # 1. Pending tasks penalty
    # 5 points for every pending task, capped at 40
    num_pending = len(pending_tasks_df)
    stress_score += min(num_pending * 5, 40)
    
    # 2. Upcoming deadlines penalty
    # Find tasks due within 3 days
    if num_pending > 0:
        pending_tasks_df['deadline'] = pd.to_datetime(pending_tasks_df['deadline']).dt.date
        today = date.today()
        urgent_tasks = pending_tasks_df[pending_tasks_df['deadline'] <= (today + pd.Timedelta(days=3))].shape[0]
        stress_score += min(urgent_tasks * 10, 30)
    
    # 3. Exam preparation penalty
    # If subjects exist and average preparation is low, add stress
    if not subjects_df.empty:
        avg_prep = subjects_df['preparation_progress'].mean()
        if avg_prep < 50:
            stress_score += min((50 - avg_prep) * 0.6, 30) # up to 30 points
            
    # Cap at 100
    stress_score = min(stress_score, 100)
    
    if stress_score < 30:
        label = "Low"
        color = "green"
        advice = "You're doing great! Keep up the good work and maintain your pace."
    elif stress_score < 70:
        label = "Moderate"
        color = "orange"
        advice = "Things are getting a bit busy. Prioritize your urgent tasks and try to allocate dedicated study time."
    else:
        label = "High"
        color = "red"
        advice = "Take a deep breath! Break down your tasks into smaller chunks, focus on immediate deadlines, and don't forget to rest."
        
    return stress_score, label, color, advice

def render_stress_indicator(score, label, color, advice):
    """Renders a visual stress indicator gauge."""
    st.subheader("Mental Well-being & Stress Analysis")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        fig = px.pie(
            values=[score, max(0, 100-score)],
            names=['Stress Level', 'Relaxation'],
            hole=0.7,
            color=['Stress Level', 'Relaxation'],
            color_discrete_map={'Stress Level': color, 'Relaxation': '#E0E0E0'}
        )
        fig.update_traces(textinfo='none', hoverinfo='none')
        fig.update_layout(
            showlegend=False, 
            margin=dict(t=0, b=0, l=0, r=0),
            annotations=[dict(text=f"{int(score)}%", x=0.5, y=0.5, font_size=20, showarrow=False)]
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    with col2:
        st.markdown(f"### Current Level: <span style='color:{color}'>{label}</span>", unsafe_allow_html=True)
        st.info(advice)

def render_workload_distribution(tasks_df):
    """Renders a bar chart showing hours estimated per subject."""
    if tasks_df.empty:
        st.write("No tasks found to analyze workload.")
        return
        
    st.subheader("Workload Distribution (Estimated Hours)")
    workload = tasks_df.groupby('subject')['estimated_hours'].sum().reset_index()
    
    if workload.empty or workload['estimated_hours'].sum() == 0:
        st.write("No estimated hours added for your tasks.")
        return
        
    fig = px.bar(workload, x='subject', y='estimated_hours', color='subject',
                 labels={'subject': 'Subject', 'estimated_hours': 'Total Hours Required'})
    st.plotly_chart(fig, use_container_width=True)

def render_preparation_progress(subjects_df):
    """Renders a progress bar style visualization for subject preparation."""
    if subjects_df.empty:
         st.write("No subjects added yet. Add subjects in the Exam Preparation tab.")
         return
         
    st.subheader("Exam Readiness by Subject")
    fig = px.bar(subjects_df, y='name', x='preparation_progress', orientation='h',
                 color='preparation_progress', text='preparation_progress',
                 color_continuous_scale='Mint', range_x=[0, 100],
                 labels={'name': 'Subject', 'preparation_progress': 'Progress (%)'})
    fig.update_traces(texttemplate='%{text}%', textposition='outside')
    st.plotly_chart(fig, use_container_width=True)
