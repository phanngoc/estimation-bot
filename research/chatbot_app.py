import streamlit as st
import os
from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage
)

# Load environment variables
load_dotenv()

# Set up OpenAI API key
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# Initialize ChatOpenAI
chat = ChatOpenAI(temperature=0.7)

# Streamlit UI
st.title("🤖 AI Chatbot")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        SystemMessage(content="You are a helpful AI assistant.")
    ]

# Display chat history
for message in st.session_state.messages[1:]:
    if isinstance(message, HumanMessage):
        with st.chat_message("user"):
            st.write(message.content)
    elif isinstance(message, AIMessage):
        with st.chat_message("assistant"):
            st.write(message.content)

# Chat input
if prompt := st.chat_input("How can I help you today?"):
    # Add user message to chat history
    st.session_state.messages.append(HumanMessage(content=prompt))
    
    with st.chat_message("user"):
        st.write(prompt)

    # Get AI response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = chat(st.session_state.messages)
            st.write(response.content)
            st.session_state.messages.append(AIMessage(content=response.content))
