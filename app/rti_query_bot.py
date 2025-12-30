"""
RTI Query Bot - General RTI Knowledge Assistant
Handles general questions about RTI Act, procedures, and guidelines
"""

from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

SYSTEM_PROMPT = """
You are an expert RTI (Right to Information) Act assistant for India.

Your role is to help citizens understand:
- The RTI Act 2005 and their rights under it
- How to file RTI applications
- Who can file RTI and to which authorities
- RTI application fees and exemptions
- Appeal procedures and timelines
- Common reasons for information denial
- Tips for drafting effective RTI applications
- State-specific RTI guidelines when asked
- RTI online filing procedures

Guidelines:
✅ Provide accurate information about RTI Act 2005
✅ Explain procedures in simple, easy-to-understand language
✅ Give practical examples when helpful
✅ Cite relevant sections of RTI Act when appropriate
✅ Be encouraging and supportive to citizens exercising their rights

❌ Do NOT provide legal advice (suggest consulting a lawyer for legal matters)
❌ Do NOT make up information - say "I'm not sure" if uncertain
❌ Do NOT help draft applications - just explain the process
❌ Do NOT answer unrelated questions about other topics

Keep responses concise but informative. Use bullet points for clarity.
"""


def answer_rti_query(question: str, chat_history: list = None) -> str:
    """
    Answer general RTI-related questions.
    
    Args:
        question: User's question about RTI
        chat_history: Previous conversation history (list of dicts with 'role' and 'content')
    
    Returns:
        Bot's response as string
    """
    try:
        # Build conversation context (user and model messages only)
        messages = []
        
        # Add chat history if provided
        if chat_history:
            for msg in chat_history:
                if msg["role"] == "user":
                    messages.append({
                        "role": "user",
                        "parts": [{"text": msg["content"]}]
                    })
                else:  # bot/assistant messages
                    messages.append({
                        "role": "model",
                        "parts": [{"text": msg["content"]}]
                    })
        
        # Add current question
        messages.append({
            "role": "user",
            "parts": [{"text": question}]
        })
        
        # Get response from Gemini with system instruction in config
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=messages,
            config={
                "system_instruction": SYSTEM_PROMPT
            }
        )
        
        return response.text
    
    except Exception as e:
        return f"Sorry, I encountered an error: {str(e)}\n\nPlease try rephrasing your question."


def get_welcome_message() -> str:
    """Return welcome message for RTI query bot."""
    return """
👋 **Welcome to RTI Knowledge Assistant!**

I can help you with:
- Understanding the RTI Act 2005
- How to file RTI applications
- RTI fees, exemptions, and timelines
- Appeal procedures
- Tips for effective RTI requests

Ask me anything about RTI!
"""


# Example usage
if __name__ == "__main__":
    # Test the bot
    print(get_welcome_message())
    
    test_question = "What is the RTI Act and who can file an RTI application?"
    response = answer_rti_query(test_question)
    print(f"\nQ: {test_question}")
    print(f"A: {response}")
