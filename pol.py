import streamlit as st
import os
import re
import google.generativeai as genai
from fpdf import FPDF
import io

# Page config
st.set_page_config(
    page_title="Polity Concept Linker",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load CSS
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Helper to find concepts in text
def search_concepts_in_file(file_path, query, content=None):
    if content is None:
        if not os.path.exists(file_path):
            return []
        with open(file_path, 'r') as f:
            content = f.read()
    
    # Split content by chapters (demarcated by CHAPTER \d+)
    chapters = re.split(r'(?=CHAPTER \d+)', content)
    
    results = []
    for chapter in chapters:
        if not chapter.strip():
            continue
        if query.lower() in chapter.lower():
            # Extract chapter title
            title_match = re.search(r'CHAPTER \d+[:]?\s+(.*)', chapter)
            title = title_match.group(1).strip() if title_match else "Unknown Chapter"
            
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
def generate_ai_notes(api_key, query, contexts):
    if not api_key:
        return None, "Please provide a Gemini API key in the sidebar."
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt = f"""
        You are a UPSC Polity Expert. I will provide you with snippets from a textbook regarding the concept: "{query}".
        Your task is to synthesize these snippets into a high-yield, structured note for UPSC preparation.
        
        CRITICAL FORMATTING INSTRUCTIONS:
        - Use **Pointers/Bullet points** for all detailed information. Avoid long paragraphs.
        - Use **Clear Markdown Headers** (`##`, `###`) for topics and sub-topics.
        - **Bold** key constitutional terms and articles.
        - Create a logical flow: Concept Definition -> Constitutional Provisions -> Linking with other Chapters -> Exam Relevance.
        
        Material:
        {contexts}
        
        Format the output precisely as follows:
        # {query}: Concept Analysis
        
        ## 1. Structured Overview
        - [Define the concept in 2-3 pointers]
        
        ## 2. Core Constitutional Provisions
        - [Key articles, powers, and duties in pointers]
        - [Use sub-topics if necessary]
        
        ## 3. High-Yield Linkages (Connecting the Dots)
        - [Explain connections across different chapters in pointers]
        
        ## 4. UPSC Quick-Recall (Prelims & Mains Focus)
        - [Snapshot pointers for fast revision]
        """
        
        response = model.generate_content(prompt)
        return response.text, None
    except Exception as e:
        return None, f"Error: {str(e)}"

def fetch_current_affairs(api_key, query):
    if not api_key:
        return None, "Please provide a Gemini API key in the sidebar."
    
    try:
        genai.configure(api_key=api_key)
        # Using 2.0 flash as it's reliable for structured extraction
        model = genai.GenerativeModel('gemini-2.0-flash') 
        
        prompt = f"""
        You are a UPSC Current Affairs Expert. Focus on the political/legal topic: "{query}".
        Search for the top 10 most important events, reports, bills, SC judgments, or controversies related to "{query}" that occurred in the last year (Jan 2025 - Jan 2026).
        
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

def generate_affair_notes(api_key, query, events):
    if not api_key:
        return None, "Please provide a Gemini API key in the sidebar."
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        events_str = "\n".join([f"- {e['title']}: {e['relevance']}" for e in events])
        
        prompt = f"""
        You are a UPSC Polity Expert. I will provide you with the top 10 current events related to the topic: "{query}".
        Your task is to create comprehensive, integrated notes for UPSC preparation that link these recent events with standard polity concepts.
        
        Top Events from 2025-2026:
        {events_str}
        
        CRITICAL STYLE INSTRUCTIONS:
        - **Prioritize Indian Express Perspective**: Incorporate insights/analysis logic typically found in Indian Express 'Explained' or 'Opinion' columns.
        - **Simple Narrative**: Use very simple, easy-to-understand language for the explanations and connections.
        - **Technical Precision**: DO NOT change or simplify important technical words, constitutional phrases, legal terms, or article names (e.g., 'Writ of Mandamus', 'Doctrine of Basic Structure', 'Constitutional Morality'). Keep these original terms exactly as they are.
        
        CRITICAL FORMATTING INSTRUCTIONS:
        - Use **Pointers/Bullet points** for all detailed information.
        - Use **Clear Markdown Headers** (`##`, `###`).
        - **Bold** key constitutional terms, articles, and committee names.
        
        Format the output precisely as follows:
        # {query}: Current Affairs Analysis (2025-2026)
        
        ## 1. Simple Timeline & Key Developments
        - [Summarize the events in very simple language in 3-4 pointers]
        
        ## 2. Deep-Dive Analysis (The 'Explained' View)
        - [Provide deeper insights inspired by Indian Express analysis]
        - [Keep the language simple but the content high-yield]
        
        ## 3. Constitutional & Static Linkage 
        - [Link to Articles, Parts, or SC Judgments using exact technical terms]
        - [Explain the impact on standard polity logic in simple pointers]
        
        ## 4. Revision Snapshot (Prelims & Mains)
        - [Key terms and potential question themes]
        """
        
        response = model.generate_content(prompt)
        return response.text, None
    except Exception as e:
        return None, str(e)

def create_pdf(text, query):
    try:
        pdf = FPDF()
        pdf.set_margins(15, 15, 15)
        pdf.add_page()
        
        # Effective page width
        epw = pdf.epw
        
        # Robust ASCII cleaner: Only allow standard printable characters
        def clean_text(s):
            # Keep standard ASCII (32-126) and newlines
            return "".join(c for c in s if 32 <= ord(c) <= 126 or c == '\n')
        
        # Title
        pdf.set_font("Helvetica", "B", 16)
        safe_title = clean_text(f"UPSC Polity Notes: {query}")
        pdf.multi_cell(epw, 8, safe_title, align='C')
        pdf.ln(10)
        
        # Content
        pdf.set_font("Helvetica", "", 11)
        
        lines = text.split('\n')
        for line in lines:
            if not line.strip():
                pdf.ln(4)
                continue
                
            clean_line = clean_text(line)
            
            # Headers
            if clean_line.startswith('#'):
                pdf.ln(5)
                pdf.set_font("Helvetica", "B", 13)
                cleaned = clean_line.lstrip('#').strip()
                pdf.multi_cell(epw, 8, cleaned)
                pdf.set_font("Helvetica", "", 11)
                pdf.ln(2)
            else:
                # Hanging Indent Logic
                if clean_line.strip().startswith(('-', '*')):
                    bullet_w = 7  # Width for bullet + space
                    pdf.set_x(15 + 5) # Bullet offset
                    pdf.write(7, "- ")
                    
                    # Core text calculation
                    core_text = re.sub(r'^[\-\*]\s*', '', clean_line.strip()).replace('**', '')
                    
                    # Mathematical indent fix: 
                    # New X = Left Margin (15) + Bullet Indent (5) + Bullet Width (7) = 27
                    # New Width = EPW - (Total Indent - Left Margin) 
                    # Actually simpler: Just set left margin for the block
                    
                    current_x = pdf.get_x()
                    pdf.set_left_margin(current_x)
                    pdf.multi_cell(0, 7, core_text) # 0 means till the right margin
                    pdf.set_left_margin(15) # Reset to standard
                    pdf.set_x(15)
                else:
                    cleaned = clean_line.replace('**', '').strip()
                    pdf.multi_cell(epw, 7, cleaned)
                    
        return bytes(pdf.output()), None
    except Exception as e:
        return None, str(e)

# Main UI
def main():
    css_path = os.path.join(os.path.dirname(__file__), 'style.css')
    if os.path.exists(css_path):
        load_css(css_path)
    
    # Sidebar for configuration
    with st.sidebar:
        st.markdown("### ⚙️ Configuration")
        api_key = st.text_input("Gemini API Key", type="password", help="Get your API key from https://aistudio.google.com/", key="gemini_api_key")
        
        st.markdown("### 📄 Material")
        uploaded_file = st.file_uploader("Upload pol.txt (Optional)", type=["txt"], help="If not provided, the default local pol.txt will be used.")
        
        st.info("Your API key is used only for the current session.")
    
    # Header
    st.markdown("""
        <div style='text-align: center; padding: 2rem 0;'>
            <h1>⚖️ Polity Concept Linker</h1>
            <p style='color: #94a3b8;'>Synthesize UPSC Polity concepts across Lakshmikanth</p>
        </div>
    """, unsafe_allow_html=True)

    # Search Section
    with st.container():
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            query = st.text_input("Enter a concept (e.g. Money Bill, President, CAG)", placeholder="Type here...", label_visibility="collapsed", key="search_query")
        with col2:
            search_btn = st.button("Link Concepts", use_container_width=True)
        with col3:
            affair_btn = st.button("Current Affair", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    if search_btn or affair_btn or query:
        if not query:
            if search_btn or affair_btn:
                st.warning("Please enter a concept to search.")
        elif affair_btn:
            if not api_key:
                st.warning("⚠️ Enter your Gemini API key in the sidebar to fetch current affairs.")
            else:
                with st.spinner(f"Searching for recent events related to **{query}**..."):
                    events, error = fetch_current_affairs(api_key, query)
                    if error:
                        st.error(error)
                    else:
                        st.subheader(f"📅 Top Current Events for '{query}' (Last Year)")
                        
                        # Display events in a grid
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
                        
                        # AI Current Affair Notes Section
                        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
                        st.subheader("🤖 AI Integrated Current Affair Notes")
                        with st.spinner("Synthesizing events into UPSC notes..."):
                            af_notes, af_error = generate_affair_notes(api_key, query, events)
                            if af_error:
                                st.error(af_error)
                            else:
                                st.markdown(af_notes)
                                
                                # PDF Download Button
                                pdf_bytes, pdf_error = create_pdf(af_notes, f"{query}_Current_Affairs")
                                if pdf_error:
                                    st.error(f"Could not generate PDF: {pdf_error}")
                                else:
                                    st.download_button(
                                        label="Download CA Notes as PDF",
                                        data=pdf_bytes,
                                        file_name=f"Polity_CA_Notes_{query.replace(' ', '_')}.pdf",
                                        mime="application/pdf",
                                        use_container_width=True
                                    )
                        st.markdown("</div>", unsafe_allow_html=True)

        elif search_btn:
            if uploaded_file is not None:
                # Read the uploaded file
                content = uploaded_file.getvalue().decode("utf-8")
                results = search_concepts_in_file(None, query, content=content)
            else:
                file_path = os.path.join(os.path.dirname(__file__), 'pol.txt')
                results = search_concepts_in_file(file_path, query)
            
            if not results:
                st.info(f"No mentions found for '{query}' in the current material.")
            else:
                st.subheader(f"Found '{query}' in {len(results)} contexts")
                
                # Display Results in a grid (fixed 3 columns per row)
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

                # AI Synthesis Section
                st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
                st.subheader("🤖 AI Synthesized Notes")
                
                if not api_key:
                    st.warning("⚠️ Enter your Gemini API key in the sidebar to generate smart notes.")
                else:
                    # Context optimization to avoid 429 Quota errors
                    max_ai_results = 15
                    ai_results = results[:max_ai_results]
                    
                    if len(results) > max_ai_results:
                        st.info(f"💡 Showing all {len(results)} results below, but synthesizing notes from the top {max_ai_results} most relevant chapters to stay within API limits.")
                        
                    with st.spinner(f"Synthesizing knowledge about **{query}**..."):
                        all_contexts = "\n\n".join([r['content'] for r in ai_results])
                        notes, error = generate_ai_notes(api_key, query, all_contexts)
                        
                        if error:
                            st.error(error)
                        else:
                            st.markdown(notes)
                            
                            # PDF Download Button
                            pdf_bytes, pdf_error = create_pdf(notes, query)
                            if pdf_error:
                                st.error(f"Could not generate PDF: {pdf_error}")
                            else:
                                st.download_button(
                                    label="Download Notes as PDF",
                                    data=pdf_bytes,
                                    file_name=f"Polity_Notes_{query.replace(' ', '_')}.pdf",
                                    mime="application/pdf",
                                    use_container_width=True
                                )
                
                st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
