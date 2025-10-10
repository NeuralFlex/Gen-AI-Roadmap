from .helpers import extract_text_from_cv, extract_text_from_doc, extract_text_from_pdf, analyze_cv_for_topic
import os

def load_cv_from_path(path: str) -> dict:
    """This function takes a CV path and returns the extracted text and topic."""
    try:
        with open(path, 'rb') as f:
            content = f.read()
        filename = os.path.basename(path)
        text = extract_text_from_cv(filename, content)
        topic = analyze_cv_for_topic(text)
        return {"cv_content": text, "cv_filename": filename, "topic": topic}
    except Exception as e:
        print(f"Error reading CV: {e}")
        return {"cv_content": "", "cv_filename": "", "topic": ""}

def main():
    data = load_cv_from_path("cv.pdf")
    print(data)

if __name__ == "__main__":
    main()