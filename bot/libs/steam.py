import requests
import json
import logging
import time

class Steam:
    def __init__(self, apikey):
        self._apikey = apikey
        self._session = requests.Session()
        self._session.headers.update({'x-webapi-key': self._apikey, 'Accept': 'application/json'})

    def get_User_Owned_Games(self, steam_id):
        try:
            result = self._session.get(f"https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/?&steamid={steam_id}&include_appinfo=1&include_played_free_games=1")
            logging.debug(result.content)
            if hasattr(result, 'content'):
                return json.loads(result.content)
            else:
                return false
        except TypeError as err:
            logging.error(err)
            raise TypeError from err
        except Exception as err:
            logging.error(err)
            raise Exception from err

    def get_game_info_from_store(self, game_id):
        try:
            req = self._session.get(f'https://store.steampowered.com/api/appdetails?appids={game_id}')
            result = json.loads(req.content)
            if str(game_id) in result:
                if result[f"{game_id}"]['success'] == True:
                    return result[f"{game_id}"]['data']
                else:
                    return None
        except requests.exceptions.RequestException as err:
            logging.error(f"game_id={game_id} {err}")
            raise UserWarning('Something went wrong when asked steam for more info. Please retry tomorrow.')
