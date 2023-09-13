# Command line program to send a file to the server and wait for completion
# python client.py file_path.ext

import requests
import sys
import time
import os

url = "http://127.0.0.1:5000/"  # Die URL, auf der dein Flask-Server läuft

# Die Datei, die du hochladen möchtest
file_path = sys.argv[1]

# Datei als 'file'-Parameter im POST-Request senden
with open(file_path, 'rb') as f:
    files = {'file': f}
    response = requests.post(url, files=files)

processing_completed = False

_, file_name = os.path.split(file_path)
output_url = url + "output/" + file_name + ".json"

while processing_completed == False:
    print("Checking result")
    response = requests.get(output_url)
    if response.status_code == 200:
        print(response.text)
        processing_completed = True
    else:
        time.sleep(5)