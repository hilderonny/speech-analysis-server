# Background service which processes all files in the upload directory
# and writes the results into the output directory.

import configparser
import time
import os
import json
import datetime

def init():
    global UPLOAD_DIR, OUTPUT_DIR
    config = configparser.ConfigParser()
    config.read("config.ini")
    UPLOAD_DIR = config["Processor"]["uploadDir"]
    OUTPUT_DIR = config["Processor"]["outputDir"]
    ARGOS_DATA_DIR = config["Processor"]["argosDataDir"]
    WHISPER_DATA_DIR = config["Processor"]["whisperDataDir"]
    WHISPER_MODEL = config["Processor"]["whisperModel"]
    USE_GPU = config["Processor"]["useGpu"] == "true"
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    argos_exists = os.path.exists(ARGOS_DATA_DIR)
    if not argos_exists:
        os.makedirs(ARGOS_DATA_DIR)
    whisper_exists = os.path.exists(WHISPER_DATA_DIR)
    if not whisper_exists:
        os.makedirs(WHISPER_DATA_DIR)
    print("Initializing Faster Whisper")
    global whisper_model
    from faster_whisper import WhisperModel    
    whisper_model_type = WHISPER_MODEL
    whisper_device = "cuda" if USE_GPU else "cpu"
    compute_type = "int8_float16" if USE_GPU else "int8"
    whisper_model = WhisperModel( model_size_or_path = whisper_model_type, device = whisper_device, local_files_only = False, compute_type = compute_type, download_root = WHISPER_DATA_DIR )
    print("Initializing Argos Translate")
    os.environ["ARGOS_PACKAGES_DIR"] = os.path.join(ARGOS_DATA_DIR, "packages")
    os.environ["ARGOS_DEVICE_TYPE"] = "cuda" if USE_GPU else "cpu"
    global argos_translation
    import argostranslate.translate
    if not argos_exists: # Download translation packages if not existing
        import argostranslate.package
        argostranslate.package.update_package_index()
        available_packages = argostranslate.package.get_available_packages()
        package_to_install = next(
            filter(
                lambda x: x.from_code == "en" and x.to_code == "de", available_packages
            )
        )
        argostranslate.package.install_from_path(package_to_install.download())
        del argostranslate.package
    argos_translation = argostranslate.translate.get_translation_from_codes("en", "de")

def translate_into_german(segments_en):
    translation_segments_de = list(map(lambda segment: { "start": segment["start"], "end": segment["end"], "text": argos_translation.translate(segment["text"]) }, segments_en))
    return translation_segments_de

def process_file(file_path):
    start_time = datetime.datetime.now()
    result = {}
    try:
        print("Processing file " + file_path)
        print("Transcribing")
        transcribe_segments_generator, transcribe_info = whisper_model.transcribe(file_path, task = "transcribe")
        transcribe_segments = list(map(lambda segment: { "start": segment.start, "end": segment.end, "text": segment.text }, transcribe_segments_generator))
        original_language = transcribe_info.language
        result["language"] = original_language
        result["original"] = { "segments": transcribe_segments, "fulltext":  "".join(map(lambda segment: segment["text"], transcribe_segments)) }
        if original_language == "de": # Deutsch brauchen wir weder uebersetzen noch in Englisch
            result["en"] = None
            result["de"] = result["original"]
        elif original_language == "en": # Englisch muss nicht ins Englische uebersetzt werden
            result["en"] = result["original"]
            print("Translating into german")
            segments_de = translate_into_german(result["en"]["segments"])
            result["de"] = { "segments": segments_de, "fulltext":  "".join(map(lambda segment: segment["text"], segments_de)) }
        else:
            print("Translating into english")
            translation_segments_generator_en, _ = whisper_model.transcribe(file_path, task = "translate")
            result["en"] = { "segments": list(map(lambda segment: { "start": segment.start, "end": segment.end, "text": segment.text }, translation_segments_generator_en)) }
            print("Translating into german")
            segments_de = translate_into_german(result["en"]["segments"])
            result["de"] = { "segments": segments_de, "fulltext":  "".join(map(lambda segment: segment["text"], segments_de)) }
        print("Deleting file " + file_path)
        os.remove(file_path)
    except Exception as ex:
        print(ex)
    finally:
        pass
    end_time = datetime.datetime.now()
    result["duration"] = (end_time - start_time).total_seconds()
    return result

def check_and_process_files():
    print("Checking for at least one file in " + UPLOAD_DIR)
    for file_name in os.listdir(UPLOAD_DIR):
        upload_file_path = os.path.join(UPLOAD_DIR, file_name)
        if os.path.isfile(upload_file_path):
            result = process_file(upload_file_path)
            json_result = json.dumps(result, indent=2)
            output_file_path = os.path.join(OUTPUT_DIR, file_name + ".json")
            print("Writing output file " + output_file_path)
            output_file = os.open(output_file_path, os.O_RDWR|os.O_CREAT)
            os.write(output_file, str.encode(json_result))
            os.close(output_file)
            print(json_result)
            return # Let the program wait a moment and recheck the uplopad directory

try:
    init()
    while True:
        check_and_process_files()
        time.sleep(3)
finally:
    pass
