import os
from typing import Dict
from utils.logger import setup_logger
from .helpers import (
    extract_text_from_cv,
    extract_text_from_doc,
    extract_text_from_pdf,
    analyze_cv_for_topic,
)

logger = setup_logger(__name__)


def load_cv_from_path(path: str) -> Dict[str, str]:
    """
    Loads and analyzes a CV file from a given file path.

    Extracts text content from the file, determines the topic, and returns a dictionary
    containing the extracted text, filename, and identified topic.

    Args:
        path (str): The file path of the CV document.

    Returns:
        Dict[str, str]: A dictionary containing:
            - 'cv_content': Extracted text from the CV
            - 'cv_filename': The name of the CV file
            - 'topic': The analyzed topic of the CV
    """
    try:
        with open(path, "rb") as file:
            content = file.read()

        filename = os.path.basename(path)
        text = extract_text_from_cv(filename, content)
        topic = analyze_cv_for_topic(text)

        logger.info(f"Successfully processed CV: {filename}")

        return {
            "cv_content": text,
            "cv_filename": filename,
            "topic": topic,
        }

    except Exception as e:
        logger.exception(f"Error reading CV from path '{path}': {e}")
        return {
            "cv_content": "",
            "cv_filename": "",
            "topic": "",
        }


def main() -> None:
    """Main function for testing the CV extraction process."""
    data = load_cv_from_path("cv.pdf")
    print(data)


if __name__ == "__main__":
    main()
