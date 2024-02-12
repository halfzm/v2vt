# 带有口型同步功能的视频翻译
转录视频语音并翻译，语音克隆，口型同步，压制字幕，支持中英视频互相转换


## 效果演示
详见`res.mp4`

<!-- <video>
<source src="https://github.com/halfzm/v2vt/blob/main/res.mp4" type="video/mp4">
</video> -->

## 技术栈
- 语音识别 [fast-whisper](https://github.com/SYSTRAN/faster-whisper)
- 文本翻译 [facebook/m2m](https://huggingface.co/facebook/m2m100_1.2B)
- 音色克隆 
  - [openvoice](https://github.com/myshell-ai/OpenVoice)（对于中文，使用微软的[TTS](https://github.com/skygongque/tts)替换openvoice自带的TTS模型）
  - [TTS](https://github.com/coqui-ai/TTS)
- 口型同步：[videotalking](https://github.com/OpenTalker/video-retalking)
- 脸部超分：[gfpgan](https://github.com/TencentARC/GFPGAN)
- 视频整合 [pyvideotrans](https://github.com/jianchang512/pyvideotrans)



## 环境搭建
1. 安装[ffmpeg](https://ffmpeg.org/)并添加到环境变量，或者是直接把相应可执行程序放到当前目录ffmpeg文件夹
```
ffmpeg
   |- ffmpeg.exe
   |- ffprobe.exe
...
```

2. 安装依赖
```
git clone git@github.com:halfzm/v2vt.git

conda create -n v2vt_clone python=3.11.0
conda activate v2vt_clone

cd v2vt_clone
pip install -r requirements.txt
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

3. 把`openvoice`中需要的[模型](https://myshell-public-repo-hosting.s3.amazonaws.com/checkpoints_1226.zip)放到`openvoice_checkpoints`文件夹中，目录结构应该如下[optional]
```
openvoice_checkpoints
   |- base_speakers
    |- ...
   |- converter
    |- ...
...
```

4. 把`tts`中需要的[模型](https://huggingface.co/coqui/XTTS-v2/tree/main)放到`tts_models`文件夹中，目录结构应该如下
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

5. 把`video_retalking`中需要的[模型](https://drive.google.com/drive/folders/18rhjMpxK8LVVxf7PI6XwOidt8Vouv_H0?usp=share_link)放到`video-retalking/checkpoints`文件夹中，目录结构应该如下
```
video-retalking
   |- checkpoints
    |- ...
...
```


## 使用说明
- 快速启动
```
python app.py
```
- 关于输入  
输入视频不能太短，否则语音克隆的时候报错（最好不要低于5S）

- 关于输出  
默认是输出到当前目录下的output.mp4，也可以在webui中直接下载


## 其它
licence和code_of_conduct和[video-retalking](https://github.com/OpenTalker/video-retalking)项目一致  
详见LICENSE和CODE_OF_CONDUCT