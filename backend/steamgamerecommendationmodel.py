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
        self.similarity_matrix = None
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
            self.games_df = pd.read_csv(self.data_path)
            print(f"Successfully loaded {len(self.games_df)} games")
        except Exception as e:
            print(f"Error loading data: {e}")
            raise
            
    def preprocess_data(self) -> None:
        """Preprocess the games data with enhanced features."""
        if self.games_df is None:
            raise ValueError("Data not loaded. Call load_data() first.")
            
        # Convert string representations of lists to actual lists
        self.games_df['genres'] = self.games_df['genres'].apply(
            lambda x: eval(x) if isinstance(x, str) else []
        )
        self.games_df['categories'] = self.games_df['categories'].apply(
            lambda x: eval(x) if isinstance(x, str) else []
        )
        
        # Create binary features for genres and categories
        genre_features = self.genre_encoder.fit_transform(self.games_df['genres'])
        category_features = self.category_encoder.fit_transform(self.games_df['categories'])
        
        # Calculate popularity score (combination of ratings and playtime)
        self.games_df['popularity_score'] = (
            self.games_df['positive_ratings'] / 
            (self.games_df['positive_ratings'] + self.games_df['negative_ratings'])
        )
        
        # Normalize numerical features
        numerical_features = ['price', 'positive_ratings', 'negative_ratings', 'popularity_score']
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
            self.games_df[['positive_ratings', 'negative_ratings']].values * self.feature_weights['ratings'],
            self.games_df[['popularity_score']].values * self.feature_weights['popularity']
        ])
        
    def build_similarity_matrix(self) -> None:
        """Build the similarity matrix for content-based recommendations."""
        if self.feature_matrix is None:
            raise ValueError("Data not preprocessed. Call preprocess_data() first.")
            
        self.similarity_matrix = cosine_similarity(self.feature_matrix)
        
    def get_content_based_recommendations(
        self, 
        game_id: int, 
        n_recommendations: int = 5,
        include_popularity: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get content-based recommendations for a given game with enhanced scoring.
        
        Args:
            game_id (int): The ID of the game to get recommendations for
            n_recommendations (int): Number of recommendations to return
            include_popularity (bool): Whether to include popularity in scoring
            
        Returns:
            List[Dict[str, Any]]: List of recommended games with their details
        """
        if self.similarity_matrix is None:
            raise ValueError("Similarity matrix not built. Call build_similarity_matrix() first.")
            
        try:
            game_idx = self.games_df[self.games_df['appid'] == game_id].index[0]
            similar_games = self.similarity_matrix[game_idx]
            
            if include_popularity:
                # Adjust similarity scores with popularity
                popularity_scores = self.games_df['popularity_score'].values
                similar_games = similar_games * (1 + popularity_scores)
            
            # Get top n similar games (excluding the input game)
            top_indices = np.argsort(similar_games)[-n_recommendations-1:-1][::-1]
            
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
        Get recommendations based on a user's game library with enhanced scoring.
        
        Args:
            user_games (List[int]): List of game IDs in user's library
            n_recommendations (int): Number of recommendations to return
            include_popularity (bool): Whether to include popularity in scoring
            
        Returns:
            List[Dict[str, Any]]: List of recommended games with their details
        """
        if self.similarity_matrix is None:
            raise ValueError("Similarity matrix not built. Call build_similarity_matrix() first.")
            
        # Get average similarity scores across user's games
        user_game_indices = [
            self.games_df[self.games_df['appid'] == game_id].index[0]
            for game_id in user_games
            if game_id in self.games_df['appid'].values
        ]
        
        if not user_game_indices:
            raise ValueError("None of the provided game IDs were found in the dataset")
            
        avg_similarity = np.mean(self.similarity_matrix[user_game_indices], axis=0)
        
        if include_popularity:
            # Adjust similarity scores with popularity
            popularity_scores = self.games_df['popularity_score'].values
            avg_similarity = avg_similarity * (1 + popularity_scores)
        
        # Get top n recommendations (excluding games user already owns)
        top_indices = np.argsort(avg_similarity)[-n_recommendations-len(user_games):-len(user_games)][::-1]
        
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
                'similarity_score': avg_similarity[idx]
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