from langchain.chains.history_aware_retriever import create_history_aware_retriever
from langchain.chains.retrieval import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

### Vector store
# from langchain_pinecone import PineconeVectorStore
from langchain_community.retrievers.pinecone_hybrid_search import PineconeHybridSearchRetriever

### message history
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_mongodb.chat_message_histories import MongoDBChatMessageHistory

### messages
from langchain_core.messages.ai import AIMessage
from langchain_core.messages.human import HumanMessage

### embeddings
from langchain_huggingface import HuggingFaceEmbeddings
from pinecone_text.sparse import BM25Encoder

### misc
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI #, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


class Chatbot():
    def __init__(self, session_id, collection,
                 MONGO_URI, MONGO_DB_NAME, index) -> None:
        self.session_id = session_id
        ## keys
        self.MONGO_URI = MONGO_URI
        self.MONGO_DB_NAME = MONGO_DB_NAME
        #-----------------
        self.collection = collection
        self.index = index
        # models
        self.sparse_encoder = BM25Encoder().default()
        self.embeddings = HuggingFaceEmbeddings(model_name='nickprock/sentence-bert-base-italian-xxl-uncased')
        self.llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
        # chain/text
        self.qa_prompt = self.build_prompt()
        self.retriever = self.build_retriever()
        pass

    def build_retriever(self, alpha=0.8, top_k=3):
        #### Definire Embedder ####
        retriever = PineconeHybridSearchRetriever(alpha=alpha, top_k=top_k,
        embeddings=self.embeddings, sparse_encoder=self.sparse_encoder,
        index=self.index
        )
        return retriever

    def build_prompt(prompt):
        ### Answer question ###
        system_prompt = (
            "You are an assistant for question-answering tasks. "
            "Use the following pieces of retrieved context to answer "
            "the question. If you don't know the answer, say that you "
            "don't know. Use three sentences maximum and keep the "
            "answer concise."
            "\n\n"
            "{context}"
        )
        qa_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )
        return qa_prompt
    

    def chat_rag_chain(self, question):
        contextualize_q_system_prompt = (
            "Given a chat history and the latest user question "
            "which might reference context in the chat history, "
            "formulate a standalone question which can be understood "
            "without the chat history. Do NOT answer the question, "
            "just reformulate it if needed and otherwise return it as is."
        )
        contextualize_q_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", contextualize_q_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )
        history_aware_retriever = create_history_aware_retriever(
            self.llm, self.retriever, contextualize_q_prompt
        )
        question_answer_chain = create_stuff_documents_chain(self.llm, self.qa_prompt)
        rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
        conversational_rag_chain = RunnableWithMessageHistory(
            rag_chain,
            lambda session_id: MongoDBChatMessageHistory(
                session_id=session_id,
                connection_string=self.MONGO_URI,
                database_name=self.MONGO_DB_NAME,
                collection_name="chat_histories",
            ),
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="answer",
        )
        result = conversational_rag_chain.invoke(
                    {"input": question },
                    config={
                        "configurable": {"session_id": self.session_id}
                    }, 
            )
        return result
