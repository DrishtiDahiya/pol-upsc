import streamlit as st
import os
import re
import google.generativeai as genai

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
def search_concepts_in_file(file_path, query):
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
        Your task is to synthesize these snippets into a holistic, linked note. 
        
        CRITICAL INSTRUCTIONS:
        - Use simple, clear, and high-yield language.
        - Preserve the core constitutional meaning and nuances.
        - Explain how this concept connects across different chapters (e.g., Executive vs Legislative).
        
        Material:
        {contexts}
        
        Format the output with:
        1. Simple Holistic Overview
        2. Key Linkages (Connecting the dots across chapters)
        3. UPSC Quick-Recall (Simple bullet points for Prelims/Mains)
        """
        
        response = model.generate_content(prompt)
        return response.text, None
    except Exception as e:
        return None, f"Error: {str(e)}"

# Main UI
def main():
    css_path = os.path.join(os.path.dirname(__file__), 'style.css')
    if os.path.exists(css_path):
        load_css(css_path)
    
    # Sidebar for configuration
    with st.sidebar:
        st.markdown("### ⚙️ Configuration")
        api_key = st.text_input("Gemini API Key", type="password", help="Get your API key from https://aistudio.google.com/", key="gemini_api_key")
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
            file_path = os.path.join(os.path.dirname(__file__), 'pol.txt')
            results = search_concepts_in_file(file_path, query)
            
            if not results:
                st.info(f"No mentions found for '{query}' in the current material.")
            else:
                st.subheader(f"Found '{query}' in {len(results)} contexts")
                
                # Display Results
                cols = st.columns(len(results))
                for i, res in enumerate(results):
                    with cols[i]:
                        st.markdown(f"""
                            <div class='glass-card' style='height: 100%;'>
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
                    with st.spinner(f"Synthesizing knowledge about **{query}**..."):
                        all_contexts = "\n\n".join([r['content'] for r in results])
                        notes, error = generate_ai_notes(api_key, query, all_contexts)
                        
                        if error:
                            st.error(error)
                        else:
                            st.markdown(notes)
                
                st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
