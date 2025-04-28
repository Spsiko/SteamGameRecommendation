#Was made utilizing AI
import tensorflow as tf
import pandas as pd
import numpy as np
from keras.saving import register_keras_serializable
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Embedding, Flatten, Concatenate, Dense
import os

@register_keras_serializable()
class NCF(Model):
    def __init__(self, num_users, num_items, embedding_dim=64, **kwargs):
        super(NCF, self).__init__(**kwargs)
        self.num_users = num_users
        self.num_items = num_items
        self.embedding_dim = embedding_dim

        self.user_embedding = Embedding(num_users, embedding_dim, embeddings_initializer='he_normal')
        self.item_embedding = Embedding(num_items, embedding_dim, embeddings_initializer='he_normal')

        self.fc1 = Dense(128, activation='relu')
        self.fc2 = Dense(64, activation='relu')
        self.fc3 = Dense(1, activation='sigmoid')

    def call(self, inputs):
        user_input, item_input = inputs
        user_vec = Flatten()(self.user_embedding(user_input))
        item_vec = Flatten()(self.item_embedding(item_input))
        x = Concatenate()([user_vec, item_vec])
        x = self.fc1(x)
        x = self.fc2(x)
        output = self.fc3(x)
        return output

    def get_config(self):
        config = super(NCF, self).get_config()
        config.update({
            'num_users': self.num_users,
            'num_items': self.num_items,
            'embedding_dim': self.embedding_dim
        })
        return config

    @classmethod
    def from_config(cls, config):
        # Handle separating custom vs base Model arguments
        num_users = config.pop('num_users')
        num_items = config.pop('num_items')
        embedding_dim = config.pop('embedding_dim')
        return cls(num_users=num_users, num_items=num_items, embedding_dim=embedding_dim, **config)

# Set base directory dynamically
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load the trained model (relative)
MODEL_PATH = os.path.join(BASE_DIR, 'ncf_model_tf.keras')
model = tf.keras.models.load_model(MODEL_PATH)

# Load game info (relative)
GAMES_PATH = os.path.join(BASE_DIR, 'SteamGameDataset', 'games.csv')
games_df = pd.read_csv(GAMES_PATH)

# Build mapping dictionaries
game_ids = games_df['AppID'].dropna().unique().tolist()
item2idx = {game_id: idx for idx, game_id in enumerate(game_ids)}
idx2item = {idx: game_id for game_id, idx in item2idx.items()}

# Assuming 1000 fake users for now
num_fake_users = 1000

def recommend_games(user_id, top_n=10):
    if user_id >= num_fake_users:
        raise ValueError("User ID out of range (for fake data)")

    valid_item_indices = np.arange(model.num_items)  # Use model.num_items (0 to 11765)
    user_array = np.full(len(valid_item_indices), user_id)

    predicted_scores = model.predict([user_array, valid_item_indices], batch_size=512)

    top_indices = np.argsort(predicted_scores.flatten())[::-1][:top_n]
    recommended_game_ids = [idx2item[i] for i in top_indices]  # Still map back

    return recommended_game_ids

def recommend_based_on_games(user_games, top_n=10):
    # Map provided AppIDs to internal model indices
    internal_indices = [item2idx.get(appid) for appid in user_games if appid in item2idx]

    if not internal_indices:
        # Instead of crashing, fallback to default
        return recommend_random_games(top_n)

    internal_indices = np.array(internal_indices)

    # Create fake "user profile" by averaging their embeddings
    item_embs = model.item_embedding(internal_indices)

    averaged_vector = tf.reduce_mean(item_embs, axis=0)

    all_item_indices = np.arange(model.num_items)

    user_vectors = tf.repeat(tf.expand_dims(averaged_vector, axis=0), repeats=len(all_item_indices), axis=0)

    all_item_embs = model.item_embedding(all_item_indices)

    scores = tf.reduce_sum(user_vectors * all_item_embs, axis=1)

    top_indices = np.argsort(scores.numpy())[::-1][:top_n]

    recommended_game_ids = [idx2item[i] for i in top_indices if idx2item[i] not in user_games]

    return recommended_game_ids

def recommend_random_games(top_n=10):
    all_games = list(idx2item.keys())
    random_indices = np.random.choice(all_games, top_n, replace=False)
    return [idx2item[i] for i in random_indices]