import os
import urllib.parse
from pathlib import Path
import sqlite3
import streamlit as st

from langchain_classic.agents import (AgentExecutor, create_tool_calling_agent, tool)
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.callbacks.streamlit import StreamlitCallbackHandler
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_groq import ChatGroq
from dotenv import load_dotenv, find_dotenv
from sqlalchemy import create_engine

# Load environment configurations
load_dotenv(find_dotenv())

st.set_page_config(page_title='LangChain: Chat with SQL DB', page_icon='🔥')
st.title('🔥 Query a database')

LOCAL_DB = 'USE_LOCALDB'
MYSQL = 'USE_MYSQL'

# Sidebar Navigation Options
radio_opt = ['Use SQLite 3 DB- student.db', 'Connect to your database [MySQL]']
selected_opt = st.sidebar.radio(label='Choose the DB you wish to chat with', options=radio_opt)

# Local connection placeholder initializations
mysql_host = None
mysql_user = None
mysql_password = None
mysql_db = None

if radio_opt.index(selected_opt) == 1:
    db_uri = MYSQL
    mysql_host = st.sidebar.text_input('Please, provide MySQL host')
    mysql_user = st.sidebar.text_input('Please, provide MySQL User')
    mysql_password = st.sidebar.text_input('Please, provide password', type='password')
    # Safe encoding for special characters like '@' in strings
    if mysql_password:
        mysql_password = urllib.parse.quote_plus(mysql_password)
    mysql_db = st.sidebar.text_input('Please, provide the database to use')
else:
    db_uri = LOCAL_DB

api_key = st.sidebar.text_input('Please, provide Groq API key', type='password')

if not api_key:
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        st.info("Please provide a Groq API key to proceed.")
        st.stop()

# Initialize modern ChatGroq client with tool support
llm = ChatGroq(groq_api_key=api_key, model_name='openai/gpt-oss-120b', streaming=True)

# Secure DB Configuration Function
@st.cache_resource(ttl='2h')
def configure_db(db_uri, host=None, user=None, password=None, database=None):
    if db_uri == LOCAL_DB:
        db_filepath = (Path(__file__).parent / 'student.db').absolute()
        creator = lambda: sqlite3.connect(f'file:{db_filepath}?mode=ro', uri=True)
        return SQLDatabase(create_engine('sqlite:///', creator=creator))
    elif db_uri == MYSQL:
        if not (host and user and password and database):
            st.error('Please, provide all MySQL connection details')
            st.stop()
        uri = f"mysql+mysqlconnector://{user}:{password}@{host}/{database}"
        return SQLDatabase(create_engine(uri))

# Setup target database instance
if db_uri == MYSQL:
    db = configure_db(db_uri, mysql_host, mysql_user, mysql_password, mysql_db)
else:
    db = configure_db(db_uri)

# Constructing Modern Native Tool Agent Framework
toolkit = SQLDatabaseToolkit(db=db, llm=llm)
tools = toolkit.get_tools()

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an advanced SQL expert. Use your tools to answer the user database questions accurately."),
    MessagesPlaceholder(variable_name="chat_history", optional=True),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

# Use native tool calling structure to avoid Groq validation API errors
agent = create_tool_calling_agent(llm=llm, tools=tools, prompt=prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)

# State Management for App Chats
if 'messages' not in st.session_state or st.sidebar.button('Clear Message History'):
    st.session_state['messages'] = [{'role': 'assistant', 'content': 'How may I help you?'}]

for msg in st.session_state['messages']:
    st.chat_message(msg['role']).write(msg['content'])

user_query = st.chat_input(placeholder='Query your database and ask anything...')

if user_query:
    st.session_state.messages.append({'role': 'user', 'content': user_query})
    st.chat_message('user').write(user_query)

    with st.chat_message('assistant'):
        streamlit_callback = StreamlitCallbackHandler(st.container())
        
        # Invoke executor passing modern prompt values
        response = agent_executor.invoke(
            {"input": user_query}, 
            {"callbacks": [streamlit_callback]}
        )
        
        output_text = response["output"]
        st.session_state.messages.append({'role': 'assistant', 'content': output_text})
        st.write(output_text)
