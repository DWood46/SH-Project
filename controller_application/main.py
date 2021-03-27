#!venv/Scripts/python.exe
from flask import Flask, render_template, request, send_file
from flask_cors import CORS
import json
import logging
import obswebsocket, obswebsocket.requests
import sqlite3
import subprocess
import threading
import time
try:
    import tkinter as tk
    from tkinter import messagebox
except:
    import Tkinter as tk

#local imports
import server
import globals
import database

#constants
TIMER = 500 #miliseconds

loop = True
current_game = 0
current_scene = ""
games = None
obs_client = None

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

window = tk.Tk()
labels = []

pointer_values = {}

def reset_values():
    """
    Reset the values of the dictionary object tracking in-game progress.
    """
    globals.out_json = {"player_count": 0, "pointers": {}, "players": {}, "games": []}
    pointer_values = {}
    with open("json/games_list.json") as json_file:
        games = json.load(json_file)
        for game in games["games"]:
            globals.out_json["games"].append(game["name"])
        

def on_switch(message):
    """
    Handler function used by obs-websocket which keeps track of the scene that is currently
    in use.
    
    :param message:     Message to handle
    """
    global current_scene
    current_scene = message.getSceneName()
    
def run():
    """
    Check if the requested game has changed, kill the threads for the old game, and start the new one.
    """
    current_game = 0
    while(True):
        #continually check for a change in game
        if globals.game != current_game:
            #remove label indicating game in progress
            if current_game != 0:
                labels[current_game-1]["text"] = ""
            current_game = globals.game
            if current_game != 0:
                #kill threads for current running game
                loop = False
                #wait to allow all threads to close properly
                time.sleep(globals.polling_speed/1000)
                read_game()

def read_game():
    """
    Read the config file for the game selected, begin reading the pointer values.
    """
    global loop
    #mark game as running in the GUI
    labels[globals.game-1]["text"] = "Running..."
    
    #read info for selected game
    game_info = None
    try:
        game_dir = "json/" + games["games"][globals.game-1]["file_name"]
        with open(game_dir) as game_file:
            game_info = json.load(game_file)
    #malformed JSON file
    except json.decoder.JSONDecodeError:
        messagebox.showerror("Error", games["games"][globals.game-1]["file_name"] + " is malformed, cannot decode.")
        globals.game = 0
        labels[current_game-1]["text"] = ""
        return
    #no file found
    except FileNotFoundError:
        messagebox.showerror("Error", "Could not find configuration file '" + games["games"][globals.game-1]["file_name"] + "'. Please ensure the correct file is specified in games_list.json.")
        globals.game = 0
        labels[current_game-1]["text"] = ""
        return
    except:
        messagebox.showerror("Error", "Unexpected error reading configuration file.")
        globals.game = 0
        labels[current_game-1]["text"] = ""
        return
        
    #run the thread that processes each pointer specified in the config
    loop = True
    t = threading.Thread(target=game_loop, name="Pointer Loop", args=[game_info])
    t.setDaemon(True)
    t.start()

def game_loop(game_info):
    """
    Continually loop reading and processing data read from the game.
    
    :param game_info:   The dictionary object representation of the game config
    """
    global loop
    ms = time.time_ns()
    winner_declared = False;
    while(loop):
        #only process if a period of time has passed, but run first time without delay
        if time.time_ns() > ms:
            ms = time.time_ns() + (globals.polling_speed*1000)
            #check pointers
            if check_pointers(game_info["platform"], game_info["pointers"]) == 0:
                #if error in pointer checking, return
                loop = False
                break
                
            #retrieve the current player count specified
            if "player_count" in list(game_info["controller"]):
                player_count = check_json_object(game_info["controller"]["player_count"])
                globals.out_json["player_count"] = player_count
            else:   
                globals.out_json["player_count"] = 0
            
            #check if the match has finished
            if "match_finished" in list(game_info["controller"]):
                match_finished = check_json_object(game_info["controller"]["match_finished"])
                if match_finished:
                    #ensure that a winner hasn't already been declared
                    if not winner_declared:
                        winner = check_json_object(game_info["controller"]["winner"])
                        globals.out_json["winner"] = winner
                        if winner in globals.out_json["players"]:
                            name = globals.out_json["players"][winner]["name"]
                            #Create user if doesn't already exist
                            database.execute("INSERT OR IGNORE INTO users (username, games_won) VALUES (?, 0)", name)
                            #Increment games won by 1
                            database.execute("UPDATE users SET games_won = games_won + 1 WHERE username=?", name)
                            winner_declared = True
                else:
                    #mark that a winner hasnt been declared
                    winner_declared = False
                    if "winner" in list(globals.out_json):
                        globals.out_json.pop("winner")
            
            #check if the game is paused
            if "paused" in list(game_info["controller"]):
                paused = check_json_object(game_info["controller"]["paused"])
                if paused:
                    change_scene("pause")
                else:
                    change_scene("game")
                    
            #update/display player score information
            for i in range(1, globals.out_json["player_count"]+1):
                #if player information hasn't been written yet, ignore
                if i in globals.out_json["players"]:
                    current_player = globals.out_json["players"][i]["name"]
                    games_won = database.execute("SELECT games_won FROM users WHERE username=?", current_player)
                    if len(games_won) != 0:
                        globals.out_json["players"][i]["wins"] = games_won[0][0]

    #mark game as not running
    reset_values()

def check_pointers(platform, pointers):
    """
    Iterate over the list of multi-level pointers described in the games config and store
    them in a dictionary object. If the 'display' parameter is provided, add them to the
    dictionary object that is exposed on the web server.
    
    :param platform:    32 or 64 bit 
    :param pointers:    List of pointers to iterate over
    :return:            0 on failure, 1 on success
    """
    try:
        count = 0
        for pointer in pointers:
            count += 1
            temp = time.time_ns()
            args = [ pointer["window"], pointer["module"], pointer["initial_offset"] ] + pointer["offsets"]
            output = read_memory(platform, args)            
            #if error, return 0
            if output == "ERROR: no process found":
                messagebox.showinfo("Alert", games["games"][globals.game-1]["name"] + " process lost.")
                globals.game = 0
                return 0
            elif output == "ERROR: incorrect platform provided in config":
                messagebox.showerror("Error", "Incorrect platform provided in config file '" +  games["games"][globals.game-1]["file_name"] + "', must be 32 or 64.")
                globals.game = 0
                return 0
            
            #display on webserver if true
            if pointer["display"]:
                globals.out_json["pointers"][pointer["id"]] = output
            #store in list
            pointer_values[pointer["id"]] = output
    except KeyError:
        messagebox.showerror("Error", "Incorrect pointers values provided in '" +  games["games"][globals.game-1]["file_name"] + "', please reference the example configuration file provided.")
        globals.game = 0
        return 0
    return 1

def read_memory(platform, args):
    """
    Runs the MemoryReader process to read the games memory using the specified offsets.
    Inside args are the following:
        window: window name of the game
        module: module associated with the window to read memory values from (used to find base address)
        initial_offset: the initial offset added to the base address to begin reading from
        offsets: list of subsequent offsets to iterate through
    
    :param platform:    32 bit or 64 bit
    :param args:        Arguments that are passed to the MemoryReader process
    :return:            Value stored in memory at the specified address
    """
    #open the external process with the given parameters and return the output of std.out
    if platform == 32:
        proc = subprocess.Popen([r"memoryreader32.exe"] + args, stdout=subprocess.PIPE, universal_newlines=True)
    elif platform == 64:
        proc = subprocess.Popen([r"memoryreader64.exe"] + args, stdout=subprocess.PIPE, universal_newlines=True)
    else:
        return("ERROR: incorrect platform provided in config")
    output = proc.communicate()[0]
    return(output.rstrip())

def check_json_object(value):
    """
    Parses a JSON object in a game configuration file.
    
    If a string:    return the value from the games memory associated with the ID
    If an integer:  return the integer
    If a JSON dict: check the logic described in the dict
    
    :param value:   Object to parse
    :return:        Integer as described, or the integer at a game pointer location
    """
    #integer
    if isinstance(value, int):
        return value
    #dict
    elif isinstance(value, dict):
        return check_logic(value)
    #string
    elif isinstance(value, str):
        value = pointer_values[value]
        return int(value)
        
def check_logic(object):
    """
    Check the logic as described in the JSON dictionary object.
    
    In order to support multiple games and promote extensibility, a basic logic must
    be implemented using a config file. Operators are simple; add, subtract, multiply,
    divide, and equals. Values can by dynamically set using IDs for memory values,
    regular integers, or other operator objects which allows for a rudimentary logic to
    be established.
    
    :param object:  The dictionary object to be checked
    :return:        The result of the equation
    """
    #operators are described in the key of the dictionary
    type = list(object)[0]
    if type == "==":
        return check_json_object(object[type][0]) == check_json_object(object[type][1])
    elif type == "!=":
        return check_json_object(object[type][0]) != check_json_object(object[type][1])
    elif type == "+":
        return(check_json_object(object[type][0]) + check_json_object(object[type][1]))
    elif type == "-":
        return(check_json_object(object[type][0]) - check_json_object(object[type][1]))
    elif type == "*":
        return(check_json_object(object[type][0]) * check_json_object(object[type][1]))
    elif type == "/":
        return(check_json_object(object[type][0]) / check_json_object(object[type][1]))
    elif type == "&&":
        return check_json_object(object[type][0]) and check_json_object(object[type][1])
    elif type == "||":
        return check_json_object(object[type][0]) or check_json_object(object[type][1])
    return None

def change_scene(scene):
    """
    Changes the scene in OBS to the scene requested if it exists
    
    :param scene:   The scene to switch to
    """
    global obs_client
    scenes = obs_client.call(obswebsocket.requests.GetSceneList()).getScenes()
    #if the scene exists, change to it
    if any(x["name"] == scene for x in scenes):
        obs_client.call(obswebsocket.requests.SetCurrentScene(scene))

def change_game(game):
    globals.game = game

def draw_gui():
    """
    Draw the Tkinter GUI for the application
    """
    global window, labels
    count = 0
    tk.Label(window, text="Select a game").grid(column=0, row=0, padx=(5,10), pady=(10,0))
    for game in games["games"]:
        count += 1
        #create buttons and labels
        #button changes the game in progress
        btn = tk.Button(window, text=game["name"], command=lambda count=count: change_game(count))
        labels.append(tk.Label(window, text=""))
        btn.grid(column=0, row=count, padx=(10,5), pady=(10,10))
        labels[count-1].grid(column=1, row=count, padx=(5,10), pady=(10,10))
    window.title("Livestream Program")
    window.mainloop()

def main():
    global games, loop, obs_client
    #run flask server
    flask_thread = threading.Thread(target=server.run, name="Flask")
    flask_thread.setDaemon(True)
    flask_thread.start()
    
    #connect to OBS
    try:
        obs_client = obswebsocket.obsws(globals.obs_host, globals.obs_port, globals.obs_pass)
        obs_client.connect()
        obs_client.register(on_switch, obswebsocket.events.SwitchScenes)
    except obswebsocket.exceptions.ConnectionFailure:
        print("Error: OBS connection could not be made")
        exit()
    print("Connected to OBS using obs-websocket")
    
    #process list of games
    with open("json/games_list.json") as json_file:
        games = json.load(json_file)
    
    #setup database
    database.setup()
    
    #setup the dict storage that is used by the server/locally
    reset_values()
    
    #run main loop
    main_thread = threading.Thread(target=run, name="Main Loop")
    main_thread.setDaemon(True)
    main_thread.start()
    
    #draw GUI
    draw_gui()
            
if __name__ == "__main__":
    main()