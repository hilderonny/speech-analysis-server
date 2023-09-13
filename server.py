# Webserver for Web- and API-Access to transcription and translation services
# Created 2023 by @hilderonny
# See https://chat.openai.com/c/25113a90-be04-41d9-8649-71ae41870663

import configparser
from flask import Flask, request, send_from_directory
import os

config = configparser.ConfigParser()
config.read("config.ini")
UPLOAD_DIR = config["Processor"]["uploadDir"]
OUTPUT_DIR = config["Processor"]["outputDir"]
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

app = Flask(__name__)

# Hochladen von Dateien oder Formular anzeigen
@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            filename = os.path.join(UPLOAD_DIR, file.filename)
            print(filename)
            file.save(filename)
    return '''
    <!doctype html>
    <title>Datei-Upload</title>
    <h1>Datei hochladen</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    '''

# Prüfen auf Vorhandensein voin Ergebnisdateien. 404 heißt, noch nix da
@app.route("/output/<path:name>")
def download_file(name):
    return send_from_directory(OUTPUT_DIR, name, as_attachment=False)

if __name__ == '__main__':
    app.run(debug=True)
