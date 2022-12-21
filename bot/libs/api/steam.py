import os, sys
from discord.errors import HTTPException
import requests
import json
import logging
import time

from requests.models import HTTPError

class Steam:
    def __init__(self, apikey):
        self._apikey = apikey
        self._session = requests.Session()
        self._session.headers.update({'x-webapi-key': self._apikey, 'Accept': 'application/json'})
        self.whoIimport = ''
        self._logger = logging.getLogger('discord')

    def get_User_Owned_Games(self, steam_id):
        try:
            # check if the bot can access to the profile
            query = self._session.get(f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?l=english&steamids={steam_id}")
            visibility = json.loads(query.content)['response']['players'][0]['communityvisibilitystate']
            self.whoIimport = json.loads(query.content)['response']['players'][0]['personaname']
            if visibility != 1:
                result = self._session.get(f"https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/?l=english&steamid={steam_id}&include_appinfo=1&include_played_free_games=1")
                logging.debug(result.content)
                if hasattr(result, 'content'):
                    return json.loads(result.content)
                else:
                    return False
            else:
                raise UserWarning("Your profil is not publicly visible, i can't read your library")
        except TypeError as err:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            logging.error(f'{fname}({exc_tb.tb_lineno}): {err}')
            raise TypeError from err
        except Exception as err:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            logging.error(f'{fname}({exc_tb.tb_lineno}): {err}')
            raise Exception(f'{fname}({exc_tb.tb_lineno}): {err}') from err

    def get_game_info_from_store(self, game_id):
        try:
            req = self._session.get(f'https://store.steampowered.com/api/appdetails?l=english&appids={game_id}')
            result = json.loads(req.content)
            if result[f'{game_id}']:
                if result[str(game_id)]['success'] is True:
                    return result[f"{game_id}"]['data']
                else:
                    raise ValueError(f"steam store don't know for the game_id {game_id}")
            else:
                raise ValueError(f"steam store has responded badly for game_id #{game_id}")
        except requests.exceptions.RequestException as err:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            self._logger.error(f'{fname}({exc_tb.tb_lineno}): {err}')
