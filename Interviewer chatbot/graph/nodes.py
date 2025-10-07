

# import json
# from typing import Dict
# from graph.state import InterviewState
# from services.gemini_client import gemini_client
# from services.tavily_client import tavily_service
# from config.prompts import *  # Import all prompts
# def setup_node(state: InterviewState) -> InterviewState:
#     print(" Welcome to the AI Interviewer (Question Evaluation Mode)!")
#     topic = input("Enter the interview topic: ").strip()
    
#     print("\nChoose question style:")
#     print("1. Broad, follow-up questions (general, builds on previous answers)")
#     print("2. Narrow, follow-up questions (specific, probes details from previous answers)")
#     print("3. Broad, non-follow-up questions (general, new topic aspects)")
#     print("4. Narrow, non-follow-up questions (specific, new topic aspects)")
#     choice = input("Enter choice (1-4): ").strip()
#     question_type_map = {
#         "1": "broad_followup",
#         "2": "narrow_followup",
#         "3": "broad_nonfollowup",
#         "4": "narrow_nonfollowup"
#     }
#     question_type = question_type_map.get(choice, "broad_followup")

#     content_list = tavily_service.search(f"key areas for interview on: {topic}")
#     initial_messages = [{"role": "user", "content": f"Interview topic: {topic}"}]

# #     prompt_question = f"""
# # You are an expert interviewer. Using the following reference content:
# # {content_list}

# # Generate question #1 for the topic: {topic}.
# # {'Ask a broad, general question.' if question_type.startswith('broad') else 'Ask a specific, detailed question.'}
# # Return ONLY the question text.
# # """
#     prompt_question = get_setup_prompt(content_list, topic, question_type)
#     first_question = gemini_client.generate_content(prompt_question) or "Tell me about your interest in this topic."

#     return {
#         **state,
#         "topic": topic,
#         "content": content_list,
#         "messages": initial_messages,
#         "step": 0,
#         "questions": [],
#         "answers": [],
#         "feedback": [],
#         "current_question": first_question,
#         "question_type": question_type
#     }

# def get_answer_node(state: InterviewState) -> InterviewState:
#     current_q = state.get("current_question")
#     if not current_q:
#         raise ValueError("No current_question found in state.")

#     print(f"\n❓ Generated Question {state['step'] + 1}: {current_q}\n")
#     answer = input("💭 Your answer: ").strip()

#     new_messages = state['messages'] + [
#         {"role": "interviewer", "content": current_q},
#         {"role": "candidate", "content": answer}
#     ]

#     return {
#         **state,
#         "current_answer": answer,
#         "messages": new_messages,
#         "questions": state['questions'] + [current_q],
#         "answers": state['answers'] + [answer]
#     }

# def evaluate_question_node(state: InterviewState) -> InterviewState:
#     transcript = ""
#     for i in range(len(state['questions']) - 1):
#         q = state['questions'][i]
#         a = state['answers'][i]
#         f = state['feedback'][i] if i < len(state['feedback']) else {}
#         transcript += f"Previous Q{i+1}: {q}\nPrevious A{i+1}: {a}\nPrevious Feedback: {f.get('question_feedback', {}).get('feedback', '')}\n\n"

#     last_q = state['questions'][-1]
#     last_a = state['answers'][-1]
#     full_messages = json.dumps(state['messages'])
#     full_content = "\n".join(state['content'])

# #     question_prompt = f"""
# # You are an expert interviewer. Evaluate the following question for its clarity, relevance, and ability to probe understanding, considering the ENTIRE interview history, accumulated context, all previous messages, questions, answers, and feedback.

# # Full Interview History (Messages): {full_messages}
# # Accumulated Context (Search Snippets): {full_content}
# # Previous Q&A Transcript: {transcript}
# # Current Question: {last_q}
# # Current Candidate Answer: {last_a}

# # Provide a rating (1-10) for question quality and 2-3 sentence feedback. Consider how well this question builds on prior answers, avoids repetition, incorporates context, and advances the topic.
# # Return in JSON format:
# # {{
# #     "rating": 0,
# #     "feedback": "..."
# # }}
# # """
#     question_prompt = get_question_evaluation_prompt(full_messages, full_content, transcript, last_q, last_a)
#     question_feedback_text = gemini_client.generate_content(question_prompt)
#     question_feedback = gemini_client.safe_parse_json(question_feedback_text, {"rating": 0, "feedback": "Failed to generate question feedback."})

# #     answer_prompt = f"""
# # You are an expert interviewer. Evaluate the following candidate answer for its clarity, relevance, depth, and alignment with the question, considering the ENTIRE interview history and context.

# # Full Interview History (Messages): {full_messages}
# # Accumulated Context (Search Snippets): {full_content}
# # Previous Q&A Transcript: {transcript}
# # Current Question: {last_q}
# # Current Candidate Answer: {last_a}

# # Provide a rating (1-10) for answer quality and 2-3 sentence feedback. Highlight strengths and areas for improvement.
# # Return in JSON format:
# # {{
# #     "rating": 0,
# #     "feedback": "..."
# # }}
# # """
#     answer_prompt = get_answer_evaluation_prompt(full_messages, full_content, transcript, last_q, last_a)
#     answer_feedback_text = gemini_client.generate_content(answer_prompt)
#     answer_feedback = gemini_client.safe_parse_json(answer_feedback_text, {"rating": 0, "feedback": "Failed to generate answer feedback."})

#     feedback = {
#         "question_feedback": question_feedback,
#         "answer_feedback": answer_feedback
#     }
    
#     # Only show minimal progress indicator during the interview
#     print(f"✅ Question {state['step'] + 1} evaluated. Moving to next question...")

#     return {
#         **state,
#         "feedback": state['feedback'] + [feedback],
#         "step": state['step'] + 1
#     }

# def generate_question_node(state: InterviewState) -> InterviewState:
#     updated_content = state['content']
#     question_type = state['question_type']
#     is_followup = "followup" in question_type
#     is_broad = question_type.startswith("broad")

#     if state['step'] > 0:
#         last_q = state['questions'][-1]
#         last_a = state['answers'][-1]
#         tavily_results = tavily_service.search(f"{state['topic']} interview context: Q: {last_q} A: {last_a}")
#         updated_content += tavily_results

#     prompt_instruction = ""
#     if is_followup:
#         prompt_instruction = f"Generate a {'broad, general' if is_broad else 'specific, detailed'} follow-up question that directly probes details from the previous answer: {state['answers'][-1] if state['answers'] else ''}."
#     else:
#         prompt_instruction = f"Generate a {'broad, general' if is_broad else 'specific, detailed'} question that explores a new aspect of the topic, independent of the previous answer."

#     prompt_question = f"""
# You are an expert interviewer. Using the following reference content:
# {updated_content}

# {prompt_instruction}
# Topic: {state['topic']}
# Question number: {state['step'] + 1}
# Return ONLY the question text.
# """
#     question = gemini_client.generate_content(prompt_question) or f"Tell me more about {state['topic']}."

#     return {
#         **state,
#         "current_question": question,
#         "content": updated_content
#     }

# def final_evaluation_node(state: InterviewState) -> InterviewState:
#     print("\n📊 Generating final evaluation of all questions...")
#     transcript = ""
#     for i, (q, a, f) in enumerate(zip(state['questions'], state['answers'], state['feedback']), 1):
#         transcript += f"Q{i}: {q}\nA{i}: {a}\nQuestion Feedback: {f['question_feedback']['feedback']} (Rating: {f['question_feedback']['rating']})\nAnswer Feedback: {f['answer_feedback']['feedback']} (Rating: {f['answer_feedback']['rating']})\n\n"

#     prompt = f"""
# Based on this transcript, produce a JSON summary evaluation of the questions:
# {transcript}

# JSON format ONLY:
# {{
#     "overall_quality": 0-10,
#     "strengths": ["..."],
#     "areas_for_improvement": ["..."],
#     "recommendation": "keep/revise/remove",
#     "final_feedback": "..."
# }}
# """
#     response_text = gemini_client.generate_content(prompt)
#     evaluation = gemini_client.safe_parse_json(response_text, {"overall_quality": 0, "recommendation": "revise", "final_feedback": "Failed to generate evaluation."})

#     return {**state, "final_evaluation": evaluation}

# def display_results_node(state: InterviewState) -> InterviewState:
#     print("\n" + "="*60)
#     print(" INTERVIEW COMPLETE - FINAL REPORT")
#     print("="*60)
#     print(f"\n Topic: {state['topic']}")
    
#     # Display all questions and answers first
#     print("\n📝 INTERVIEW TRANSCRIPT:")
#     print("-" * 40)
#     for i, (q, a) in enumerate(zip(state['questions'], state['answers']), 1):
#         print(f"\nQ{i}: {q}")
#         print(f"A{i}: {a}")
    
#     # Display detailed feedback for all questions
#     print("\n\n📊 DETAILED FEEDBACK:")
#     print("-" * 40)
#     for i, (q, a, f) in enumerate(zip(state['questions'], state['answers'], state['feedback']), 1):
#         print(f"\n{'='*50}")
#         print(f"QUESTION {i} ANALYSIS:")
#         print(f"{'='*50}")
#         print(f"Question: {q}")
#         print(f"Answer: {a}")
#         print(f"\nQuestion Feedback: {f['question_feedback']['feedback']}")
#         print(f"Question Rating: {f['question_feedback']['rating']}/10")
#         print(f"\nAnswer Feedback: {f['answer_feedback']['feedback']}")
#         print(f"Answer Rating: {f['answer_feedback']['rating']}/10")

#     # Display final evaluation
#     print("\n\n🏁 FINAL EVALUATION:")
#     print("-" * 40)
#     eval_data = state['final_evaluation']
#     if "error" in eval_data:
#         print(" Could not parse evaluation:", eval_data["error"])
#     else:
#         print(f"Overall Quality: {eval_data.get('overall_quality', 'N/A')}/10")
#         print(f"\nStrengths:")
#         for strength in eval_data.get('strengths', []):
#             print(f"  • {strength}")
#         print(f"\nAreas for Improvement:")
#         for area in eval_data.get('areas_for_improvement', []):
#             print(f"  • {area}")
#         print(f"\nRecommendation: {eval_data.get('recommendation', 'N/A')}")
#         print(f"\nFinal Feedback: {eval_data.get('final_feedback', 'N/A')}")

#     # Save results
#     with open("interview_results.json", "w") as f:
#         json.dump(state, f, indent=2)
#     print(f"\n💾 Results saved to 'interview_results.json'")
    
#     return state

import json
from typing import Dict
from graph.state import InterviewState
from services.gemini_client import gemini_client
from services.tavily_client import tavily_service
from config.prompts import *  # Import all prompts

def setup_node(state: InterviewState) -> InterviewState:
    print(" Welcome to the AI Interviewer (Question Evaluation Mode)!")
    topic = input("Enter the interview topic: ").strip()
    
    print("\nChoose question style:")
    print("1. Broad, follow-up questions (general, builds on previous answers)")
    print("2. Narrow, follow-up questions (specific, probes details from previous answers)")
    print("3. Broad, non-follow-up questions (general, new topic aspects)")
    print("4. Narrow, non-follow-up questions (specific, new topic aspects)")
    choice = input("Enter choice (1-4): ").strip()
    question_type_map = {
        "1": "broad_followup",
        "2": "narrow_followup",
        "3": "broad_nonfollowup",
        "4": "narrow_nonfollowup"
    }
    question_type = question_type_map.get(choice, "broad_followup")

    content_list = tavily_service.search(f"key areas for interview on: {topic}")
    initial_messages = [{"role": "user", "content": f"Interview topic: {topic}"}]

    # Use prompt template for first question generation
    prompt_question = get_setup_prompt(content_list, topic, question_type)
    first_question = gemini_client.generate_content(prompt_question) or "Tell me about your interest in this topic."

    return {
        **state,
        "topic": topic,
        "content": content_list,
        "messages": initial_messages,
        "step": 0,
        "questions": [],
        "answers": [],
        "feedback": [],
        "current_question": first_question,
        "question_type": question_type
    }

def get_answer_node(state: InterviewState) -> InterviewState:
    current_q = state.get("current_question")
    if not current_q:
        raise ValueError("No current_question found in state.")

    print(f"\n❓ Generated Question {state['step'] + 1}: {current_q}\n")
    answer = input("💭 Your answer: ").strip()

    new_messages = state['messages'] + [
        {"role": "interviewer", "content": current_q},
        {"role": "candidate", "content": answer}
    ]

    return {
        **state,
        "current_answer": answer,
        "messages": new_messages,
        "questions": state['questions'] + [current_q],
        "answers": state['answers'] + [answer]
    }

def evaluate_question_node(state: InterviewState) -> InterviewState:
    transcript = ""
    for i in range(len(state['questions']) - 1):
        q = state['questions'][i]
        a = state['answers'][i]
        f = state['feedback'][i] if i < len(state['feedback']) else {}
        transcript += f"Previous Q{i+1}: {q}\nPrevious A{i+1}: {a}\nPrevious Feedback: {f.get('question_feedback', {}).get('feedback', '')}\n\n"

    last_q = state['questions'][-1]
    last_a = state['answers'][-1]
    full_messages = json.dumps(state['messages'])
    full_content = "\n".join(state['content'])

    # Use prompt templates for evaluation
    question_prompt = get_question_evaluation_prompt(full_messages, full_content, transcript, last_q, last_a)
    question_feedback_text = gemini_client.generate_content(question_prompt)
    question_feedback = gemini_client.safe_parse_json(question_feedback_text, {"rating": 0, "feedback": "Failed to generate question feedback."})

    answer_prompt = get_answer_evaluation_prompt(full_messages, full_content, transcript, last_q, last_a)
    answer_feedback_text = gemini_client.generate_content(answer_prompt)
    answer_feedback = gemini_client.safe_parse_json(answer_feedback_text, {"rating": 0, "feedback": "Failed to generate answer feedback."})

    feedback = {
        "question_feedback": question_feedback,
        "answer_feedback": answer_feedback
    }
    
    # Only show minimal progress indicator during the interview
    print(f"✅ Question {state['step'] + 1} evaluated. Moving to next question...")

    return {
        **state,
        "feedback": state['feedback'] + [feedback],
        "step": state['step'] + 1
    }

def generate_question_node(state: InterviewState) -> InterviewState:
    updated_content = state['content']
    question_type = state['question_type']
    is_followup = "followup" in question_type
    is_broad = question_type.startswith("broad")

    if state['step'] > 0:
        last_q = state['questions'][-1]
        last_a = state['answers'][-1]
        tavily_results = tavily_service.search(f"{state['topic']} interview context: Q: {last_q} A: {last_a}")
        updated_content += tavily_results

    # Use prompt template functions for question generation
    prompt_instruction = get_question_instruction(
        question_type, is_followup, is_broad, 
        state['answers'][-1] if state['answers'] else ""
    )
    
    prompt_question = get_question_generation_prompt(
        updated_content, prompt_instruction, state['topic'], state['step']
    )
    
    question = gemini_client.generate_content(prompt_question) or f"Tell me more about {state['topic']}."

    return {
        **state,
        "current_question": question,
        "content": updated_content
    }

def final_evaluation_node(state: InterviewState) -> InterviewState:
    print("\n📊 Generating final evaluation of all questions...")
    transcript = ""
    for i, (q, a, f) in enumerate(zip(state['questions'], state['answers'], state['feedback']), 1):
        transcript += f"Q{i}: {q}\nA{i}: {a}\nQuestion Feedback: {f['question_feedback']['feedback']} (Rating: {f['question_feedback']['rating']})\nAnswer Feedback: {f['answer_feedback']['feedback']} (Rating: {f['answer_feedback']['rating']})\n\n"

    # Use prompt template for final evaluation
    prompt = get_final_evaluation_prompt(transcript)
    response_text = gemini_client.generate_content(prompt)
    evaluation = gemini_client.safe_parse_json(response_text, {"overall_quality": 0, "recommendation": "revise", "final_feedback": "Failed to generate evaluation."})

    return {**state, "final_evaluation": evaluation}

def display_results_node(state: InterviewState) -> InterviewState:
    print("\n" + "="*60)
    print(" INTERVIEW COMPLETE - FINAL REPORT")
    print("="*60)
    print(f"\n Topic: {state['topic']}")
    
    # Display all questions and answers first
    print("\n📝 INTERVIEW TRANSCRIPT:")
    print("-" * 40)
    for i, (q, a) in enumerate(zip(state['questions'], state['answers']), 1):
        print(f"\nQ{i}: {q}")
        print(f"A{i}: {a}")
    
    # Display detailed feedback for all questions
    print("\n\n📊 DETAILED FEEDBACK:")
    print("-" * 40)
    for i, (q, a, f) in enumerate(zip(state['questions'], state['answers'], state['feedback']), 1):
        print(f"\n{'='*50}")
        print(f"QUESTION {i} ANALYSIS:")
        print(f"{'='*50}")
        print(f"Question: {q}")
        print(f"Answer: {a}")
        print(f"\nQuestion Feedback: {f['question_feedback']['feedback']}")
        print(f"Question Rating: {f['question_feedback']['rating']}/10")
        print(f"\nAnswer Feedback: {f['answer_feedback']['feedback']}")
        print(f"Answer Rating: {f['answer_feedback']['rating']}/10")

    # Display final evaluation
    print("\n\n🏁 FINAL EVALUATION:")
    print("-" * 40)
    eval_data = state['final_evaluation']
    if "error" in eval_data:
        print(" Could not parse evaluation:", eval_data["error"])
    else:
        print(f"Overall Quality: {eval_data.get('overall_quality', 'N/A')}/10")
        print(f"\nStrengths:")
        for strength in eval_data.get('strengths', []):
            print(f"  • {strength}")
        print(f"\nAreas for Improvement:")
        for area in eval_data.get('areas_for_improvement', []):
            print(f"  • {area}")
        print(f"\nRecommendation: {eval_data.get('recommendation', 'N/A')}")
        print(f"\nFinal Feedback: {eval_data.get('final_feedback', 'N/A')}")

    # Save results
    with open("interview_results.json", "w") as f:
        json.dump(state, f, indent=2)
    print(f"\n💾 Results saved to 'interview_results.json'")
    
    return state