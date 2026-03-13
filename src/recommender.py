import os
import requests
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ==============================
# OMDb API KEY
# ==============================
OMDB_API_KEY = "20b8e1de"

# ==============================
# LOAD DATASET
# ==============================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "../data/movies.csv")

movies = pd.read_csv(DATA_PATH)
movies["genres"] = movies["genres"].fillna("")

# TF-IDF on genres
tfidf = TfidfVectorizer(stop_words="english")
tfidf_matrix = tfidf.fit_transform(movies["genres"])

cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)

movies = movies.reset_index()
indices = pd.Series(movies.index, index=movies["title"]).drop_duplicates()

# ==============================
# SEARCH FUNCTION
# ==============================

def search_movies(query):
    if not query:
        return []

    query = query.lower()
    matches = movies[movies["title"].str.lower().str.contains(query)]
    return matches["title"].head(10).tolist()

# ==============================
# FETCH MOVIE DETAILS FROM OMDb
# ==============================

def fetch_movie_details(title):
    url = f"http://www.omdbapi.com/?t={title}&apikey={OMDB_API_KEY}"
    response = requests.get(url)
    data = response.json()

    if data.get("Response") == "True":
        return {
            "title": data.get("Title"),
            "year": data.get("Year"),
            "rating": data.get("imdbRating"),
            "plot": data.get("Plot"),
            "actors": data.get("Actors"),
            "poster": data.get("Poster")
        }
    else:
        return {
            "title": title,
            "year": "N/A",
            "rating": "N/A",
            "plot": "Not available",
            "actors": "N/A",
            "poster": None
        }

# ==============================
# RECOMMENDATION FUNCTION
# ==============================

def get_recommendations(title):
    if title not in indices:
        return []

    idx = indices[title]

    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = sim_scores[1:6]

    movie_indices = [i[0] for i in sim_scores]

    recommendations = []

    for i in movie_indices:
        movie_title = movies.iloc[i]["title"]
        details = fetch_movie_details(movie_title)
        recommendations.append(details)

    return recommendations