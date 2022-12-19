from ift6758.ift6758.client.serving_client import ServingClient
from notebooks.util.util.data_aquisition import PbPData
from notebooks.util.util.engineered_data_frame import engineered_data_frame
import requests, joblib, time, re, os
import numpy as np
import pandas as pd

features_columns = ['Period_Time_Seconds', 'Period', 'X_Coordinate', 'Y_Coordinate', 'Distance_Net', 'Angle',
                    'Shoot_Type', 'Last_Event_Type', 'Last_Coordinate_X', 'Last_Coordinate_Y',
                    'Time_Between_Events', 'Distance_Last_Event', 'Rebond', 'Delta_Angle', 'Speed',
                    'Powerplay_Since', 'Friendly_Non_Goalies', 'Opponent_Non_Goalies']
package_directory = os.path.dirname(os.path.abspath(__file__))


class GameClient:

    def __init__(self, game_id: str, ip: str = "127.0.0.1", port: int = 5000):
        # Check whether the game_id is valid
        assert re.fullmatch(r"\d*", game_id) and len(game_id) == 10, "Game id must be a string of 10 digits"
        self.game_id = game_id
        self.serving_client = ServingClient(ip=ip, port=port)
        self.home = None
        self.away = None
        self.period = None
        self.time_left_in_period = None
        self.home_goals = None
        self.away_goals = None
        self.home_sum_of_expected_goals = 0
        self.away_sum_of_expected_goals = 0
        self.df = pd.DataFrame(columns=features_columns + ["Goal_Probability"])  # Df to be outputted in the webpage
        self.last_event_index = -1  # Set as index of last goal or shot in self.full_data_df.
        self.feature_transformer = joblib.load(os.path.join(package_directory, 'all_features_transformer.joblib'))

    def ping_game(self):
        # 1) Download game data.
        df_downloaded_full = self.download_game_data()  # Includes features_columns and Attacking_Team
        df_downloaded = df_downloaded_full[features_columns]  # Includes only features_columns
        # 2) Filter out seen events and update last_event_index.
        df_new_events = df_downloaded.iloc[self.last_event_index + 1:]
        self.last_event_index = len(df_downloaded) - 1
        if len(df_new_events) > 0:
            # 3) Transform data.
            transformed_np_array = self.feature_transformer.transform(df_new_events)
            transformed_df = pd.DataFrame(transformed_np_array, index=df_new_events.index)
            # 4) Get prediction form model.
            prediction_df = self.serving_client.predict(transformed_df)
            # 5) Calculate sums of expected goals and update self.df
            temp_df = df_downloaded_full.loc[df_new_events.index].join(prediction_df)
            new_xg = temp_df.groupby(by="Attacking_Team")["Goal_Probability"].sum()
            self.home_sum_of_expected_goals += new_xg["home"]
            self.away_sum_of_expected_goals += new_xg["away"]
            self.df = pd.concat([self.df, df_downloaded.loc[df_new_events.index].join(prediction_df)])

    def download_game_data(self):
        """
        Downloads all available game data from the api.
        Extracts the new feature engineered data frame and other information needed for the web page.
        Returns data frame with all events from the beginning of the game, with the columns being  "features_columns",
        with the additional column "Attacking_Team" that determines whether the team performing the attack is "home" or
        "away".
        """
        # Download data from api

        ok = False
        while not ok:
            response = requests.get(f"https://statsapi.web.nhl.com/api/v1/game/{self.game_id}/feed/live/")
            ok = response.status_code == 200
            if not ok:
                time.sleep(2)

        current_game_data = response.json()

        # Generate feature engineered data frame
        saison = int(self.game_id[0:4])
        gameTypeNumber = self.game_id[4:6]
        gameType = "PR" if gameTypeNumber == "01" else "R" if gameTypeNumber == "02" else "P" if gameTypeNumber == "03" \
            else "A"

        data = [{"season": f"{saison}-{saison + 1}", "gameType": gameType, "data": [current_game_data]}]
        pbp_data = PbPData(data=data)
        df = engineered_data_frame(pbp_data)

        # Extract other information needed for the webpage
        self.home = current_game_data["gameData"]["teams"]["home"]["name"]
        self.away = current_game_data["gameData"]["teams"]["away"]["name"]
        self.period = current_game_data["liveData"]["linescore"]["currentPeriod"]
        self.time_left_in_period = current_game_data["liveData"]["plays"]["allPlays"][-1]["about"][
            "periodTimeRemaining"]
        self.home_goals = current_game_data["liveData"]["boxscore"]["teams"]["home"]["teamStats"]["teamSkaterStats"][
            "goals"]
        self.away_goals = current_game_data["liveData"]["boxscore"]["teams"]["away"]["teamStats"]["teamSkaterStats"][
            "goals"]

        # Clean the data frame
        df_all_features = df[features_columns].copy()
        df_all_features.loc[:, "Attacking_Team"] = df.apply(
            lambda row: "home" if row["Team_Attack"] == self.home else "away", axis=1)
        df_all_features = df_all_features.dropna()
        df_all_features = df_all_features[df_all_features.Speed != np.inf]
        df_all_features.reset_index(inplace=True, drop=True)
        return df_all_features
