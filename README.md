# Polity Concept Linker

A Streamlit application for synthesising UPSC Polity concepts across M. Laxmikanth's "Indian Polity" (8th Edition).

## Features
- **Concept Search**: Quickly find mentions of specific polity concepts across various chapters.
- **AI Synthesis**: Uses Google's Gemini AI to generate holistic, linked notes based on found contexts.
- **UPSC Oriented**: Tailored for Civil Services preparation with a focus on high-yield language and key linkages.

## Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   streamlit run pol.py
   ```

4. **API Key**: 
   Provide your Gemini API key in the sidebar of the application.

## Data Source
This application expects a `pol.txt` file (not included in the repository) to be present in the root directory, containing the text content of "Indian Polity" by M. Laxmikanth.
