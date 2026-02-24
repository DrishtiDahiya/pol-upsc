import streamlit as st
import os
import re
import google.generativeai as genai
from fpdf import FPDF
import io

# Page config
st.set_page_config(
    page_title="UPSC Concept Linker",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load CSS
def load_css(file_name):
    css_path = os.path.join(os.path.dirname(__file__), file_name)
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Helper to find concepts in text
def search_concepts_in_file(file_path, query, content=None, split_pattern=r'(?i)(?=CHAPTER \d+|Chapter \d+)'):
    if content is None:
        if not file_path or not os.path.exists(file_path):
            return []
        with open(file_path, 'r', encoding="utf-8") as f:
            content = f.read()
    
    # Split content by chapters
    chapters = re.split(split_pattern, content)
    
    results = []
    for chapter in chapters:
        if not chapter.strip():
            continue
        if query.lower() in chapter.lower():
            # Extract chapter title
            title_match = re.search(r'(?i)(?:CHAPTER \d+|Chapter \d+)[:]?\s*(.*)', chapter)
            title = "Unknown Chapter"
            if title_match:
                lines = title_match.group(1).split('\n')
                for line in lines:
                    if line.strip():
                        title = line.strip()
                        break
            
            # Find relevant snippets (lines containing the query)
            lines = chapter.split('\n')
            snippets = [line.strip() for line in lines if query.lower() in line.lower() and not line.startswith('#')]
            
            results.append({
                'chapter': title,
                'content': chapter.strip(),
                'snippets': snippets
            })
    
    return results

# AI Generation
def generate_ai_notes(api_key, query, contexts, subject_expert="UPSC Expert"):
    if not api_key:
        return None, "Please provide a Gemini API key in the sidebar."
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-pro')
        
        prompt = f"""
        You are a {subject_expert}. I will provide you with snippets from a textbook regarding the concept: "{query}".
        Your task is to synthesize these snippets into a high-yield, structured note for UPSC preparation.
        
        CRITICAL FORMATTING INSTRUCTIONS:
        - Use **Pointers/Bullet points** for all detailed information. Avoid long paragraphs.
        - Use **Clear Markdown Headers** (`##`, `###`) for topics and sub-topics.
        - **Bold** key technical terms, articles, or economic concepts.
        - Create a logical flow: Concept Definition -> Core Provisions/Principles -> Linking with other Topics -> Exam Relevance.
        
        Material:
        {contexts}
        
        Format the output precisely as follows:
        # {query}: Concept Analysis
        
        ## 1. Structured Overview
        - [Define the concept in 2-3 pointers]
        
        ## 2. Core Technical Provisions/Details
        - [Key principles, data, powers, and duties in pointers]
        - [Use sub-topics if necessary]
        
        ## 3. High-Yield Linkages (Connecting the Dots)
        - [Explain connections across different chapters/subjects in pointers]
        
        ## 4. UPSC Quick-Recall (Prelims & Mains Focus)
        - [Snapshot pointers for fast revision]
        """
        
        response = model.generate_content(prompt)
        return response.text, None
    except Exception as e:
        return None, f"Error: {str(e)}"

def fetch_current_affairs(api_key, query, subject="Polity"):
    if not api_key:
        return None, "Please provide a Gemini API key in the sidebar."
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-pro') 
        
        prompt = f"""
        You are a UPSC Current Affairs Expert. Focus on the {subject} topic: "{query}".
        Search for the top 10 most important events, reports, data, bills, or controversies related to "{query}" that occurred in the last year (Jan 2025 - Jan 2026).
        
        PRIORITY INSTRUCTION: Prioritize coverage and analysis from the **Indian Express** (especially 'Explained' sections) and other standard UPSC sources.
        
        List them in order of priority (most searched/relevant at the top).
        
        Format each event with a title and a brief 1-line summary of its UPSC relevance in simple language.
        Format accurately as a JSON list of objects:
        [
          {{"title": "Event Name", "relevance": "Brief UPSC relevance in simple terms..."}},
          ...
        ]
        Limit to exactly 10 events. Output ONLY the JSON.
        """
        
        response = model.generate_content(prompt)
        # Extract JSON from response
        json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
        if json_match:
            import json
            events = json.loads(json_match.group(0))
            return events, None
        else:
            return None, "Failed to parse events from AI response. Please try again."
    except Exception as e:
        return None, str(e)

def generate_affair_notes(api_key, query, events, subject_expert="UPSC Expert"):
    if not api_key:
        return None, "Please provide a Gemini API key in the sidebar."
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-pro')
        
        events_str = "\n".join([f"- {e['title']}: {e['relevance']}" for e in events])
        
        prompt = f"""
        You are a {subject_expert}. I will provide you with the top 10 current events related to the topic: "{query}".
        Your task is to create comprehensive, integrated notes for UPSC preparation that link these recent events with standard subject concepts.
        
        Top Events from 2025-2026:
        {events_str}
        
        CRITICAL STYLE INSTRUCTIONS:
        - **Prioritize Indian Express Perspective**: Incorporate insights/analysis logic typically found in Indian Express 'Explained' or 'Opinion' columns.
        - **Simple Narrative**: Use very simple, easy-to-understand language for the explanations and connections.
        - **Technical Precision**: DO NOT change or simplify important technical words, articles, or economic terms. Keep original terms exactly as they are.
        
        CRITICAL FORMATTING INSTRUCTIONS:
        - Use **Pointers/Bullet points** for all detailed information.
        - Use **Clear Markdown Headers** (`##`, `###`).
        - **Bold** key technical terms and articles.
        
        Format the output precisely as follows:
        # {query}: Current Affairs Analysis (2025-2026)
        
        ## 1. Simple Timeline & Key Developments
        - [Summarize the events in very simple language in 3-4 pointers]
        
        ## 2. Deep-Dive Analysis (The 'Explained' View)
        - [Provide deeper insights inspired by Indian Express analysis]
        - [Keep the language simple but the content high-yield]
        
        ## 3. Conceptual & Static Linkage 
        - [Link to Static Theory using exact technical terms]
        - [Explain the impact on standard subject logic in simple pointers]
        
        ## 4. Revision Snapshot (Prelims & Mains)
        - [Key terms and potential question themes]
        """
        
        response = model.generate_content(prompt)
        return response.text, None
    except Exception as e:
        return None, str(e)

def create_pdf(text, query, subject_tag="Polity"):
    try:
        pdf_file = FPDF()
        pdf_file.set_margins(15, 15, 15)
        pdf_file.add_page()
        
        # Effective page width
        epw = pdf_file.epw
        
        # Robust ASCII cleaner
        def clean_text(s):
            return "".join(c for c in s if 32 <= ord(c) <= 126 or c == '\n')
        
        # Title
        pdf_file.set_font("Helvetica", "B", 16)
        safe_title = clean_text(f"UPSC {subject_tag} Notes: {query}")
        pdf_file.multi_cell(epw, 8, safe_title, align='C')
        pdf_file.ln(10)
        
        # Content
        pdf_file.set_font("Helvetica", "", 11)
        
        lines = text.split('\n')
        for line in lines:
            if not line.strip():
                pdf_file.ln(4)
                continue
                
            clean_line = clean_text(line)
            
            # Headers
            if clean_line.startswith('#'):
                pdf_file.ln(5)
                pdf_file.set_font("Helvetica", "B", 13)
                cleaned = clean_line.lstrip('#').strip()
                pdf_file.multi_cell(epw, 8, cleaned)
                pdf_file.set_font("Helvetica", "", 11)
                pdf_file.ln(2)
            else:
                if clean_line.strip().startswith(('-', '*')):
                    pdf_file.set_x(20)
                    pdf_file.write(7, "- ")
                    core_text = re.sub(r'^[\-\*]\s*', '', clean_line.strip()).replace('**', '')
                    current_x = pdf_file.get_x()
                    pdf_file.set_left_margin(current_x)
                    pdf_file.multi_cell(0, 7, core_text)
                    pdf_file.set_left_margin(15)
                    pdf_file.set_x(15)
                else:
                    cleaned = clean_line.replace('**', '').strip()
                    pdf_file.multi_cell(epw, 7, cleaned)
                    
        return bytes(pdf_file.output()), None
    except Exception as e:
        return None, str(e)

def render_subject_ui(subject_name, default_file, expert_role, api_key, uploaded_file):
    # Header
    icon = "⚖️" if subject_name == "Polity" else "📈"
    st.markdown(f"""
        <div style='text-align: center; padding: 1rem 0;'>
            <h1>{icon} {subject_name} Concept Linker</h1>
            <p style='color: #94a3b8;'>Synthesize UPSC {subject_name} concepts from standard material</p>
        </div>
    """, unsafe_allow_html=True)

    # Search Section
    with st.container():
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            query = st.text_input(f"Enter a {subject_name} concept", placeholder="Type here...", label_visibility="collapsed", key=f"query_{subject_name}")
        with col2:
            search_btn = st.button("Link Concepts", use_container_width=True, key=f"btn_link_{subject_name}")
        with col3:
            affair_btn = st.button("Current Affair", use_container_width=True, key=f"btn_ca_{subject_name}")
        st.markdown("</div>", unsafe_allow_html=True)

    if search_btn or affair_btn or query: # Allow Enter key to trigger search if query is provided
        if not query:
            if search_btn or affair_btn:
                st.warning("Please enter a concept to search.")
        elif affair_btn:
            if not api_key:
                st.warning(f"⚠️ Enter your Gemini API key in the sidebar to fetch {subject_name} current affairs.")
            else:
                with st.spinner(f"Searching for recent events related to **{query}**..."):
                    events, error = fetch_current_affairs(api_key, query, subject=subject_name)
                    if error:
                        st.error(error)
                    else:
                        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
                        st.subheader(f"🤖 AI Integrated {subject_name} Current Affair Notes")
                        with st.spinner("Synthesizing events into UPSC notes..."):
                            af_notes, af_error = generate_affair_notes(api_key, query, events, subject_expert=expert_role)
                            if af_error:
                                st.error(af_error)
                            else:
                                st.markdown(af_notes)
                                pdf_bytes, pdf_error = create_pdf(af_notes, f"{query}_Current_Affairs", subject_tag=subject_name)
                                if not pdf_error:
                                    st.download_button(label="Download CA Notes as PDF", data=pdf_bytes, file_name=f"{subject_name}_CA_Notes_{query.replace(' ', '_')}.pdf", mime="application/pdf", use_container_width=True)
                        st.markdown("</div>", unsafe_allow_html=True)

                        st.divider()
                        st.subheader(f"📅 Top Current Events for '{query}' (Last Year)")
                        num_cols = 2
                        for i in range(0, len(events), num_cols):
                            cols = st.columns(num_cols)
                            chunk = events[i:i + num_cols]
                            for j, event in enumerate(chunk):
                                with cols[j]:
                                    st.markdown(f"""
                                        <div class='glass-card' style='height: 100%; margin-bottom: 20px;'>
                                            <h4 style='color: #60a5fa; margin-bottom: 5px;'>{i+j+1}. {event['title']}</h4>
                                            <p style='font-size: 0.9rem; color: #cbd5e1;'>{event['relevance']}</p>
                                        </div>
                                    """, unsafe_allow_html=True)

        elif search_btn:
            with st.spinner(f"Linking concepts for **{query}**..."):
                if uploaded_file is not None:
                    content = uploaded_file.getvalue().decode("utf-8")
                    results = search_concepts_in_file(None, query, content=content)
                else:
                    results = search_concepts_in_file(default_file, query)
                
                if not results:
                    st.info(f"No mentions found for '{query}' in the current material.")
                else:
                    # AI Synthesis Section First
                    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
                    st.subheader(f"🤖 AI Synthesized {subject_name} Notes")
                    if not api_key:
                        st.warning("⚠️ Enter your Gemini API key in the sidebar to generate smart notes.")
                    else:
                        max_ai_results = 15
                        ai_results = results[:max_ai_results]
                        all_contexts = "\n\n".join([r['content'] for r in ai_results])
                        notes, error = generate_ai_notes(api_key, query, all_contexts, subject_expert=expert_role)
                        if error:
                            st.error(error)
                        else:
                            st.markdown(notes)
                            pdf_bytes, pdf_error = create_pdf(notes, query, subject_tag=subject_name)
                            if not pdf_error:
                                st.download_button(label="Download Notes as PDF", data=pdf_bytes, file_name=f"{subject_name}_Notes_{query.replace(' ', '_')}.pdf", mime="application/pdf", use_container_width=True)
                    st.markdown("</div>", unsafe_allow_html=True)

                    # Source Contexts at the end
                    st.divider()
                    st.subheader(f"📖 Textual Sources ({len(results)} contexts)")
                    num_cols = 3
                    for i in range(0, len(results), num_cols):
                        cols = st.columns(num_cols)
                        chunk = results[i:i + num_cols]
                        for j, res in enumerate(chunk):
                            with cols[j]:
                                st.markdown(f"""
                                    <div class='glass-card' style='height: 100%; margin-bottom: 20px;'>
                                        <h3 style='font-size: 1.1rem;'>{res['chapter']}</h3>
                                        <div style='font-size: 0.9rem; color: #cbd5e1; margin-top: 10px;'>
                                            {"<br><br>".join([f"• {s}" for s in res['snippets'][:3]])}...
                                        </div>
                                    </div>
                                """, unsafe_allow_html=True)

# Main UI
def main():
    load_css('style.css')
    
    # Sidebar for configuration
    with st.sidebar:
        st.markdown("### ⚙️ Configuration")
        api_key = st.text_input("Gemini API Key", type="password", help="Get your API key from https://aistudio.google.com/", key="gemini_api_key")
        
        st.markdown("### 📄 Material Upload")
        uploaded_pol = st.file_uploader("Upload custom pol.txt", type=["txt"], key="upload_pol")
        uploaded_eco = st.file_uploader("Upload custom eco.txt", type=["txt"], key="upload_eco")
        
        st.info("Your API key is used only for the current session.")
    
    # Tabs for Subjects
    tab_pol, tab_eco = st.tabs(["⚖️ Polity", "📈 Economics"])
    
    curr_dir = os.path.dirname(__file__)
    
    with tab_pol:
        render_subject_ui(
            "Polity", 
            os.path.join(curr_dir, 'pol.txt'), 
            "UPSC Polity Expert", 
            api_key, 
            uploaded_pol
        )
        
    with tab_eco:
        render_subject_ui(
            "Economics", 
            os.path.join(curr_dir, 'eco.txt'), 
            "UPSC Economics Expert", 
            api_key, 
            uploaded_eco
        )

if __name__ == "__main__":
    main()
