# speech-analysis-server

Webserver for transcribing and translating audio files via whisper based on python.

## Requirements

- Python 3 with `pip`
- [cuBLAS for CUDA 11](https://developer.nvidia.com/cublas)
- [cuDNN 8 for CUDA 11](https://developer.nvidia.com/cudnn)
- Or together downloaded from https://github.com/Purfview/whisper-standalone-win/releases/tag/libs and put into library folder of ctranslate2 python package

## Installation

When using the server for the first time an internet connection is required to download the AI models.
Or the models must be downloaded manually.

```sh
pip install git+https://github.com/hilderonny/argos-translate
pip install faster-whisper
```

## Running the server

```
python server.py
```