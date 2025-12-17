import streamlit as st
import requests

API_URL = "http://localhost:8000"

st.set_page_config(page_title="RAG PDF Agent", page_icon="📄")

st.title("📄 RAG PDF Agent")
st.markdown("Upload a PDF and ask questions about its content.")

uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])

query = st.text_input("Enter your question about the PDF")

if st.button("Ask", disabled=not (uploaded_file and query)):
    if uploaded_file and query:
        with st.spinner("Processing..."):
            try:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                params = {"query": query}

                response = requests.post(f"{API_URL}/chat", files=files, params=params)

                if response.status_code == 200:
                    data = response.json()
                    st.subheader("Response")
                    st.write(data["response"])
                else:
                    st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
            except requests.exceptions.ConnectionError:
                st.error("Cannot connect to API. Make sure the server is running on port 8000.")
            except Exception as e:
                st.error(f"Error: {str(e)}")
