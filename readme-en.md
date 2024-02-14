<p align="left">
    English ｜ <a href="readme.md">中文</a>
</p>
<h1 align="left">
  Video to Video Translation with Lip Synchronization 
</h1>

- video to video translation  
- voice clone  
- lip synchronization  
- add subtitles  
- support chinese and english  

## Demo
you can see it at `res.mp4`.

<!-- <video>
<source src="https://github.com/halfzm/v2vt/blob/main/res.mp4" type="video/mp4">
</video> -->

## Tech Route
- Speech Recognition: [fast-whisper](https://github.com/SYSTRAN/faster-whisper)
- Text Translation: 
  - ~~[facebook/m2m](https://huggingface.co/facebook/m2m100_1.2B)~~
  - [translators](https://github.com/UlionTse/translators)
- Voice Clone: 
  - [openvoice](https://github.com/myshell-ai/OpenVoice)（对于中文，使用微软的[TTS](https://github.com/skygongque/tts)替换openvoice自带的TTS模型）
  - [TTS](https://github.com/coqui-ai/TTS)
- Lip Synchronization：[videotalking](https://github.com/OpenTalker/video-retalking)
- Face Restore：[gfpgan](https://github.com/TencentARC/GFPGAN)
- Viceo Combine: [pyvideotrans](https://github.com/jianchang512/pyvideotrans)



## Enviroment
1. Install [ffmpeg](https://ffmpeg.org/) and add it to the enviroment variable, or simply put the executable file in the `ffmpeg` directory, and the directory structure should be as follows:
```
ffmpeg
   |- ffmpeg.exe
   |- ffprobe.exe
...
```

2. Install dependencies
```
git clone git@github.com:halfzm/v2vt.git

conda create -n v2vt_clone python=3.11.0
conda activate v2vt_clone

cd v2vt_clone
pip install -r requirements.txt
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

3. Put the pretrained models needed by [`openvoice`](https://myshell-public-repo-hosting.s3.amazonaws.com/checkpoints_1226.zip) in the `openvoice_checkpoints` directory, and the directory structure should be as follows:[optional]
```
openvoice_checkpoints
   |- base_speakers
    |- ...
   |- converter
    |- ...
...
```

4. Put the pretrained models needed by [`tts`](https://huggingface.co/coqui/XTTS-v2/tree/main)in the `tts_models` directory，and the directory structure should be as follows:
```
tts_models
   |- tts_models--multilingual--multi-dataset--xtts_v2
    |- config.json
    |- model.pth
    |- speakers_xtts.pth
    |- vocal.json
   |- ...
...
```

5. Put the pretrained models needed by[`video_retalking`](https://drive.google.com/drive/folders/18rhjMpxK8LVVxf7PI6XwOidt8Vouv_H0?usp=share_link) in the `video-retalking/checkpoints`directory，and the directory structure should be as follows:
```
video-retalking
   |- checkpoints
    |- ...
...
```


## Usage
- Quick start
```
python app.py
```
- Input file  
The input video should not be too short, otherwise an error will be reported when the voice is cloned (preferably not lower than 5S)

- Output file  
By default, you can find the outfile in current work directory, named `outpu.mp4`, which can also be downloaded directly from the webui.


## Others
About licence and code_of_conduct, we follow the [video-retalking](https://github.com/OpenTalker/video-retalking) project.  
You can see the details at `LICENSE` and `CODE_OF_CONDUCT`.