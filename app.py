import os
import subprocess
import shutil
import gradio as gr

from s2st import Speech2SpeechTranslation
from utils import timer_decorator

# 当前执行目录
rootdir = os.getcwd()
# 添加环境变量 ffmpeg
ffmpeg_path = os.path.join(rootdir, "ffmpeg")
os.environ["PATH"] = ffmpeg_path + ";" + os.environ["PATH"]

s2st = Speech2SpeechTranslation(voice_clone_model="xtts", use_m2m_as_translator=False)


@timer_decorator
def extract_audio_from_video(video_fp):
    os.system(f"ffmpeg -y -i {video_fp} -loglevel error -vn ./tmp/src.wav")
    os.system(f"ffmpeg -y -i {video_fp} -loglevel error -an ./tmp/novoice_src.mp4")


def embed_audio_to_video(audio_fp, video_fp, tgt_fp):
    os.system(f"ffmpeg -y -i {video_fp} -i {audio_fp} -loglevel error {tgt_fp}")


def embed_subtitle_to_video(sub_fp, video_fp, tgt_fp):
    os.system(
        f"""ffmpeg -y -i {video_fp} -vf "subtitles={sub_fp}" -loglevel error {tgt_fp}"""
    )


@timer_decorator
def video_retalk():
    base_dir = os.getcwd()

    video_fp = os.path.join(base_dir, "./tmp/novoice_src.mp4")
    audio_fp = os.path.join(base_dir, "./tmp/tgt.wav")
    output_fp = os.path.join(base_dir, "./tmp/tgt.mp4")
    command = f"python inference.py --face {video_fp} --audio {audio_fp} --outfile {output_fp}"

    os.chdir(os.path.join(base_dir, "video-retalking"))
    if os.path.exists("./temp"):
        shutil.rmtree("./temp")
    os.mkdir("./temp")
    os.mkdir("./temp/temp")
    os.mkdir("./temp/face")

    subprocess.run(command)

    os.chdir(base_dir)


@timer_decorator
def video_to_video_translation(video_fp, video_retalking=True):
    print("extract audio from video...")
    if not os.path.exists("./tmp"):
        os.mkdir("./tmp")
    else:
        shutil.rmtree("./tmp")
        os.mkdir("./tmp")

    extract_audio_from_video(video_fp)

    print("speech to speech translation...")
    audio_fp = "./tmp/src.wav"
    sub_fp = "./tmp/sub.srt"
    s2st.speech_to_speech_translation(audio_fp, sub_fp, adjust_audio_speed=True)

    if video_retalking:
        print("video retalking...")
        video_retalk()

    print("embed audio to video...")
    audio_fp = "./tmp/tgt.wav"
    if video_retalking:
        video_fp = "./tmp/tgt_enhanced.mp4"
    else:
        video_fp = "./tmp/novoice_src.mp4"
    tgt_fp = "./tmp/tgt_retalk.mp4"
    embed_audio_to_video(audio_fp, video_fp, tgt_fp)

    print("embed subtitle to video...")
    sub_fp = "./tmp/sub.srt"
    video_fp = "./tmp/tgt_retalk.mp4"
    tgt_fp = "output.mp4"
    embed_subtitle_to_video(sub_fp, video_fp, tgt_fp)

    print("finished!")
    # shutil.rmtree("./tmp")
    return tgt_fp


def v2vt_app():
    demo = gr.Blocks()
    with demo:
        gr.Markdown(
            """
            <div style="text-align:center;">
                <span style="font-size:3em; font-weight:bold;">带有口型同步的视频翻译</span>
            </div>
            """
        )
        gr.Markdown(
            """
            <div style="text-align:center;">
                <span style="font-size:1em; font-weight:bold;">
                    <a href="https://space.bilibili.com/694977673" target="_blank">
                        开发者：二分之一的子木
                    </a>
                </span>
            </div>
            """
        )
        with gr.Row():
            input_video = gr.Video(label="输入视频")
            output_video = gr.Video(label="输出视频")
        submit = gr.Button(value="开始转换")
        submit.click(
            fn=video_to_video_translation,
            inputs=[input_video],
            outputs=[output_video],
        )

    demo.launch()


if __name__ == "__main__":
    v2vt_app()
