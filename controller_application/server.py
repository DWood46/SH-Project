#!venv/Scripts/python.exe
from flask import Flask, redirect, url_for, render_template, request, send_file, jsonify
from flask_cors import CORS
import obswebsocket, obswebsocket.requests
import json
import requests
import time
import threading
import sys
import configparser
import glob
import os
import logging

#local imports
import globals

#
app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
CORS(app)

#disable all loggers for the web server
app.logger.disabled = True
log = logging.getLogger('werkzeug')
log.disabled = True
    
@app.route('/', methods=['GET', 'POST'])
def index():
    error = None
    if request.method == 'POST':
        if request.form['password'] != globals.server_pass:
            error = 'incorrect password'
        #if correct, allow access
        else:
            #send the current OBS address/password so the config can communicate too
            obs_address = globals.obs_host + ":" + globals.obs_port
            return render_template('updater.html', obs_address=obs_address, obs_password=globals.obs_pass)
    return render_template('login.html', error=error)
    
@app.route("/overlays/<path:path>")
def overlay(path):
    return render_template("overlays/" + path + ".html")

@app.route("/update", methods=["POST"])
def update():
    update_json(request.form)
    return "OK"
	#return redirect("/")    #redirect to index
    
@app.route("/update_game", methods=["POST"])
def update_game():
    change_game(request.form)
    return "OK"
	#return redirect("/")    #redirect to index

@app.route("/out.json", methods=["POST", "GET"])
def databaseJSON():
    try:
        return jsonify(globals.out_json)
    except Exception as e:
        return str(e)

def update_json(information):
    """
    Update the player names in the output JSON dict
    
    :param information: dict object containing list of names
    """
    #for each value in the update request, update the JSON output to match
    for key in information:
        index = int(key)
        if key in globals.out_json["players"]:
            globals.out_json["players"][index]["name"] = information[key]
        else:
            globals.out_json["players"][index] = {"name": information[key], "wins": 0}

def change_game(information):
    """
    Update the current game with the one requested by the web configuration.
    
    :param information: dict object containing the game ID
    """
    game_index = int(information["game"]) + 1
    globals.game = game_index 

def run():
    """
    Run the web server
    """
    #use SSL
    if os.path.exists("ssl/cert.crt") and os.path.exists("ssl/key.key"):
        app.run(host=globals.server_host, port=globals.server_port, ssl_context=('ssl/cert.crt', 'ssl/key.key'))
    #dont use SSL
    else:
        print("WARNING: no certificates found, not using SSL")
        app.run(host=globals.server_host, port=globals.server_port)