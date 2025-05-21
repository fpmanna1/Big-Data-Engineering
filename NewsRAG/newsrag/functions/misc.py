import worldnewsapi
import re

# Fetch
def NewsAPI_fetch(max_results=2, NEWSAPI_API_KEY="API_KEY", min_date="", max_date=""):
    # time window definition
    if min_date or max_date == "":
        import datetime
        temp = datetime.datetime.now().date() - datetime.timedelta(days=1)
        min_date = str(temp)+"00:00:00"#str(datetime.datetime.combine(temp, datetime.time.min))
        max_date = str(temp)+"23:59:59"#str(datetime.datetime.combine(temp, datetime.time.max))
    # sources
    newsapi_configuration = worldnewsapi.Configuration(api_key={'apiKey': NEWSAPI_API_KEY})  # 2 account
    news_urls = [
        "https://www.ansa.it/",
        "https://www.ilfattoquotidiano.it/",
        "https://www.ilsole24ore.com/",
        "https://www.repubblica.it/",
        "https://www.ilmattino.it/"
    ]
    # Converti la lista degli URL in una stringa separata da virgole
    news_sources = ",".join(news_urls)

    try:
        newsapi_instance = worldnewsapi.NewsApi(worldnewsapi.ApiClient(newsapi_configuration))

        max_results = max_results  # replace with your maximum
        offset = 0
        all_results = []

        while len(all_results) < max_results:
            request_count = min(100, max_results - len(all_results))  # request 100 or the remaining number of articles
            response = newsapi_instance.search_news(
                source_countries='it',
                language='it',
                news_sources=news_sources,
                earliest_publish_date=min_date,
                latest_publish_date=max_date,
                sort="publish-time",
                sort_direction="asc",
                offset=offset,
                number=request_count)

            print("Retrieved " + str(len(response.news)) + " articles. Offset: " + str(offset) + "/" + str(max_results) +
                ". Total available: " + str(response.available) + ".")
            all_results.extend(response.news)
            offset += 100
    except worldnewsapi.ApiException as e:
        print("Exception when calling NewsApi->search_news: %s\n" % e)

    if all_results:
        print("Publish date of the last news article:", all_results[-1].publish_date)
    
    # Initialize an empty list to store dictionaries
    news_dicts = []
    for news_article in all_results:
        news_dicts.append(news_article.to_dict())

	# Define the keys to exclude
    keys_to_exclude = {"id", "image", "language", "source_country", "summary"}
	# Initialize an empty list to store filtered dictionaries
    filtered_news_dicts = []
	# Iterate over each NewsArticle object in all_results and convert it to a filtered dictionary
    for news_article in news_dicts:
        filtered_article = {k: v for k, v in news_article.items() if k not in keys_to_exclude}
        filtered_news_dicts.append(filtered_article)
    
    return filtered_news_dicts

# Preprocessing

def extract_website_name(url):
    # Remove the 'https://www.' part from the URL
    website_dict = {
    'ansa': 'ANSA',
    'ilfattoquotidiano': 'Il Fatto Quotidiano',
    'ilsole24ore': 'Il Sole 24 Ore',
    'repubblica': 'Repubblica',
    'ilmattino': 'Il Mattino'
    }
    temp = url.split("//www.")[-1].split(".")[0]
    if temp in website_dict.keys():
        return website_dict[temp]
    else:
        return None

# Function to extract categories from URL
def extract_categories(url, category_list=None):
    if category_list is None:
            category_list = [
            "politica",        # Politics
            "economia",        # Economy
            "cronaca",         # Crime
            "sport",           # Sports
            "mondo",           # World news
            "cultura",         # Culture
            "scienza",         # Science
            "tecnologia",      # Technology
            "salute",          # Health
            "ambiente",        # Environment
            "spettacoli",      # Entertainment
            "arte",            # Art
            "musica",          # Music
            "cinema",          # Cinema
            "moda",            # Fashion
            "viaggi",          # Travel
            "gastronomia",     # Food
            "istruzione",      # Education
            "lavoro",          # Work/Employment
            "finanza",         # Finance
            "giustizia",       # Justice
            "societa",         # Society
            "interni",         # National news
            "esteri",          # International news
            "motori",          # Automobiles
            "media",           # Media
            "televisione",     # Television
            "libri",           # Books
            "religione",       # Religion
            "storia",          # History
            "filosofia"        # Philosophy
            "art",
            "sanità"
            ]
    # Join the category list into a regex pattern
    pattern = r"https?://(?:www\.)?[\w.-]+(/[^/]+)+"
    match = re.search(pattern, url)
    if match:
        # Extract the matched categories
        path_segments = match.group(0).split('/')
        categories_found = [segment for segment in path_segments if segment in category_list]
        # Remove duplicates and convert to a comma-separated string
        unique_categories = ', '.join(sorted(set(categories_found)))
        return unique_categories
    return ''

# Function to extract author names
def extract_author_names(author_list):
    # Ensure the input is a list
    if not isinstance(author_list, list):
        return []
    
    all_matches = []
    for text in author_list:
        if not isinstance(text, str):
            continue
        # Regex to find words starting with uppercase letters
        pattern = r'\b[A-Z][a-z]*\s[A-Z][a-z]*\b'
        # Check for special case "REDAZIONE ANSA"
        if text.upper() == "REDAZIONE ANSA":
            all_matches.append("Redazione ANSA")
            continue
        # Find all matches
        matches = re.findall(pattern, text)
        # Filter out names with 'redat' attached
        filtered_matches = [name for name in matches if not re.search(r'redat', name, flags=re.IGNORECASE)]
        all_matches.extend(filtered_matches)
    
    # Remove duplicates and sort
    unique_authors = sorted(set(all_matches))
    return unique_authors[0]