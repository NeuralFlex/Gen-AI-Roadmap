# 🧠 Interviewer Chatbot

A **LangGraph-powered terminal application** that conducts AI-driven technical interviews.  
It dynamically generates and evaluates interview questions using **Gemini** and **Tavily APIs**, managing the entire conversation through a **stateful graph**.

---

## 📘 Table of Contents

1. [Core Components](#1-core-components)  
2. [Installation](#2-installation)  
   - [2.1 Prerequisites](#21-prerequisites)  
   - [2.2 Environment Configuration](#22-environment-configuration)  
   - [2.3 Setup Steps](#23-setup-steps)  
   - [2.4 Running the Application](#24-running-the-application)  

---

## 1. Core Components

### 1.1 Interview Graph (LangGraph)
Implements the main interview logic as a directed graph in `graph/graph.py`.  
Each node handles a stage of the interview (setup, question generation, answer evaluation, and final summary).

### 1.2 State Management
`graph/state.py` defines `InterviewState`, which maintains all session variables such as topic, current step, and responses.

### 1.3 Gemini & Tavily Integration
- **`services/gemini_client.py`** – Handles question generation and answer evaluation using the Gemini API.  
- **`services/tavily_client.py`** – Provides contextual content and background knowledge via Tavily API.

### 1.4 Configuration & Prompts
- **`config/prompts.py`** – Contains predefined prompt templates for interviews.  
- **`config/settings.py`** – Loads API keys and environment settings.

### 1.5 Logging
- **`utils/logger.py`** – Handles structured logging.  
  All logs are printed directly in the terminal.

---

## 2. Installation

### 2.1 Prerequisites
Ensure the following are installed:
- Python 3.10+
- pip
- Virtual environment tool (`venv` or `virtualenv`)

---

### 2.2 Environment Configuration

Create a `.env` file in the project root with your API keys, The API keys required to run this code can be found in .env_example in root folder of the project



---

### 2.3 Setup Steps

```bash
# Clone the repository
git clone https://github.com/yourusername/interviewer_chatbot.git
cd interviewer_chatbot

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate   # On Linux/macOS
venv\Scripts\activate      # On Windows

# Install dependencies
pip install -r requirements.txt
```

---

### 2.4 Running the Application

Once setup is complete, launch the chatbot from your terminal:

```bash
python main.py
```

You’ll be prompted to:

1. Enter an **interview topic** (e.g., “Python”, “R Language”, “Machine Learning”).
2. Choose the **question type** – `broad`, `narrow_up`, or `follow_up`.

The system will then conduct a full AI-driven interview session in the terminal.




---

✅ **Ready to Use!**
You can now run and extend your **LangGraph-powered terminal interview chatbot**
to support new interview types, topics, and logic flows — all from your terminal.

