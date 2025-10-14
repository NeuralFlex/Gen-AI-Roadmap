
# Interviewer Chatbot

A **LangGraph** system that conducts **AI-driven interviews in the terminal**.  
It dynamically generates and evaluates interview questions using **Gemini** and **Tavily** APIs, managing the conversation flow through a **stateful interview graph**.

---

## Index

1. **Core Components**  
2. **Installation**  
   2.1 Prerequisites  
   2.2 Environment Configuration  
   2.3 Setup Steps  
   2.4 Running the Application  
3. **Project Structure**  
4. **Usage Workflow**

---

## 1. Core Components

### 1.1 Interview Graph (LangGraph)
Implements the main interview logic as a directed, stateful graph defined in `graph/graph.py`.

The graph consists of the following nodes:

- **Setup Node** – initializes the interview topic, question type, and parameters.  
- **Generate Question Node** – generates a new question using the selected topic and type (broad, narrow_up, follow_up, etc.).  
- **Get Answer Node** – collects the user's input from the terminal.  
- **Evaluate Question Node** – evaluates the response using the Gemini model.  
- **Final Evaluation Node** – summarizes candidate performance and feedback.  
- **Display Results Node** – displays interview results in the terminal.

Graph transitions and conditions are defined through `StateGraph` in `graph/graph.py`.

---

### 1.2 State Management

`graph/state.py` defines a `TypedDict` named **InterviewState** that tracks all key variables throughout the session.

| Field | Description |
|-------|--------------|
| `topic` | Current interview topic |
| `content` | Contextual or reference content |
| `questions` | List of all asked questions |
| `answers` | List of user answers |
| `feedback` | Evaluations and reasoning |
| `current_question` | Currently active question |
| `current_answer` | Most recent answer |
| `step` | Current interview step count |
| `max_questions` | Total questions per session |
| `final_evaluation` | Overall feedback summary |
| `messages` | Conversation history |
| `question_type` | Question style (broad, narrow_up, follow_up, etc.) |

---

### 1.3 Gemini & Tavily Integration

- **`services/gemini_client.py`** → Handles interaction with the Gemini API for question generation and answer evaluation.  
- **`services/tavily_client.py`** → Fetches external reference content or related context for Retrieval-Augmented Generation (RAG).

---

### 1.4 Configuration & Prompts

- **`config/prompts.py`** → Contains prompt templates used for interviews and evaluations.  
- **`config/settings.py`** → Loads environment variables (e.g., API keys, default settings).

---

### 1.5 Logging

Structured logging is handled by **`utils/logger.py`**, which provides timestamped logs for all major actions and state transitions.

---

## 2. Installation

Local setup for development and terminal-based testing.

---

### 2.1 Prerequisites

#### System Requirements
- Python 3.9 or higher  
- Git

#### External Services
- **Gemini API key**  
- **Tavily API key** (optional, for contextual retrieval)

---

### 2.2 Environment Configuration

Before running the project, create an environment file:

```bash
cp config/.env.example config/.env
````

Then fill in your API keys and configurations inside `config/.env`, e.g.:

```bash
GEMINI_API_KEY=your_gemini_api_key
TAVILY_API_KEY=your_tavily_api_key
```

---

### 2.3 Setup Steps

#### 2.3.1 Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows
```

#### 2.3.2 Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 2.4 Running the Application

Run the chatbot directly in the terminal:

```bash
python main.py
```

When prompted, enter:

1. The **interview topic** (e.g., "Python programming", "R language")
2. The **question type** (e.g., "broad", "narrow_up", "follow_up") in number (1,2,3,4)

The system will then conduct an interactive interview session right in your terminal.

---

## 3. Project Structure

```
interviewer_chatbot/
│
├── config/
│   ├── prompts.py           # Prompt templates
│   ├── settings.py          # Environment variables and configuration
│
├── graph/
│   ├── graph.py             # LangGraph structure and node transitions
│   ├── nodes.py             # Logic for each node
│   ├── state.py             # InterviewState schema
│
├── models/
│   ├── gemini_model.py      # Gemini model helper classes
│
├── services/
│   ├── gemini_client.py     # Handles Gemini API communication
│   ├── tavily_client.py     # Optional RAG integration via Tavily
│
├── utils/
│   ├── logger.py            # Logging configuration
│
├── notebooks/               # Jupyter notebooks (optional, for testing)
├── main.py                  # Entry point for terminal chatbot
├── requirements.txt         # Python dependencies
└── README.md
```

---

## 4. Usage Workflow

### 4.1 Starting an Interview

Run the chatbot and follow the prompts:

```bash
python main.py
```

Example interaction:

```
Enter interview topic: Python programming
Select question type (broad, narrow_up, follow_up): broad

💬 Interviewer: Could you explain what Python is commonly used for?
👤 You: It’s a general-purpose language used for automation and data science.

💬 Interviewer: Great! Can you elaborate on a project where you used Python?
👤 You: I used it to automate data collection from APIs.

✅ Interview completed!
```

---

### 4.2 Logs & Debugging

All logs are printed in the terminal.
To enable more detailed logs, update the logging level in `utils/logger.py`.

---

### 4.3 Extending the Interview Graph

You can add new nodes or transitions to customize the interview flow.

Steps:

1. Define a new node function in `graph/nodes.py`
2. Add it to the graph builder in `graph/graph.py` using `builder.add_node()` and `builder.add_edge()`

Example:

```python
builder.add_node("new_node", new_node_function)
builder.add_edge("existing_node", "new_node")
```

---

✅ **Ready to Use!**

You can now run and extend your **LangGraph-powered terminal interview chatbot**
to support different interview types, topics, and logic flows — all from your terminal.

---

```

---

```
