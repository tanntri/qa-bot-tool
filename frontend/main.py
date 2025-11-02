import streamlit as st
import requests
import os
from dotenv import load_dotenv


load_dotenv()
# Streamlit App Configuration
st.set_page_config(page_title="Internal QA Tool", layout="centered")

# Define API endpoint
API_URL = os.getenv("API_URL", "http://localhost:8000")

# Streamlit UI Elements
st.title("QA Chatbot")
st.write("Internal QA Tool for questions about known bugs or user feedback.")

# Input box for user messages
user_input = st.text_area("Message:", height=150, placeholder="Type your message here...")

# Button to send the query
if st.button("Submit"):
    if user_input.strip():
        try:
            # Send the input to the FastAPI backend
            payload = {"question": user_input.strip()}
            response = requests.post(API_URL, json=payload)
            
            # Display the response
            if response.status_code == 200:
                response_data = response.json()
                
                # Check for error in response
                if "error" in response_data and response_data.get("error"):
                    st.error(response_data["error"])
                elif response_data.get("success"):
                    # Display the answer from ChatResponse model
                    st.subheader("Response:")
                    st.markdown(f"**Answer:** {response_data['answer']}")
                else:
                    st.warning("No response found in the agent output.")
            else:
                st.error(f"Request failed with status code {response.status_code}.")
                
        except Exception as e:
            st.error(f"An error occurred: {e}")
    else:
        st.warning("The field can't be empty.")