import streamlit as st
### MONGO DB LIBRARIES
from bson import ObjectId
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
### DASHBOARD LIBRARIES
import datetime
import random
import time
from uuid import uuid1
import os
import json
from dotenv import load_dotenv
from rag import Chatbot

from config.database import MongoDatabaseConnector
from pinecone import Pinecone

# Setting up webpage attributes
st.set_page_config(page_title="NewsRAG", page_icon=":newspaper:", layout="centered", initial_sidebar_state="auto",
                   menu_items={
                       'About': "# Applicazione di fact checking \n"
                                "Ricevi informazioni da testate giornalistiche attendibili.\n"
                                "### Articoli supportati dal sistema:\n"
                                "- Periodo: 23/02/2022 - 30/04/2024\n"
                                "- Origine articoli: Italia"
                   })


@st.cache_resource(show_spinner=False)
def load_data(session_id):
    print(session_id)
    with st.spinner(text="Loading and indexing the Streamlit docs – hang tight! This should take 1-2 minutes."):
        service_context = Chatbot(session_id=session_id, collection=collection,
                  MONGO_URI=MONGO_URI, MONGO_DB_NAME=MONGO_DB_NAME,
                  index=index
                  )
        return service_context

# .env load
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

## connessioni
connection = MongoDatabaseConnector(MONGO_URI)
db = connection[MONGO_DB_NAME]
collection = db['articles']
chat_collection = db['chat_histories']
# Send a ping to confirm a successful connection
try:
    connection.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    st.write(e)
# connect to index
# api_key = os.getenv("PINECONE_API_KEY")
pc = Pinecone(api_key=PINECONE_API_KEY)
index_name = 'newsrag'
index = pc.Index(index_name)

### Function----------------------------------------------------------------------------------------------------------------------
def response_generation(chatbot_instance, prompt):
    response = chatbot_instance.chat_rag_chain(prompt)
    return response
    
def print_sources(response):
    with st.expander("See explanation"):
        for rez in response['context']:
            st.write("Document id: ", rez.metadata['doc_id'], "  \n"
                    "Title : [{title}]({url})".format(title=collection.find_one({"_id": ObjectId(rez.metadata['doc_id'])}) \
                                            .get('title', 'URL not found'),
                                            url=collection.find_one({"_id": ObjectId(rez.metadata['doc_id'])}) \
                                            .get('url', 'URL not found')),
                    "  \n",
                    "Content: ",rez.page_content)

# Streamed response emulator
def stream_answer(answer):
    for word in answer.split():
        yield word + " "
        time.sleep(0.05)

def get_button_label(chat_id):
    first_message = list(chat_collection.find({'SessionId': chat_id}))[0]['History']
    first_message = json.loads(first_message)
    stringa = first_message['data']['content'][:25]+'...'
    return stringa, chat_id
###--------------------------------------------------------------------------------------------------------------------------------

st.title(
    "News RAG :newspaper: :speaking_head_in_silhouette: :fire:")

################################################ --- SIDEBAR FIELD ---
# Define the aggregation pipeline
pipeline = [
    {
        '$group': {
            '_id': None,
            'min_publish_date': {'$min': '$publish_date'},
            'max_publish_date': {'$max': '$publish_date'}
        }
    }
]

with st.sidebar:
    print_response_flag = st.checkbox("Report Sources content")
    st.write("Si consiglia per ogni nuovo argomento di iniziare una nuova chat")
    if st.button("New Chat"):
        
        st.session_state.session_id = str(uuid1())
        st.session_state.messages.clear()
    st.write("## Chat History")

# Initialize session state for session_id if it doesn't exist
if 'session_id' not in st.session_state:
    st.session_state.session_id = None

button_labels = []
label_dict = {}
# Populate button_labels and label_dict
for _id in list(chat_collection.distinct('SessionId')):
    button_label, session_id = get_button_label(_id)
    label_dict[button_label] = session_id
    button_labels.append(button_label)

# Create buttons in the sidebar and handle button clicks
for button_label in button_labels:
    if st.sidebar.button(button_label):
        st.session_state.session_id = label_dict[button_label]
        # print(type(st.session_state.session_id))
        st.session_state.messages.clear()

### instanziamo il chatbot
chatbot = load_data(str(st.session_state.session_id))


if st.session_state.session_id:
    chat_history = ""
    for record in chat_collection.find({'SessionId': st.session_state.session_id}):
        message = json.loads(record['History'])
        chat_record = "{type} : {message}  \n  \n".format(
            type=message['type'],
            message=message['data']['content']
        )
        chat_history += chat_record
        if chat_record.split()[0] == 'human':
            with st.chat_message("user"):
                st.markdown(message['data']['content'])
        else:
            with st.chat_message("assistant"):
                st.markdown(message['data']['content'])

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("Cosa vuoi sapere?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        ## gira il prompt all'llm
        response = response_generation(chatbot, prompt)
        st.write_stream(stream_answer(response['answer']))
        if print_response_flag == True:
            print_sources(response)
            
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response['answer']})