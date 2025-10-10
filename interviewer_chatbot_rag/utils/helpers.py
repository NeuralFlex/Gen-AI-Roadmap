from services.gemini_client import GeminiClient
import io
import PyPDF2

gemini_client = GeminiClient()
def extract_text_from_cv(filename: str, content: bytes) -> str:
    """Extract text from CV based on file type."""
    try:
        if filename.endswith('.pdf'):
            return extract_text_from_pdf(content)
        elif filename.endswith('.txt'):
            return content.decode('utf-8')
        elif filename.endswith(('.doc', '.docx')):
            return extract_text_from_doc(content, filename)
        else:
            return content.decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"Error extracting text from CV: {e}")
        return ""

def extract_text_from_pdf(content: bytes) -> str:
    pdf_file = io.BytesIO(content)
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text

def extract_text_from_doc(content: bytes, filename: str) -> str:
    if filename.endswith('.docx'):
        doc_file = io.BytesIO(content)
        doc = Document(doc_file)
        return "\n".join([p.text for p in doc.paragraphs])
    else:
        return "Word document extraction only supports .docx"

def analyze_cv_for_topic(cv_text: str) -> str:
    """Analyze CV content to determine interview focus."""
    prompt = f"""
    Analyze this CV/resume and determine the most appropriate technical interview topic focus.
    Consider skills, experience, technologies mentioned, and role preferences.
    
    CV Content:
    {cv_text[:3000]}
    
    Return ONLY the main interview topic as a short phrase.
    """
    
    topic = gemini_client.generate_content(prompt)
    if not topic:
        topic = "Software Development"
    return topic.strip()

