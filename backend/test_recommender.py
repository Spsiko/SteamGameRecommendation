# test_recommender.py
import time
from steamgamerecommendationmodel import SteamGameRecommender

def test_initialize(recommender):
    print("\n[1] Testing Initialization...")
    try:
        recommender.initialize()
        print("✅ Initialization successful!")
    except Exception as e:
        print(f"❌ Initialization failed: {e}")

def test_single_game_recommendation(recommender, game_id=620):
    print("\n[2] Testing Content-Based Recommendation...")
    try:
        start = time.time()
        recs = recommender.get_content_based_recommendations(game_id=game_id, n_recommendations=5)
        end = time.time()

        for rec in recs:
            print(f"🎮 {rec['name']} (Similarity: {rec['similarity_score']:.4f})")
        print(f"⏱️ Took {end - start:.3f} seconds for recommendation.")

    except Exception as e:
        print(f"❌ Single game recommendation failed: {e}")

def test_user_based_recommendation(recommender, user_games=[620, 730]):
    print("\n[3] Testing User-Based Recommendation...")
    try:
        start = time.time()
        recs = recommender.get_user_based_recommendations(user_games=user_games, n_recommendations=5)
        end = time.time()

        for rec in recs:
            print(f"🎯 {rec['name']} (Similarity: {rec['similarity_score']:.4f})")
        print(f"⏱️ Took {end - start:.3f} seconds for recommendation.")

    except Exception as e:
        print(f"❌ User-based recommendation failed: {e}")

def test_bad_game_id(recommender):
    print("\n[4] Testing Invalid Game ID...")
    try:
        recommender.get_content_based_recommendations(game_id=99999999, n_recommendations=5)
        print("❌ Error: Should have raised an exception but did not!")
    except Exception as e:
        print(f"✅ Correctly caught error: {e}")

def test_empty_user_library(recommender):
    print("\n[5] Testing Empty User Library...")
    try:
        recommender.get_user_based_recommendations(user_games=[], n_recommendations=5)
        print("❌ Error: Should have raised an exception but did not!")
    except Exception as e:
        print(f"✅ Correctly caught error: {e}")

if __name__ == "__main__":
    print("🎮 Steam Game Recommender Test Suite 🎮")
    
    # Path to your games.csv
    recommender = SteamGameRecommender('backend/SteamGameDataset/games.csv')

    # Run tests
    test_initialize(recommender)
    test_single_game_recommendation(recommender)
    test_user_based_recommendation(recommender)
    test_bad_game_id(recommender)
    test_empty_user_library(recommender)

    print("\n🏁 All tests completed.")
