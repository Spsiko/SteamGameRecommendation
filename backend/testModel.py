from steamgamerecommendationmodel import SteamGameRecommender
import os

def generate_recommendations(data):
    """
    Generate game recommendations based on user input.
    
    Args:
        data (dict): Dictionary containing either:
            - 'game_id': Single game ID for content-based recommendations
            - 'user_games': List of game IDs for user-based recommendations
    
    Returns:
        list: List of recommended games with their details
    """
    # Initialize the recommender
    data_path = os.path.join('backend', 'SteamGameDataset', 'games.csv')
    recommender = SteamGameRecommender(data_path)
    recommender.initialize()
    
    # Set optimal feature weights based on testing
    recommender.update_feature_weights({
        'genres': 0.4,
        'categories': 0.3,
        'price': 0.1,
        'ratings': 0.1,
        'popularity': 0.1
    })
    
    # Generate recommendations based on input type
    if 'game_id' in data:
        return recommender.get_content_based_recommendations(
            game_id=data['game_id'],
            n_recommendations=5,
            include_popularity=True
        )
    elif 'user_games' in data:
        return recommender.get_user_based_recommendations(
            user_games=data['user_games'],
            n_recommendations=5,
            include_popularity=True
        )
    else:
        raise ValueError("Input data must contain either 'game_id' or 'user_games'")


from steamgamerecommendationmodel import SteamGameRecommender

recommender = SteamGameRecommender('backend/SteamGameDataset/games.csv')
recommender.initialize()

print("Initialization complete!")
