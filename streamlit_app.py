import streamlit as st
from openai import OpenAI
import requests
from bs4 import BeautifulSoup

st.title("🔍 New York Life Chatbot")

# Input API key
openai_api_key = st.secrets.get("openai", {}).get("token")
if not openai_api_key:
    openai_api_key = st.text_input("Enter your OpenAI API Key", type="password")

if not openai_api_key:
    st.stop()

client = OpenAI(api_key=openai_api_key)

# Define the function metadata
functions = [
    {
        "name": "search_newyorklife",
        "description": "Searches approved New York Life websites for information.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The topic to search."
                }
            },
            "required": ["query"]
        }
    }
]

# Function to perform the search
def search_newyorklife(query: str) -> str:
    url = f"https://www.newyorklife.com/search?q={query}"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    results = soup.find_all('p')
    return "\n\n".join([r.get_text() for r in results[:5]]) or "No relevant results found."

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
if prompt := st.chat_input("Ask me about New York Life"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Initial GPT call to decide if it wants to call the function
    messages = [{"role": "system", "content": "You are a helpful assistant who only uses newyorklife.com for info."}] + st.session_state.messages
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        functions=functions,
        function_call="auto"
    )

    message = response.choices[0].message
    if message.get("function_call"):
        function_name = message.function_call.name
        function_args = eval(message.function_call.arguments)
        result = search_newyorklife(**function_args)

        # Feed result back to GPT
        messages.append({"role": "assistant", "function_call": message.function_call})
        messages.append({"role": "function", "name": function_name, "content": result})
        response = client.chat.completions.create(model="gpt-4o", messages=messages)
        final_msg = response.choices[0].message.content
    else:
        final_msg = message.content

    with st.chat_message("assistant"):
        st.markdown(final_msg)
    st.session_state.messages.append({"role": "assistant", "content": final_msg})