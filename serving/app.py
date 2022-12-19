"""
If you are in the same directory as this file (app.py), you can run run the app using gunicorn:
    
    $ gunicorn --bind 0.0.0.0:<PORT> app:app

gunicorn can be installed via:

    $ pip install gunicorn

"""
import os
from pathlib import Path
import logging
from flask import Flask, jsonify, request, abort
import sklearn
import pandas as pd
import joblib
from comet_ml import API
from xgboost import XGBClassifier
from multiprocessing import Process

import ift6758


LOG_FILE = os.environ.get("FLASK_LOG", "flask.log")


app = Flask(__name__)
MODEL = None


#Stores a mapping from (workspace, model, version) to filename (path) in the system
#Supported models are exactly the models included here
#If a model is included, but there is no file on the system for the corresponding path,
#The model will be downloaded from comet
MODEL_TO_PATH = {"nassim-walha":
    {"xgb-all": {"1.0.0": Path("models")/"xgb_all_features.json"},
     "xgb-tuned-all": {"1.0.0" :Path("models")/"xgb_tuned_all_features.json"}}}

AVAILABLE_MODELS = [(i,j,k) for i in MODEL_TO_PATH for j in MODEL_TO_PATH[i] for k in MODEL_TO_PATH[i][j]]

def load_model(model_dict):
    """
    Loads the model defined by model_dict.
    model_dict contains the keys "workspace", "model", "version".
    Assumes the model described by model_dict exists on comet.
    First checks whether the model is on the local system. If yes, it is loaded.
    If not, it tries to download it from comet.
    If the download was successful, the model is loaded, otherwise the old model is kept.
    Returns a response message.
    """
    workspace = model_dict["workspace"]
    model = model_dict["model"]
    version = model_dict ["version"]
    global MODEL
    # Check whether the model is available in the system
    if os.path.exists(MODEL_TO_PATH[workspace][model][version]):
        app.logger.info("Loading model " + str((workspace, model, version)) + " from the system.")
        temp_model = XGBClassifier()
        temp_model.load_model(MODEL_TO_PATH[workspace][model][version])
        MODEL = temp_model
        app.logger.info("Model loaded successfully.")
        return "Model found on the system and was loaded successfully."
    else:
        app.logger.info("Model " + str((workspace, model, version)) + " not available on the system,"
                                                                      "trying to download.")
        try:
            # Trying to download the model.
            api = API(api_key=os.environ.get('COMET_API_KEY'))
            api.download_registry_model(workspace=workspace, registry_name=model, version=version,
                                        output_path=Path("models/"))
        except:
            app.logger.exception("Error happened while downloading the model. Keeping old model.")
            return "Tried to download model but download was unsuccessful. Keeping current model."
        else:
            app.logger.info("Model " + str((workspace, model, version)) + " downloaded successfully.")
            temp_model = XGBClassifier()
            temp_model.load_model(MODEL_TO_PATH[workspace][model][version])
            MODEL = temp_model
            app.logger.info("Model " + str((workspace, model, version)) + " loaded successfully and is ready to use.")
            return "Model downloaded and loaded successfully."


@app.before_first_request
def before_first_request():
    """
    Hook to handle any initialization before the first request (e.g. load model,
    setup logging handler, etc.)
    """
    logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
                        format='%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')

    app.logger.info('Loading base model.')
    base_model_dict = {"workspace": "nassim-walha", "model": "xgb-all", "version": "1.0.0"}
    load_model(base_model_dict)

@app.route("/logs", methods=["GET"])
def logs():
    """Reads data from the log file and returns them as the response"""
    app.logger.info("Received GET request on /logs.")

    with open(LOG_FILE) as f:
        response = [line.rstrip() for line in f]

    return jsonify(response)  # response must be json serializable!


@app.route("/download_registry_model", methods=["POST"])
def download_registry_model():
    """
    Handles POST requests made to http://IP_ADDRESS:PORT/download_registry_model

    The comet API key should be retrieved from the ${COMET_API_KEY} environment variable.

    Recommend (but not required) json with the schema:

        {
            workspace: (required),
            model: (required),
            version: (required),
            ... (other fields if needed) ...
        }
    
    """

    # Get POST json data
    json = request.get_json()
    app.logger.info("Recieved POST request on /download_registry_model.")
    app.logger.info(json)
    #Check whether all information is available
    if "workspace" not in json or "model" not in json or "version" not in json:
        app.logger.info("Request body missing required information.")
        return jsonify("Missing model information in request body. Must include: workspace, model, and version."), 400

    # Check whether information corresponds to an available model
    workspace = json ["workspace"]
    model = json["model"]
    version = json["version"]
    flag = False
    if workspace in MODEL_TO_PATH:
        if model in MODEL_TO_PATH[workspace]:
            if version in MODEL_TO_PATH[workspace][model]:
                flag = True
    if not flag:
        app.logger.info("Request body information doesn't correspond to a supported model.")
        response_string = "Request information doesn't correspond to a supported model.\n " \
                          "List of supported supported models (workspace, model, version): "+str(AVAILABLE_MODELS)+"."
        return jsonify(response_string), 400


    response = load_model(json)

    app.logger.info(response)
    return jsonify(response)  # response must be json serializable!


@app.route("/predict", methods=["POST"])
def predict():
    """
    Handles POST requests made to http://IP_ADDRESS:PORT/predict

    Returns predictions
    """
    # Get POST json data
    json = request.get_json()
    app.logger.info(json)

    #First try block to check whether json request has the correct structure, if yes, it is getting parsed
    try:
        temp_dict = {column :[json[column] [key] for key in sorted(list(json[column].keys())) ] for column in json}
        X = pd.DataFrame(temp_dict)
        if len(X.columns)!=32:
            raise Exception("Input with a number of columns different than 32.")
    except:
        app.logger.exception("Exception happened during the parsing of input.")
        response ="Invalid prediction input. Please send the result of DataFrame.to_json() applied to the " \
                  "input data frame in your request. The data frame should have 32 columns."
        return jsonify(response), 400

    #Second try block to perform the prediction.
    try:
        response = MODEL.predict_proba(X)[:, 1].tolist()
    except:
        app.logger.exception("Prediction error.")
        return jsonify("Prediction error. Probably caused by wrong input values."), 400


    app.logger.info(response)
    return jsonify(response)  # response must be json serializable!
