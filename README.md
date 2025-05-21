# 📰 Fact-Checking through Q&A using Retrieval Augmented Generation (RAG)

> Final project for the Big Data Engineering course – Computer Engineering Degree, Polytechnic School of Basic Sciences, Academic Year 2023/2024

## 📚 Project Description

This project implements an advanced **fact-checking system** using **Large Language Models (LLMs)** in combination with **Retrieval-Augmented Generation (RAG)** techniques. It enables the verification of the truthfulness of news statements by cross-referencing a large corpus of Italian news articles.

### ✅ Features
- Automatic fact-checking via chatbot
- Interactive analytics dashboard
- Streamlit-based user interface
- Keyword and topic extraction from news content

---

## 🧱 Architecture Overview

### 🗂 Dataset

- **Source**: [WorldNewsAPI](https://worldnewsapi.com/)
- **Language**: Italian 🇮🇹
- **Collected Articles**: ~120,000 (reduced to 31,000 for storage limits)
- **Time Range**: March 2022 – April 2024
- **News Outlets**:
  - ANSA
  - Il Sole 24 Ore
  - Repubblica
  - Il Mattino

### ⚙️ Preprocessing Pipeline

1. **Metadata Extraction**
   - Author name via regex
   - News category from URL
   - Publisher from domain
2. **Text Cleaning**
   - Accent and punctuation removal
   - Lowercasing, stopword removal
   - Lemmatization
3. **Information Extraction**
   - Keywords with [KeyBERT](https://github.com/MaartenGr/KeyBERT)
   - Topics with [BERTopic](https://github.com/MaartenGr/BERTopic)

---

## 💾 Data Storage

| Component     | Technology       | Purpose                         |
|---------------|------------------|----------------------------------|
| Document DB   | MongoDB Atlas    | Stores raw and processed articles |
| Vector DB     | Pinecone         | Stores text chunk embeddings      |

- Articles are split into chunks of 300 tokens
- Embeddings are created using:
  - Dense: `sentence-bert-base-italian-xxl-uncased`
  - Sparse: BM25 algorithm
- An internal log ensures synchronization between MongoDB and Pinecone

---

## 🤖 Chatbot & RAG Pipeline

### 💬 Language Model

- **Model**: `gpt-3.5-turbo` (OpenAI)
- **Rationale**:
  - Supports large context windows (16,385 tokens)
  - High-quality pretrained model with good domain coverage
  - Fast API-based generation

### 🔍 Retrieval Strategy

- **Hybrid Search**: Combines dense and sparse (keyword) vectors
- **Vector Scaling**: Controlled by α ∈ [0, 1]

- **Retriever**: Implemented using Langchain's `PineconeHybridSearch`

### 🧠 Generation Logic

- Uses the retrieved documents + chat history + current question as prompt context
- Includes a summarization mechanism to optimize token usage
- Persisted chat logs in MongoDB allow conversation recall

---

## 📊 Analytics Dashboard

Implemented using **Streamlit**, enabling users to explore and filter the dataset.

### 🔎 Available Insights

1. **Article Distribution Over Time**  
 Monthly distribution of published articles.

2. **Keyword Trends**  
 Top keywords and their time-based frequency.

3. **Author Analytics**  
 - Number of articles by publisher and category
 - WordCloud of writing style
 - Placeholder biography and contact links

4. **BERTopic Visualizations**  
 - Topic distribution across documents (2D embedding plot)  
 - Top words for each topic with c-TF-IDF scores

---

## 🚀 Getting Started

### 🧰 Prerequisites

- Python ≥ 3.9
- Accounts:
- [MongoDB Atlas](https://www.mongodb.com/atlas/database)
- [Pinecone](https://www.pinecone.io/)
- [OpenAI API Key](https://platform.openai.com/account/api-keys)
- Python libraries:
- `streamlit`, `langchain`, `bertopic`, `keybert`, `sentence-transformers`, `spacy`, `wordcloud`, `hdbscan`, `umap-learn`, etc.

### 🔧 Installation

```bash
git clone https://github.com/<your-org>/fact-checking-rag.git
cd fact-checking-rag
pip install -r requirements.txt


📁 fact-checking-rag/
├── app.py                     # Main Streamlit application
├── rag_pipeline.py           # RAG logic: retrieval and generation
├── embeddings/               # Chunking and embedding processing
├── analytics/                # MongoDB analytics scripts
├── data_preprocessing/       # Keyword & topic extraction functions
├── config.py                 # API keys and constants
├── requirements.txt
└── README.md
