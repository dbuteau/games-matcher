import requests
import json

class Gog:
    def __init__(self, apikey):
        self._apikey = apikey
        self._session = requests.Session()
        self._auth()
        self._session.headers.update({'Authorization': f'Bearer {self._accesstoken}'})

    def _auth(self, refresh=False):
        if refresh:
            grant_type = 'authorization_code'
        else:
            grant_type = 'refresh_token'
        self._session.get(f'https://auth.gog.com/token?client_id={self._clientID}&client_secret={self._clientSecret}&grant_type={grant_type}')

    def get_User_Owned_Games():
        result = self._session.get(f'https://embed.gog.com/account/getFilteredProducts?mediaType=1')
        return json.loads(result['products'])

    """
    gog api don't return "feature" field will maybe work the day they implement it back
    def is_multiplayer(game_id):
        result = self._session.get(f'https://api.gog.com/products/{game_id}')
        for feature in result['features']:
            if feature == 'Multi-player':
                return True
        return False
    """