import streamlit as st
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import requests
import ast


st.set_page_config(
    page_title='Movie Recommendation Engine',
    page_icon= '📺',
    layout='wide'
)

st.title('📺 Movie Recommendation Engine'.upper())
st.write('Select movies you have watched, and the model will suggest your next watch!!!!')


def extract_genres(genre_str):
    """
    Parses a stringified JSON list like:
    '[{"id": 28, "name": "Action"}, {"id": 12, "name": "Adventure"}]'
    and converts it into a clean space-separated string: 'Action Adventure'
    """
    try:
        # Convert string representation of list into actual Python list of dicts
        genres_list = ast.literal_eval(genre_str)
        # Extract names and join them
        return " ".join([g['name'] for g in genres_list])
    except (ValueError, SyntaxError):
        # Fallback if it's already a string or empty
        return ""

@st.cache_data
def load_data_train_model():
    """
    Loads Movie dataset (or create a built in data to fallback to)
    """
    
    try:
        url = "https://raw.githubusercontent.com/vamshi121/TMDB-5000-Movie-Dataset/refs/heads/main/tmdb_5000_movies.csv"
        df = pd.read_csv(url)
        df['genres_clean'] = df['genres'].apply(extract_genres)
        # st.write(df['genres_clean'])
    except Exception:
        data = {
            'movieId' : list(range(1, 11)),
            'title' : [
                'Toy Story (1995)', 'Jumanji (1995)', 'Grumpier Old Men (1995)',
                'Waiting to Exhale (1995)', 'Father of the Bride Part II (1995)',
                'Heat (1995)', 'Sarbina (1995)', 'Tom and Huck (1995)',
                'Sudden Death (1995)', 'Golden Eye (1995)'
            ],
            'genres_clean': [
                "Adventure Animation Children Comedy Fantasy",
                "Adventure Children Fantasy",
                "Comedy Romance",
                "Comedy Drama Romance",
                "Comedy",
                "Action Crime Thriller",
                "Comedy Romance",
                "Adventure Children",
                "Action",
                "Action Adventure Thriller"
            ]
        }
        df = pd.DataFrame(data)
    df['display_title'] = df['title']

    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix =tfidf.fit_transform(df['genres_clean'])

    # compute similarity score using cosine_similarity
    similiarity_matrix = cosine_similarity(tfidf_matrix, tfidf_matrix)

    return df, similiarity_matrix

df, similarity_matrix = load_data_train_model()

TMDB_API_KEY = st.sidebar.text_input('TMDB API Key (Optional for posters)', type='password')

def fetch_poster(movie_title):
    if TMDB_API_KEY:
        try:
            clean_search_title = movie_title.split(' (')[0]
            search_url = f'https://api.themoviedb.org/3/trending/movie/day?api_key={TMDB_API_KEY}&query={clean_search_title}&language=en-US'
            response = requests.get(search_url).json()
            #st.write(response)
            if response.get('results'):
                poster_path = response['results'][0].get('poster_path')
                if poster_path:
                    return f'https://image.tmdb.org/t500{poster_path}'
        except Exception:
            pass
    else:
        st.warning('No API KEY')

    encoded_title = movie_title.replace(' ', '+')
    return f'https://via.placeholder.com/300x450/1e293b/ffffff?text={encoded_title}'


def predict_next_movies(watched_titles, df, similarity_matrix, top_n=5):

    if not watched_titles:
        return []

    indices = df[df['display_title'].isin(watched_titles)].index.tolist()

    # aggregate the similiarity scoress
    sim_scores = similarity_matrix[indices].mean(axis=0)

    scored_indices = list(enumerate(sim_scores))
    scored_indices = sorted(scored_indices, key=lambda x: x[1], reverse=True)

    recommendations = []
    for idx, score in scored_indices:
        title = df.iloc[idx]['display_title']
        if title not in watched_titles:
            recommendations.append((title, df.iloc[idx]['genres'].replace('|', ', ')))

        if len(recommendations) == top_n:
            break
    return recommendations




st.subheader('1.Pick Movies you have watched')
all_movies = df['display_title'].values

selected_movies = st.multiselect(
    'Search and select titles', options= all_movies, default = [all_movies[0]] if len(all_movies) > 0 else []
)

num_recs = st.slider('Number of recommendations', min_value=3, max_value=10, value=5)

if st.button('Predict Next Watch', type='primary'):
    if not selected_movies:
        st.warning('Please, select at least one movie you have watched')
    else:
        with st.spinner('Analyzing viewing preferences and finding the best matches...'):
            recommendations = predict_next_movies(selected_movies, df, similarity_matrix, top_n=num_recs)

        st.subheader('Recommended for you')

        cols = st.columns(len(recommendations))
        for idx, (title, genres) in enumerate(recommendations):
            poster_url = fetch_poster(title)
            with cols[idx]:
                st.image(poster_url, width='content')
                st.markdown(f'**{title}**')
                st.caption(f'{genres}')
