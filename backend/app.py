#parts of this code were made by use of AI
import flask
import requests
from flask import request, jsonify, send_from_directory
from flask_cors import CORS
import os
from dotenv import load_dotenv
import json
import nfcModel

load_dotenv()

app = flask.Flask(__name__, static_folder='..//frontend')
CORS(app)  # Enable CORS for all routes
port = 3000

STEAM_API_KEY = os.getenv('STEAM_API_KEY')

@app.route('/')
def home():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/script.js')
def script():
    return send_from_directory(app.static_folder, 'script.js')

@app.route('/style.css') #We don't have a style.css but this is in case it is needed.
def style():
    pass

@app.route('/images/blank.png')
def blank():
    return send_from_directory(app.static_folder, 'images/blank.png')

@app.route('/serverRequest', methods=['GET'])
def server_request():
    print(f'Request received: {request.args}')
    type = request.args.get('type')
    url = ''

    # Determining which type of information is needed from Steam
    if type == 'search':
        game_name = request.args.get('game')
        url = f'https://steamcommunity.com/actions/SearchApps/{game_name}'
    else:
        appid = request.args.get('appid')
        url = f'https://store.steampowered.com/api/appdetails?appids={appid}'

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return jsonify(data)
    except requests.exceptions.RequestException as error:
        print(f"Error fetching from Steam: {error}")
        return jsonify({'error': 'Failed to fetch from Steam'}), 500

@app.route('/getSteamLibrary', methods=['GET'])
def get_steam_library():
    print(f'{STEAM_API_KEY}')
    steam_id = request.args.get('steamid')
    if not steam_id:
        return jsonify({'error': 'Steam ID is required'}), 400

    url = f'http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={STEAM_API_KEY}&steamid={steam_id}&format=json'

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return jsonify(data)
    except requests.exceptions.RequestException as error:
        print(f"Error fetching Steam library: {error}")
        return jsonify({'error': 'Failed to fetch Steam library'}), 500

@app.route('/resolveVanityURL', methods=['GET'])
def resolve_vanity_url():
    vanity_url = request.args.get('vanityurl')
    if not vanity_url:
        return jsonify({'error': 'Vanity URL is required'}), 400

    url = f'http://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/?key={STEAM_API_KEY}&vanityurl={vanity_url}'

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return jsonify(data)
    except requests.exceptions.RequestException as error:
        print(f"Error resolving vanity URL: {error}")
        return jsonify({'error': 'Failed to resolve vanity URL'}), 500
    
@app.route('/getRecommendations', methods=['POST'])
def get_recommendations():
    try:
        data = request.get_json()

        # Expecting {"games": [list of AppIDs]}
        user_games = data.get('games')
        if not user_games:
            return jsonify({"error": "Missing 'games' field in request"}), 400

        recommendations = nfcModel.recommend_based_on_games(user_games)
        return jsonify({"recommended_games": recommendations})

    except Exception as e:
        print(f"Error processing recommendations: {str(e)}")
        return jsonify({'error': 'Server error during recommendation'}), 500

if __name__ == '__main__':
    print("Starting Flask server...")
    app.run(host='0.0.0.0', port=port)