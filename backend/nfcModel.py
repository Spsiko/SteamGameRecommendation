# Was made utilizing AI
import tensorflow as tf
import pandas as pd
import numpy as np
import os
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Embedding, Flatten, Concatenate, Dense, Dropout, BatchNormalization, Multiply, LeakyReLU
from keras.saving import register_keras_serializable
import requests

@register_keras_serializable()
class AdvancedNCF(Model):
    def __init__(self, num_users, num_items, embedding_dim=64, **kwargs):
        super(AdvancedNCF, self).__init__(**kwargs)
        self.num_users = num_users
        self.num_items = num_items
        self.embedding_dim = embedding_dim

        # GMF part
        self.user_embedding_gmf = Embedding(num_users, embedding_dim)
        self.item_embedding_gmf = Embedding(num_items, embedding_dim)

        # MLP part
        self.user_embedding_mlp = Embedding(num_users, embedding_dim)
        self.item_embedding_mlp = Embedding(num_items, embedding_dim)

        # MLP hidden layers
        self.fc1 = Dense(256)
        self.bn1 = BatchNormalization()
        self.fc2 = Dense(128)
        self.bn2 = BatchNormalization()
        self.fc3 = Dense(64)
        self.bn3 = BatchNormalization()
        self.dropout = Dropout(0.2)

        # Final prediction
        self.final_dense = Dense(1, activation='sigmoid')

    def call(self, inputs):
        user_input, item_input = inputs

        # GMF branch
        user_vec_gmf = self.user_embedding_gmf(user_input)
        item_vec_gmf = self.item_embedding_gmf(item_input)
        gmf = Multiply()([user_vec_gmf, item_vec_gmf])

        # MLP branch
        user_vec_mlp = self.user_embedding_mlp(user_input)
        item_vec_mlp = self.item_embedding_mlp(item_input)
        mlp = Concatenate()([user_vec_mlp, item_vec_mlp])
        mlp = Flatten()(mlp)
        mlp = self.fc1(mlp)
        mlp = LeakyReLU()(mlp)
        mlp = self.bn1(mlp)
        mlp = self.dropout(mlp)
        mlp = self.fc2(mlp)
        mlp = LeakyReLU()(mlp)
        mlp = self.bn2(mlp)
        mlp = self.dropout(mlp)
        mlp = self.fc3(mlp)
        mlp = LeakyReLU()(mlp)
        mlp = self.bn3(mlp)

        # Final concat and predict
        combined = Concatenate()([Flatten()(gmf), mlp])
        output = self.final_dense(combined)
        return output

    def get_config(self):
        config = super(AdvancedNCF, self).get_config()
        config.update({
            'num_users': self.num_users,
            'num_items': self.num_items,
            'embedding_dim': self.embedding_dim
        })
        return config

    @classmethod
    def from_config(cls, config):
        num_users = config.pop('num_users')
        num_items = config.pop('num_items')
        embedding_dim = config.pop('embedding_dim')
        return cls(num_users=num_users, num_items=num_items, embedding_dim=embedding_dim, **config)


# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load the trained model
MODEL_PATH = os.path.join(BASE_DIR, 'ncf_advanced_model.keras')
model = tf.keras.models.load_model(MODEL_PATH)

# Load games data
GAMES_PATH = os.path.join(BASE_DIR, 'SteamGameDataset/games.csv')
games_df = pd.read_csv(GAMES_PATH)

# Create a mapping from appid to name
appid_to_name = pd.Series(games_df['Name'].values, index=games_df['AppID']).to_dict()

def get_game_name_from_steam(appid):
    try:
        url = f'https://store.steampowered.com/api/appdetails?appids={appid}'
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        if data[str(appid)]['success']:
            return data[str(appid)]['data']['name']
    except Exception as e:
        print(f"Failed to fetch name for AppID {appid}: {e}")
    return "Unknown Game"

# Load mappings
item2idx = pd.read_csv(os.path.join(BASE_DIR, 'item2idx.csv'), index_col=0)
item2idx = item2idx.squeeze().to_dict()

idx2item = pd.read_csv(os.path.join(BASE_DIR, 'idx2item.csv'), index_col=0)
idx2item = idx2item.squeeze().to_dict()

# Safety if pandas warns:
if isinstance(idx2item, pd.Series):
    idx2item = idx2item.to_dict()

def recommend_based_on_games(user_games, top_n=10):
    internal_indices = [item2idx.get(appid) for appid in user_games if appid in item2idx]

    if not internal_indices:
        return recommend_random_games(top_n)

    internal_indices = np.array(internal_indices)

    item_embs_gmf = model.item_embedding_gmf(internal_indices)
    item_embs_mlp = model.item_embedding_mlp(internal_indices)

    averaged_vector_gmf = tf.reduce_mean(item_embs_gmf, axis=0)
    averaged_vector_mlp = tf.reduce_mean(item_embs_mlp, axis=0)

    user_profile = tf.concat([averaged_vector_gmf, averaged_vector_mlp], axis=-1)

    all_item_gmf = model.item_embedding_gmf(np.arange(model.num_items))
    all_item_mlp = model.item_embedding_mlp(np.arange(model.num_items))
    item_profiles = tf.concat([all_item_gmf, all_item_mlp], axis=-1)

    scores = tf.reduce_sum(user_profile * item_profiles, axis=1)

    for idx in internal_indices:
        scores = tf.tensor_scatter_nd_update(scores, [[idx]], [-np.inf])

    top_indices = tf.argsort(scores, direction='DESCENDING').numpy()[:top_n]

    recommendations = []
    for i in top_indices:
        appid = idx2item.get(i)
        if appid is None:
            continue

        # 🔵 Force appid into a native Python int
        appid = int(appid)

        game_name = appid_to_name.get(appid)
        if not game_name:
            game_name = get_game_name_from_steam(appid)

        recommendations.append({
            'appid': appid,
            'name': game_name
        })

    return recommendations

def recommend_random_games(top_n=10):
    all_game_ids = list(idx2item.values())
    random_appids = np.random.choice(all_game_ids, size=top_n, replace=False)

    recommendations = []
    for appid in random_appids:
        appid = int(appid)  # 🔵 Convert to Python int

        game_name = appid_to_name.get(appid)
        if not game_name:
            game_name = get_game_name_from_steam(appid)

        recommendations.append({
            'appid': appid,
            'name': game_name
        })

    return recommendations