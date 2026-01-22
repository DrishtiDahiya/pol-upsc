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

def create_pdf(text, query):
    try:
        pdf = FPDF()
        pdf.add_page()
        
        # Effective page width
        epw = pdf.epw
        
        # Title - Strictly ASCII
        pdf.set_font("Helvetica", "B", 16)
        safe_title = f"UPSC Polity Notes: {query}".encode('ascii', 'ignore').decode('ascii')
        pdf.multi_cell(epw, 10, safe_title, align='C')
        pdf.ln(10)
        
        # Content - Strictly ASCII
        pdf.set_font("Helvetica", "", 12)
        
        lines = text.split('\n')
        for line in lines:
            if not line.strip():
                pdf.ln(5)
                continue
                
            # Nuclear ASCII cleanup
            clean_line = line.encode('ascii', 'ignore').decode('ascii')
            
            # Headers
            if clean_line.startswith('#'):
                pdf.set_font("Helvetica", "B", 14)
                cleaned = clean_line.lstrip('#').strip()
                pdf.multi_cell(epw, 10, cleaned)
                pdf.set_font("Helvetica", "", 12)
            else:
                # Basic bullet point handling with ASCII dash
                if clean_line.strip().startswith(('-', '*')):
                    core_text = re.sub(r'^[\-\*]\s*', '', clean_line.strip())
                    cleaned = f"  - {core_text.replace('**', '')}"
                else:
                    cleaned = clean_line.replace('**', '').strip()
                
                pdf.multi_cell(epw, 10, cleaned)
                    
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
        col1, col2 = st.columns([4, 1])
        with col1:
            query = st.text_input("Enter a concept (e.g. Money Bill, President, CAG)", placeholder="Type here...", label_visibility="collapsed", key="search_query")
        with col2:
            search_btn = st.button("Link Concepts", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    if search_btn or query:
        if not query:
            st.warning("Please enter a concept to search.")
        else:
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
