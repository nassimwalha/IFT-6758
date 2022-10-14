import os
import requests
import re
import json
import time
from tqdm import tqdm
import shutil

class PbPData():
    """
    Class representing play_by_play data.

    -The actual data is stored in the attribute self.data.
    -This class overloads the __add__() operator, resulting in concatenating the data attributes
    of the operands and creating a new PbPData object out of the concatenated data.
    -If the data is already present in your system, it will be loaded locally, otherwise it will be downloaded
    from the NHL API and saved in your system for later use.

    Attributes
    ----------
    data : a list of dict objects representing the data. Each element corresponds to the play-by-play data of
    all games of a given season and a given game type (regular or play-off).

    """
    def __init__(self, download_data: dict = None , data: list =[]):
        """
        Initializes a PbPData object. Can be used in three modes:
        1) If download_data is specified, the games data corresponding to the specified season and game type
        (play-off or regular) will be loaded from your system (if they already exist) of downloaded from
        the NHL api and saved to your system.
        2) If the download_data is not specified and data is specified, a PbPData will be created
        with the self.data attribute having the specified data.
        3) If neither is specified, a PbPData will be created with the self.data attribute being an empty list.
        :param download_data: A dictionary contatining information about the data you want to load. It MUST contain
        a 'saison' key with an integer value corresponding to the season of the games you want to get (for example
        2016 for the season 2017-2017), and a 'play_off' key with a boolean value set to True if you want play-off
        fames and to False if you want regular games. You can add an optional key 'root_data_path' to specify
        where you store or want to store your data. If this key is not included, the default data path is "../data".
        :param data: specified data to be wrapped in a PdPData object.
        """
        if download_data is not None:
            self.data = self.__download(download_data['saison'], download_data['play_off'], download_data.get('root_data_path', "../data"))
        else :
            self.data = data

    def __add__(self, other):
        return PbPData(data = self.data + other.data)

    def __download(self, saison: int, play_off: bool, root_data_path: str = "../data" )-> list:
        path = root_data_path + ("/regular_season" if not play_off else "/play_off")+f"/{saison}-{saison + 1}/"
        data=[]

        if os.path.exists(path):
            print("Data is available on your system. Will be loaded from: "+os.path.abspath(path))
            for file_name in os.listdir(path):
                if file_name.endswith('.json'):
                    with open(path+file_name, 'r') as f:
                        data.append(json.load(f))

            data = [{"season": f"{saison}-{saison + 1}", "gameType": "R" if not play_off else "P", "data": data}]
            return data

        print("Data is not available on your system. Will be downloaded and saved in: "+os.path.abspath(path))

        #Look for the list of game IDs (playoff or regular depending on play_off) of the season
        ok = False
        params = {"season": f"{saison}{saison + 1}", "gameType": "R" if not play_off else "P"}
        while not ok:
            response = requests.get(f"https://statsapi.web.nhl.com/api/v1/schedule", params=params)
            ok = response.status_code == 200
            if not ok:
                time.sleep(2)
        games = response.text
        gameIDs = re.findall(r'(?<="gamePk" : )[0-9]*(?=,)', games)

        try:
            #Download and save the PbP data of the found games
            for id in tqdm(gameIDs, desc="Downloading..."):

                ok = False
                while not ok:
                    response = requests.get(f"https://statsapi.web.nhl.com/api/v1/game/{id}/feed/live/")
                    ok = response.status_code == 200
                    if not ok:
                        time.sleep(2)
                current_game_data = response.json()
                data.append(current_game_data)
                #Saving the current_game_data
                os.makedirs(path, exist_ok = True)
                with open(path+f"{id}.json", 'w') as f:
                        json.dump(current_game_data, f)
        except:
            print(f"An error occured while downloading the data for season {saison}-{saison + 1} and game type "
                  +f"{'R' if not play_off else 'P'}. Directory "+path+" will be deleted and an empty data list will"
                  +" be returned. Please retry downloading again.")
            shutil.rmtree(path)
            return []

        data = [{"season": f"{saison}-{saison + 1}", "gameType": "R" if not play_off else "P", "data": data}]
        return data

def generate (seasons: list = [2016, 2017, 2018, 2019, 2020], play_offs: list = [True, False] )-> PbPData:
    data = PbPData()
    for season in seasons:
        for play_off in play_offs:
            config =  {"saison": season, "play_off": play_off}
            data = data + PbPData(config)
    return data

def test_func():
    print(os.getcwd())