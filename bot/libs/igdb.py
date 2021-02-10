import time
import requests

class Igdb:
    def __init__(self, clientID, clientSecret):
        try:
            self._clientID = clientID # ***REMOVED***
            self._clientSecret = clientSecret # ***REMOVED***
            self._session = requests.Session()
            self._auth()
            headers = {
                'Client-ID': self._clientID,
                'Authorization': f'Bearer {self._accessToken}',
                'Accept': 'application/json'
            }
            self._session.headers.update(headers)
        except TypeError:
            raise TypeError("You Forget to define IGDB ClientID or ClientSecret or both") from None
        except Exception as exc:
            raise NotImplementedError(f"Failed to instanciate IGDB Object") from exc

    def _auth(self):
        response = self._session.get(f'https://id.twitch.tv/oauth2/token?client_id={self._clientID}&client_secret={self._clientSecret}&grant_type=client_credentials')
        self._accessToken = response['access_token']
        self._expiration = time.time() + response['expires_in']

    def _check_expiration(self):
        if self._expiration <= time.time():
            self._auth()

    def search_game(game_name):
        response = self._session.post(url='https://api.igdb.com/v4/games', data=f'search "{game_name}"; fields "id,name,external_games,game_modes"')
        # game_modes: 1=Solo,2=multi,3=Coop, 5=MMO
        return response

    def find_game_from_steamID(self, steam_id):
        response = self._session(f'https://api.igdb.com/v4/external_games', data=f'fields "game"; where uid="{steam_id}" & category=1')
        return response

    def find_game_from_gogID(self, gog_id):
        response = self._session(f'https://api.igdb.com/v4/external_games', data=f'fields "game"; where uid="{gog_id}" & category=5')
        return response

    def get_external_id(igdbID)
        response = self._session.post(f'https://api.igdb.com/v4/external_games', data=f'fields "category,uid,game"; where game = {igdbID}')
        # category: 1=steam,5=gog,11=microsoft,14=twitch
        return response