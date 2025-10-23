# 🧠 Interviewer Chatbot

A **LangGraph-powered terminal application** that conducts AI-driven technical interviews.  
It dynamically generates and evaluates interview questions using **Gemini** and **Tavily APIs**, manages state with a **LangGraph-based workflow**, and retrieves relevant CV context using **vector embeddings**, effectively using RAG to enhance the interview experience when necessary.

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

### 1.1 Interview Graph
Implements the main interview logic as a **directed LangGraph**, where each node represents a stage of the interview process — setup, question generation, answer evaluation, and final summary.

### 1.2 Stateful Interview Management
Maintains all session variables such as topic, current step, generated questions, and recorded responses throughout the interview session.

### 1.3 AI & Knowledge Services
- **Gemini** powers dynamic question generation and answer evaluation.  
- **Tavily** enriches the process with contextual background knowledge and relevant references.

### 1.4 Vector Database & Embeddings 
Integrates **vector similarity search** to enhance interview personalization:

- The candidate’s **CV is split into text chunks**.  
- Each chunk is **converted into an embedding vector** using an embedding model (e.g., Gemini or OpenAI).  
- When the candidate answers a question, their answer is also **embedded**.  
- The system computes the **distance (cosine similarity or Euclidean distance)** between the answer embedding and each CV chunk.  
- **Relevant CV chunks** are retrieved if the **distance is below a predefined threshold** (e.g., 0.55).  
- Retrieved chunks are injected into the **question generation** phase for richer, context-aware reasoning.

This enables the chatbot to:
- Ask **personalized follow-up questions** grounded in the candidate’s real experience.  
- **Evaluate responses** more accurately against background knowledge.  
- Keep the entire interview **contextually consistent** across turns.



### 1.5 Prompts and Configuration

Uses structured prompt templates and environment-driven configuration to ensure consistency and security across sessions.

### 1.6 Logging

Includes structured terminal logging for all key steps, making debugging and tracking straightforward.

---

## 2. Installation

### 2.1 Prerequisites

Ensure the following are installed:

* Python 3.10+
* pip
* Virtual environment tool (`venv` or `virtualenv`)

---

### 2.2 Environment Configuration

Create a `.env` file in the project root with your API keys.
You can refer to the `.env_example` file included in the project for required variables.

---

### 2.3 Setup Steps

```bash
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

1. Enter cv path
2. Enter an **interview topic** (e.g., “Python”, “R Language”, “Machine Learning”).
3. Choose the **question type** – `broad`, `narrow_up`, or `follow_up`.

The system will then conduct a complete AI-driven interview session directly in the terminal.


