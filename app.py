import streamlit as st
import pickle
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time

# Create a session with retry logic
session = requests.Session()
retry = Retry(connect=3, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)

# Set page config
st.set_page_config(page_title="Movie Recommender System", layout="wide")

# Custom CSS for better UI
st.markdown("""
<style>
    .reportview-container {
        background: #f0f2f6;
    }
    .main {
        background-color: #f0f2f6;
    }
    div.stButton > button:first-child {
        background-color: #ff4b4b;
        color: white;
        border-radius: 10px;
        font-size: 20px;
        font-weight: bold;
        border: none;
        padding: 10px 24px;
    }
    div.stButton > button:first-child:hover {
        background-color: #ff6b6b;
    }
    h1 {
        color: #ff4b4b;
        font-family: 'Helvetica Neue', sans-serif;
    }
</style>
""", unsafe_allow_html=True)

# Function to fetch movie poster
def fetch_poster(movie_id, title):
    api_key = "dd6f0158309ae1879f43d935b52e6c86"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Connection": "keep-alive"
    }
    
    try:
        # 1. Try fetching by ID first
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US"
        # Use session instead of requests.get
        response = session.get(url, timeout=10, headers=headers, verify=False)
        
        # If ID lookup works
        if response.status_code == 200:
            data = response.json()
            poster_path = data.get('poster_path')
            if poster_path:
                return "https://image.tmdb.org/t/p/w500/" + poster_path
        
        # 2. If ID lookup failed or no poster, try searching by title
        clean_title = title.split('(')[0].strip() # Remove year
        search_url = f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={clean_title}"
        search_response = session.get(search_url, timeout=10, headers=headers, verify=False)
        
        if search_response.status_code == 200:
                data = search_response.json()
                if data['results']:
                    for result in data['results']:
                        if result.get('poster_path'):
                            return "https://image.tmdb.org/t/p/w500/" + result.get('poster_path')

        print(f"FAILED: {title} | Status: {response.status_code}")
        return "https://placehold.co/500x750?text=No+Poster"
            
    except Exception as e:
        # Return the actual error message on the image so we can debug
        error_msg = str(e).split(':')[0][:20] 
        print(f"FAILED: {title} | Error: {e}") 
        return f"https://placehold.co/500x750?text={error_msg}"

# Recommendation function
def recommend(movie):
    try:
        movie_index = movies[movies['title'] == movie].index[0]
        distances = similarity[movie_index]
        movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

        recommended_movies = []
        recommended_movies_posters = []
        
        for i in movies_list:
            movie_id = movies.iloc[i[0]].movie_id
            movie_title = movies.iloc[i[0]].title
            recommended_movies.append(movie_title)
            recommended_movies_posters.append(fetch_poster(movie_id, movie_title))
            
        return recommended_movies, recommended_movies_posters
    except Exception as e:
        st.error(f"Error recommending movies: {e}")
        return [], []

# Load data
try:
    movies_dict = pickle.load(open('movies.pkl', 'rb'))
    # If it's already a DataFrame, use it directly, otherwise convert
    movies = pd.DataFrame(movies_dict) if not isinstance(movies_dict, pd.DataFrame) else movies_dict
    similarity = pickle.load(open('similarity.pkl', 'rb'))
except FileNotFoundError:
    st.error("Error: 'movies.pkl' or 'similarity.pkl' not found. Please ensure data files are in the directory.")
    st.stop()


# UI Header
with st.container():
    st.markdown("<h1 style='text-align: center; color: #ff4b4b;'>🎬 Movie Recommender System</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #333;'>Discover your next favorite movie!</h3>", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("About")
    st.info("This is a Content-Based Movie Recommender System. Select a movie you like, and we'll suggest 5 similar movies based on their metadata (genres, cast, crew, etc.).")
    st.markdown("---")
    st.success("Built with Streamlit & Python")

# Movie Selection
selected_movie_name = st.selectbox(
    'Which movie do you like?',
    movies['title'].values,
    index=0
)

# Recommendation Button
if st.button('Get Recommendations', use_container_width=True):
    with st.spinner('Thinking...'):
        names, posters = recommend(selected_movie_name)
    
    st.markdown("---")
    st.subheader("We think you'll love these:")
    
    cols = st.columns(5)
    for idx, col in enumerate(cols):
        with col:
            st.image(posters[idx], use_container_width=True)
            st.markdown(f"<div style='text-align: center; font-weight: bold;'>{names[idx]}</div>", unsafe_allow_html=True)
