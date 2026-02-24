from pypdf import PdfReader
import os

def convert_pdf_to_txt(pdf_path, txt_path):
    print(f"Reading {pdf_path}...")
    reader = PdfReader(pdf_path)
    text = ""
    for i, page in enumerate(reader.pages):
        text += f"--- Page {i+1} ---\n"
        page_text = page.extract_text()
        if page_text:
            # If the extraction is word-per-line, try to join them
            # We judge this by checking the average length of lines
            lines = page_text.split('\n')
            if len(lines) > 20:
                avg_len = sum(len(line.strip()) for line in lines) / len(lines)
                if avg_len < 10: # likely word-per-line
                    # Join lines that don't end with sentence-ending punctuation
                    joined_text = ""
                    for line in lines:
                        line = line.strip()
                        if not line: continue
                        joined_text += line + " "
                    page_text = joined_text
            
            text += page_text + "\n\n"
        
        if (i + 1) % 50 == 0:
            print(f"Processed {i+1} pages...")
    
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"Successfully saved to {txt_path}")

if __name__ == "__main__":
    pdf_file = "/Users/drishtidahiya/Documents/UPSC/eco.pdf"
    txt_file = "/Users/drishtidahiya/Documents/UPSC/eco.txt"
    convert_pdf_to_txt(pdf_file, txt_file)
