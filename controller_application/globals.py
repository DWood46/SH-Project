#!venv/Scripts/python.exe
from threading import Lock
import configparser

config = configparser.ConfigParser()
config.read('config.ini')

'''GLOBALS'''
#SERVER
server_host = config['SERVER']['host']
server_port = config['SERVER']['port']
server_pass = config['SERVER']['password']

#OBS
obs_host = config['OBS']['host']
obs_port = config['OBS']['port']
obs_pass = config['OBS']['password']

#APPLICATION
try:
    polling_speed = int(config['APPLICATION']['polling_speed'])
except:
    print("Defaulting to 500ms polling speed")
    polling_speed = 500 #default if failed to parse int

#Dictionary object that is output as a JSON object to the WebServer
out_json = {}

game = 0

db_conn = None

mutex = Lock()