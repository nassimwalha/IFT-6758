import json
import requests
import pandas as pd
import logging


logger = logging.getLogger(__name__)


class ServingClient:
    def __init__(self, ip: str = "127.0.0.1", port: int = 5000, features=None):
        self.base_url = f"http://{ip}:{port}"
        logger.info(f"Initializing client; base URL: {self.base_url}")

        if features is None:
            features = ["distance"]
        self.features = features

        # any other potential initialization

    def predict(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Formats the inputs into an appropriate payload for a POST request, and queries the
        prediction service. Retrieves the response from the server, and processes it back into a
        dataframe that corresponds index-wise to the input dataframe.
        
        Args:
            X (Dataframe): Input dataframe to submit to the prediction service.
        """
        json_body = json.loads(X.to_json())
        prediction = requests.post(self.base_url+"/predict", json = json_body).json()
        return pd.DataFrame({"Goal_Probability": prediction}).set_index(X.index)

    def logs(self) -> dict:
        """Get server logs"""
        response_as_list = requests.get(self.base_url+"/logs").json()
        return {i: element for i, element in enumerate(response_as_list)}

    def download_registry_model(self, workspace: str, model: str, version: str) -> str:
        """
        Triggers a "model swap" in the service; the workspace, model, and model version are
        specified and the service looks for this model in the model registry and tries to
        download it. 

        See more here:

            https://www.comet.ml/docs/python-sdk/API/#apidownload_registry_model
        
        Args:
            workspace (str): The Comet ML workspace
            model (str): The model in the Comet ML registry to download
            version (str): The model version to download
        """
        model_dict = {"workspace": workspace, "model": model, "version": version}
        return requests.post(self.base_url+"/download_registry_model", json=model_dict).text

# #Testing
# from util.data_aquisition import generate
# from util.engineered_data_frame import engineered_data_frame
# import joblib
# from pathlib import Path
# import numpy as np
#if __name__=='__main__':
#     client = ServingClient(port = 5000)
#     print(client.logs())
#     print(client.download_registry_model("nassim-walha", "xgb-tuned-all", "1.0.0"))
#     print(client.logs())
#     data = generate(seasons=[2019], play_offs=[False])
#     df = engineered_data_frame(data)
#     features_columns = ['Period_Time_Seconds', 'Period', 'X_Coordinate', 'Y_Coordinate', 'Distance_Net', 'Angle',
#                         'Shoot_Type', 'Last_Event_Type', 'Last_Coordinate_X', 'Last_Coordinate_Y',
#                         'Time_Between_Events', 'Distance_Last_Event', 'Rebond', 'Delta_Angle', 'Speed',
#                         'Powerplay_Since', 'Friendly_Non_Goalies', 'Opponent_Non_Goalies']
#     df_all_features = df[features_columns]
#     df_all_features = df_all_features.dropna()
#     df_all_features = df_all_features[df_all_features.Speed != np.inf]
#     my_transformer = joblib.load(Path("/Users/nassimwalha/Desktop/IFT-6758/notebooks/models/all_features_transformer.joblib"))
#     X = pd.DataFrame(my_transformer.transform(df_all_features.iloc[0:10])).iloc[3:5]
#     print(client.predict(X))



