# This is the model for the Steam Game Recommender
# It is used to recommend games to users based on their game library
# It is also used to recommend games to users based on the games they have played

import pandas as pd
import numpy as np
from sklearn.preprocessing import MultiLabelBinarizer, MinMaxScaler
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Any
import os
from datetime import datetime
import ast


class SteamGameRecommender:
    def __init__(self, data_path: str):
        """
        Initialize the Steam Game Recommender with enhanced features.
        
        Args:
            data_path (str): Path to the games.csv file
        """
        self.data_path = data_path
        self.games_df = None
        self.genre_encoder = MultiLabelBinarizer()
        self.category_encoder = MultiLabelBinarizer()
        self.scaler = MinMaxScaler()
        self.feature_weights = {
            'genres': 0.3,
            'categories': 0.2,
            'price': 0.1,
            'ratings': 0.2,
            'release_date': 0.1,
            'popularity': 0.1
        }
        
    def load_data(self) -> None:
        """Load and preprocess the games data."""
        try:
            self.games_df = pd.read_csv(self.data_path, encoding='latin1')

            columns_to_drop = [
            'about_the_game', 'short_description', 'detailed_description',
            'header_image', 'background', 'screenshots', 'website',
            'support_url', 'legal_notice', 'pc_requirements', 'mac_requirements',
            'linux_requirements', 'developers', 'publishers'
            ]
            self.games_df.drop(columns=[col for col in columns_to_drop if col in self.games_df.columns], inplace=True)
        
            print(f"Successfully loaded {len(self.games_df)} games")
        except Exception as e:
            print(f"Error loading data: {e}")
            raise
            
    def preprocess_data(self) -> None:
        """Preprocess the games data with enhanced features."""
        if self.games_df is None:
            raise ValueError("Data not loaded. Call load_data() first.")
            
        self.games_df.rename(columns={
            'Genres': 'genres',
            'Categories': 'categories'
        }, inplace=True)
            
        # Convert string representations of lists to actual lists
        self.games_df['genres'] = self.games_df['genres'].apply(
            lambda x: ast.literal_eval(x) if isinstance(x, str) and x.startswith('[') else []
        )

        self.games_df['categories'] = self.games_df['categories'].apply(
            lambda x: ast.literal_eval(x) if isinstance(x, str) and x.startswith('[') else []
        )

        
        # Create binary features for genres and categories
        genre_features = self.genre_encoder.fit_transform(self.games_df['genres'])
        category_features = self.category_encoder.fit_transform(self.games_df['categories'])
        
        # Calculate popularity score (combination of ratings and playtime)
        self.games_df['popularity_score'] = (
            self.games_df['Positive'] / 
            (self.games_df['Positive'] + self.games_df['Negative'])
        )
        
        # Normalize numerical features
        numerical_features = ['price', 'Positive', 'Negative', 'popularity_score']
        for feature in numerical_features:
            if feature in self.games_df.columns:
                self.games_df[feature] = self.games_df[feature].fillna(0)
                self.games_df[feature] = self.scaler.fit_transform(
                    self.games_df[feature].values.reshape(-1, 1)
                )
        
        # Combine all features with weights
        self.feature_matrix = np.hstack([
            genre_features * self.feature_weights['genres'],
            category_features * self.feature_weights['categories'],
            self.games_df[['price']].values * self.feature_weights['price'],
            self.games_df[['Positive', 'Negative']].values * self.feature_weights['ratings'],
            self.games_df[['popularity_score']].values * self.feature_weights['popularity']
        ])

        self.feature_matrix = self.feature_matrix.astype(np.float32)
        
    def compute_similarities(self, query_vector: np.ndarray) -> np.ndarray:
        """
        Compute cosine similarities between a query vector and all game vectors.

        Args:
            query_vector (np.ndarray): 1D feature vector of a game

        Returns:
            np.ndarray: Array of similarity scores
        """
        return cosine_similarity(query_vector.reshape(1, -1), self.feature_matrix).flatten()

        
    def get_content_based_recommendations(
    self, 
    game_id: int, 
    n_recommendations: int = 5,
    include_popularity: bool = True
) -> List[Dict[str, Any]]:
        """
        Get content-based recommendations for a given game.
        """
        if self.feature_matrix is None:
            raise ValueError("Data not preprocessed. Call preprocess_data() first.")

        try:
            game_idx = self.games_df[self.games_df['appid'] == game_id].index[0]
            query_vector = self.feature_matrix[game_idx]
            
            # --- Use on-demand similarity ---
            similar_games = self.compute_similarities(query_vector)

            if include_popularity:
                popularity_scores = self.games_df['popularity_score'].values
                similar_games = similar_games * (1 + popularity_scores)
            
            # Exclude the input game itself
            similar_games[game_idx] = -np.inf

            # Get top n games
            top_indices = np.argsort(similar_games)[-n_recommendations:][::-1]

            recommendations = []
            for idx in top_indices:
                game = self.games_df.iloc[idx]
                recommendations.append({
                    'appid': game['appid'],
                    'name': game['name'],
                    'genres': game['genres'],
                    'categories': game['categories'],
                    'price': game['price'],
                    'positive_ratings': game['positive_ratings'],
                    'negative_ratings': game['negative_ratings'],
                    'similarity_score': similar_games[idx]
                })
                
            return recommendations

        except IndexError:
            raise ValueError(f"Game with ID {game_id} not found in dataset")

            
    def get_user_based_recommendations(
    self,
    user_games: List[int],
    n_recommendations: int = 5,
    include_popularity: bool = True
) -> List[Dict[str, Any]]:
        """
        Get recommendations based on a user's game library.
        """
        if self.feature_matrix is None:
            raise ValueError("Data not preprocessed. Call preprocess_data() first.")

        # Find feature vectors for user's games
        user_game_indices = [
            self.games_df[self.games_df['appid'] == game_id].index[0]
            for game_id in user_games
            if game_id in self.games_df['appid'].values
        ]
        
        if not user_game_indices:
            raise ValueError("None of the provided game IDs were found in the dataset")

        user_vectors = self.feature_matrix[user_game_indices]
        
        # Average their feature vectors
        avg_user_vector = np.mean(user_vectors, axis=0)

        # --- Use on-demand similarity ---
        similar_games = self.compute_similarities(avg_user_vector)

        if include_popularity:
            popularity_scores = self.games_df['popularity_score'].values
            similar_games = similar_games * (1 + popularity_scores)
        
        # Exclude games user already owns
        for idx in user_game_indices:
            similar_games[idx] = -np.inf

        # Get top n games
        top_indices = np.argsort(similar_games)[-n_recommendations:][::-1]

        recommendations = []
        for idx in top_indices:
            game = self.games_df.iloc[idx]
            recommendations.append({
                'appid': game['appid'],
                'name': game['name'],
                'genres': game['genres'],
                'categories': game['categories'],
                'price': game['price'],
                'positive_ratings': game['positive_ratings'],
                'negative_ratings': game['negative_ratings'],
                'similarity_score': similar_games[idx]
            })

        return recommendations

        
    def initialize(self) -> None:
        """Initialize the recommender by loading and preprocessing data."""
        self.load_data()
        self.preprocess_data()
        self.build_similarity_matrix()
        
    def update_feature_weights(self, weights: Dict[str, float]) -> None:
        """
        Update the weights for different features in the recommendation system.
        
        Args:
            weights (Dict[str, float]): Dictionary of feature weights to update
        """
        self.feature_weights.update(weights)
        # Rebuild the feature matrix with new weights
        self.preprocess_data()
        self.build_similarity_matrix()