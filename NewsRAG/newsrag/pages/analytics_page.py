import streamlit as st
import streamlit.components.v1 as components

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

import os
import re
from datetime import datetime
from dotenv import load_dotenv
from config.database import MongoDatabaseConnector

from wordcloud import WordCloud
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
# Set the page
st.set_page_config(
    page_title="Articles Analysis Dashboard",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded")

# collection -> csv

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")
## connessioni
connection = MongoDatabaseConnector(MONGO_URI)
db = connection[MONGO_DB_NAME]
collection = db['articles']

def cut_date(date):
    date_str = date.split()[0][:7]
    return date_str

def get_date_list(collection):
    dates = collection.find({}, {'_id': 0, 'publish_date': 1})
    dates = [d['publish_date'].split()[0][:7] for d in list(dates)]
    return list(set(dates))

def get_distinct_list(collection, key):
    values_list = collection.distinct(key)
    return list(values_list)

# text processing# Funzione per rimuovere gli accenti
def remove_accents(text):
    accented_chars = 'àáâäãåèéêëìíîïòóôöõùúûüÀÁÂÄÃÅÈÉÊËÌÍÎÏÒÓÔÖÕÙÚÛÜ'
    replacement_chars = 'aaaaaaeeeeiiiiooooouuuuAAAAAAEEEEIIIIOOOOOUUUU'
    translation_table = str.maketrans(accented_chars, replacement_chars)
    return text.translate(translation_table)
# Funzione per pulire il testo dai caratteri accentai, convertire in minuscolo e sostituire i caratteri speciali con degli spazi
def clean_text(text):
    text = remove_accents(text)
    text = text.lower()
    text = re.sub(r"[\.,:;!?'\-\"«»<>’]", " ", text)
    return text
def remove_stopwords(text):
    ita_stopwords = stopwords.words('italian')
    tokens = word_tokenize(text)
    return [token for token in tokens if token not in ita_stopwords]
def process_text(text):
    text = clean_text(text)
    text = remove_stopwords(text)
    return text

@st.cache_data
def load_df(start_date, end_date, author, category, publisher):
    start_date = start_date.strftime('%Y-%m')
    start_date += "-01 : 00:00:00"
    end_date = end_date.strftime('%Y-%m')
    end_date += "-01 : 23:59:59"
    query = {}
    if publisher:
        query["publisher"] = {"$in": publisher}
    if category:
        query["category"] = {"$in": category}
    if author:
        query["author"] = {"$in": author} #author
    if start_date and end_date:
        query["publish_date"] = {"$gte": start_date, "$lte": end_date}
    elif start_date:
        query["publish_date"] = {"$gte": start_date}
    elif end_date:
        query["publish_date"] = {"$lte": end_date}
    # print(query)
    df = pd.DataFrame(list(collection.find(query).limit(20)))
    if len(df) == 0:
        st.write("No articles found")
    return df
plt.style.use("dark_background")
# sidebar
with st.sidebar:
    year_list = get_date_list(collection)
    # year_list = sorted(year_list)
    # author_list = get_authors_list(collection)
    # categories_list = get_categories_list(collection)

    year_list = sorted(year_list)
    author_list = get_distinct_list(collection, 'author')
    categories_list = get_distinct_list(collection, 'category')
    publisher_list = get_distinct_list(collection, 'publisher')
    keyword_list = get_distinct_list(collection, 'keywords')
    ### data minima/massima
    pipeline = [
    {
        '$group': {
            '_id': None,
            'min_publish_date': {'$min': '$publish_date'},
            'max_publish_date': {'$max': '$publish_date'}
        }
    }
    ]
    # Run the aggregation
    result = list(collection.aggregate(pipeline))
    min_publish_date = result[0]['min_publish_date']
    min_publish_date = datetime.strptime(min_publish_date, '%Y-%m-%d %H:%M:%S')
    max_publish_date = result[0]['max_publish_date']
    max_publish_date = datetime.strptime(max_publish_date, '%Y-%m-%d %H:%M:%S')
    #-----------------------------------------------------------------
    st.header("Filters")
    # Place language and source_country on the same line
    col1, col2 = st.columns(2)
    # # Place start_date and end_date on the same line
    start_date = col1.date_input("Start Date", min_value=min_publish_date,
                                max_value=max_publish_date, value=min_publish_date)  # , value=datetime.date(2023, 1, 1)
    end_date = col2.date_input("End Date", min_value=min_publish_date, max_value=max_publish_date)
    author = st.multiselect("Select an author:", options=author_list)
    category = st.multiselect("Select a category", options=categories_list)#[0]
    publisher = st.multiselect("Select a publisher", options=publisher_list)
    keywords_to_count = st.multiselect("Select keyword(s)", options=keyword_list)


pipeline = [
    {
        "$addFields": {
            "parsed_date": { "$dateFromString": { "dateString": "$publish_date", "format":  "%Y-%m-%d %H:%M:%S" } }
        }
    },
    {
        "$group": {
            "_id": {
                "year": { "$year": "$parsed_date" },
                "month": { "$month": "$parsed_date" }
            },
            "count": { "$sum": 1 }
        }
    },
    {
        "$sort": { "_id.year": 1, "_id.month": 1 }
    },
    {
        "$project": {
            "_id": 0,
            "publish_date": {
                "$concat": [
                    { "$toString": "$_id.year" },
                    "-",
                    { "$cond": { "if": { "$lt": ["$_id.month", 10] }, "then": "0", "else": "" } },
                    { "$toString": "$_id.month" }
                ]
            },
            "count": 1
        }
    }
]

results = list(collection.aggregate(pipeline))
# Separate lists for unique dates and counts
unique_dates = [result['publish_date'] for result in results]
counts = [result['count'] for result in results]
df_tmp = pd.DataFrame(results)
st.write("## Overall Article distribution")
st.bar_chart(data=df_tmp, x="publish_date", y="count", color=None, width=None, height=None, use_container_width=True)
# KEYWORDS
st.write("## Keywords Analysis")
col1, col2 = st.columns([1, 3])
# global
start_date_tmp = str(start_date)+" T00:00:00"
end_date_tmp = str(end_date)+" T23:59:59"
pipeline_keywords = [
    {
        "$match": {
            "publish_date": {
                "$gte": start_date_tmp,
                "$lt": end_date_tmp
            }
        }
    },
    {
        "$unwind": "$keywords"
    },
    {
        "$group": {
            "_id": "$keywords",
            "count": { "$sum": 1 }
        }
    },
    {
        "$sort": { "count": -1 }
    }
]

df_tmp = pd.DataFrame(list(collection.aggregate(pipeline_keywords)))
df_tmp.rename(columns={'_id':'keyword', 'count':'count'}, inplace=True)
col1.dataframe(df_tmp.head(10))
# keywords chosen by user
if keywords_to_count:
    pipeline = [
        {
            "$match": {
                "keywords": { "$in": keywords_to_count }
            }
        },
        {
            "$addFields": {
                "publish_month": {
                    "$substr": ["$publish_date", 0, 7]  # Extract the "YYYY-MM" part of the publish_date
                }
            }
        },
        {
            "$unwind": "$keywords"
        },
        {
            "$match": {
                "keywords": { "$in": keywords_to_count }
            }
        },
        {
            "$group": {
                "_id": {
                    "month": "$publish_month",
                    "keyword": "$keywords"
                },
                "count": { "$sum": 1 }
            }
        },
        {
            "$sort": { "_id.month": 1, "_id.keyword": 1 }  # Sort by month and then by keyword
        }
    ]

    # Execute the aggregation
    results = list(collection.aggregate(pipeline))
    reshaped_results = [
        {
            "date": result['_id']['month'],
            "keyword": result['_id']['keyword'],
            "count": result['count']
        }
        for result in results
    ]
    df_tmp = pd.DataFrame(reshaped_results)
    col2.line_chart(data=df_tmp, x="date", y="count", color="keyword")
# AUTHOR
if st.sidebar.button("Submit"):
    df = load_df(start_date, end_date, author, category, publisher)
    # st.dataframe(df)
    if author:
        st.write("# Author Section")
        # st.dataframe(df)
    # viz 1: distribution of articles w/ categories
        df_mod = df
        df_mod['publish_date'] = df_mod['publish_date'].apply(cut_date)
        counts = []
        for date in year_list:
            # count = df_mod[(df_mod['publish_date'] == date) & (df_mod['authors'] == author_to_find)].shape[0]
            count = df_mod[df_mod['publish_date'] == date].shape[0]
            counts.append(count)
        df_tmp=pd.DataFrame(zip(year_list, counts), columns=["Date", "counts"])
        st.write("### {author} articles distribution".format(author=author[0]))
        st.bar_chart(data=df_tmp, x="Date", y="counts")
        # viz 2
        auth_col1, auth_col2 = st.columns(2)
        df_mod['category'] = ["unclassified" if x==[] else x[0] for x in list(df_mod['category'])]
        plot2 = sns.countplot (x= df_mod["publisher"],hue=df_mod['category'])
        bio_template = "{author} è un giornalista con oltre dieci anni di esperienza nel campo del giornalismo investigativo. Laureato in Scienze della Comunicazione, ha iniziato la sua carriera presso il quotidiano locale, 'Il Giornale di Torino', dove ha sviluppato un'innata capacità di raccontare storie complesse in modo chiaro e avvincente. Attualmente lavora per una delle principali testate nazionali, dove si occupa di cronaca e politica. Luca è noto per la sua integrità professionale e il suo impegno nel garantire un'informazione accurata e imparziale. Nel tempo libero, ama viaggiare e scoprire nuove culture.".format(author=author[0])
        stringa_contatti = "[X](www.x.com)\n[IG](www.instagram.com)"
        auth_col1.write("#### Biography:"+"  \n")
        auth_col1.write(bio_template)
        auth_col1.write("Social: "+stringa_contatti)
        auth_col2.write("#### At a glance")
        auth_col2.pyplot(plot2.get_figure(), clear_figure =True)
        st.write("#### {author} articles repository".format(author=author[0]))
        st.dataframe(df_mod[['publish_date','title',"url"]])

        # viz 3: wordcloud
        corpus = ' '.join(df_mod['text'])
        corpus = process_text(corpus)
        corpus = ' '.join(corpus)
        wc = WordCloud(background_color="white", max_words=30, width=1000, height=500)
        wc_image = wc.generate(corpus)
        plt.imshow(wc_image, interpolation="bilinear")
        plt.axis("off")
        plt.show()
        st.pyplot()
    #--------------------------------------------------------

st.write("## Topics")
with open("pages/content/topic_cluster.html",'r', encoding='utf-8') as f: 
    html_data = f.read()
# Show in webpage
# st.markdown(html_data, unsafe_allow_html=True)
st.components.v1.html(html_data, width=1300, height=800, scrolling=True)
st.write("### Topics Word Scores")
with open("pages/content/barchart.html",'r', encoding='utf-8') as f: 
    html_data = f.read()
# Show in webpage
# st.markdown(html_data, unsafe_allow_html=True)
st.components.v1.html(html_data, width=1300, height=800, scrolling=True)