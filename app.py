import os
import re
import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from neo4j import GraphDatabase




os.environ["GOOGLE_API_KEY"] = "AIzaSyDuNUB-DumIHOhRj0d3WXz6nmtzLUWvbak"




NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "MahletAmenu16@"

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def run_cypher_query(query):
    with driver.session() as session:
        result = session.run(query)
        return [record.data() for record in result]




st.set_page_config(page_title="📚 Ask the Books Database", page_icon="📖", layout="centered")
st.title("📚 Ask About Authors & Books")




if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "selected_question" not in st.session_state:
    st.session_state.selected_question = ""
if "question_count" not in st.session_state:
    st.session_state.question_count = 0




llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0,
    google_api_key=os.environ["GOOGLE_API_KEY"]
)




cypher_prompt = PromptTemplate(
    input_variables=["question"],
    template="""
        You are an assistant that converts natural language questions into Cypher queries
        for a Neo4j database with Authors and Books.

        Schema:
        (:Author {{name, birthYear}})-[:WROTE]->(:Book {{title, published, rating, reviewCount, good, genre}})

        Question: {question}
        Cypher Query:
        """
)

answer_prompt = PromptTemplate(
    input_variables=["question", "results"],
    template="""
        You are a helpful assistant. Based on the user's question and the database results,
        respond in natural language.

        Question: {question}
        Results: {results}

        Answer:
        """
)



st.sidebar.title("💡 Quick Questions")
st.sidebar.markdown("Click a question to fill the box:")

suggestions = [
    "Which books are good?",
    "Who wrote '1984'?",
    "List all authors born before 1950",
    "Which books have a rating above 4?",
    "Show books with more than 100 reviews",
    "What did Harper Lee write?",
    "Find authors who wrote multiple books",
    "Which books are in the 'Fantasy' genre?",
    "Show books published before 1950",
    "Which author wrote the most books?"
]

for question in suggestions:
    if st.sidebar.button(question):
        st.session_state.selected_question = question

if st.sidebar.button("Reset Chat"):
    st.session_state.chat_history = []
    st.session_state.selected_question = ""
    st.session_state.question_count = 0

st.sidebar.markdown("---")
st.sidebar.markdown("🔍 Powered by Gemini + Neo4j")



default_input = st.session_state.selected_question if st.session_state.selected_question else ""
with st.form("ask_form", clear_on_submit=True):
    user_question = st.text_input("🗣️ Ask a question about authors and books:", value=default_input)
    submitted = st.form_submit_button("Ask")

if submitted and user_question.strip():
    with st.spinner("🤖 Thinking..."):
        # Step 1: Generate Cypher query
        raw_query = llm.predict(cypher_prompt.format(question=user_question)).strip()
        cypher_query = re.sub(r"^```cypher|```$", "", raw_query).strip()

        # Step 2: Run Cypher query
        try:
            results = run_cypher_query(cypher_query)
            if results:
                # Step 3: Ask Gemini to summarize results
                answer = llm.predict(answer_prompt.format(
                    question=user_question,
                    results=str(results)
                )).strip()

                # Step 4: Save to chat history
                st.session_state.chat_history.append({
                    "question": user_question,
                    "answer": answer
                })
                st.session_state.question_count += 1
                st.success(answer)
            else:
                st.session_state.chat_history.append({
                    "question": user_question,
                    "answer": "No results found."
                })
                st.session_state.question_count += 1
                st.info("No results found.")
        except Exception as e:
            st.session_state.chat_history.append({
                "question": user_question,
                "answer": "❌ Something went wrong while answering your question."
            })
            st.session_state.question_count += 1
            st.error("❌ Something went wrong while answering your question.")

    st.session_state.selected_question = ""


if st.session_state.question_count > 1:
    with st.expander("💬 Show Chat History"):
        for entry in reversed(st.session_state.chat_history[:-1]):
            st.markdown(f"**You:** {entry['question']}")
            st.markdown(f"**Gemini:** {entry['answer']}")
            st.markdown("---")
