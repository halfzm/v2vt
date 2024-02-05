import os
import torch
import argparse
import gradio as gr
import langid
import se_extractor
from api import BaseSpeakerTTS, ToneColorConverter


base_dir = os.getcwd()
os.environ["PATH"] = base_dir + ";" + os.environ["PATH"]


parser = argparse.ArgumentParser()
parser.add_argument(
    "--share", action="store_true", default=False, help="make link public"
)
args = parser.parse_args()

en_ckpt_base = "checkpoints/base_speakers/EN"
zh_ckpt_base = "checkpoints/base_speakers/ZH"
ckpt_converter = "checkpoints/converter"
device = "cuda" if torch.cuda.is_available() else "cpu"
output_dir = "outputs"
os.makedirs(output_dir, exist_ok=True)

# load models
en_base_speaker_tts = BaseSpeakerTTS(f"{en_ckpt_base}/config.json", device=device)
en_base_speaker_tts.load_ckpt(f"{en_ckpt_base}/checkpoint.pth")
zh_base_speaker_tts = BaseSpeakerTTS(f"{zh_ckpt_base}/config.json", device=device)
zh_base_speaker_tts.load_ckpt(f"{zh_ckpt_base}/checkpoint.pth")
tone_color_converter = ToneColorConverter(
    f"{ckpt_converter}/config.json", device=device
)
tone_color_converter.load_ckpt(f"{ckpt_converter}/checkpoint.pth")

# load speaker embeddings
en_source_default_se = torch.load(f"{en_ckpt_base}/en_default_se.pth").to(device)
en_source_style_se = torch.load(f"{en_ckpt_base}/en_style_se.pth").to(device)
zh_source_se = torch.load(f"{zh_ckpt_base}/zh_default_se.pth").to(device)

# This online demo mainly supports English and Chinese
supported_languages = ["zh", "en"]


def predict(prompt, style, audio_file_pth, agree):
    # initialize a empty info
    text_hint = ""

    # first detect the input language
    language_predicted = langid.classify(prompt)[0].strip()
    print(f"检测到的语种为:{language_predicted}")

    if language_predicted not in supported_languages:
        text_hint += f"[ERROR] The detected language {language_predicted} for your input text is not in our Supported Languages: {supported_languages}\n"
        gr.Warning(
            f"The detected language {language_predicted} for your input text is not in our Supported Languages: {supported_languages}"
        )

        return (
            text_hint,
            None,
            None,
        )

    if language_predicted == "zh":
        tts_model = zh_base_speaker_tts
        source_se = zh_source_se
        language = "Chinese"
        if style not in ["default"]:
            text_hint += f"[ERROR] The style {style} is not supported for Chinese, which should be in ['default']\n"
            gr.Warning(
                f"The style {style} is not supported for Chinese, which should be in ['default']"
            )
            return (
                text_hint,
                None,
                None,
            )

    else:
        tts_model = en_base_speaker_tts
        if style == "default":
            source_se = en_source_default_se
        else:
            source_se = en_source_style_se
        language = "English"
        if style not in [
            "default",
            "whispering",
            "shouting",
            "excited",
            "cheerful",
            "terrified",
            "angry",
            "sad",
            "friendly",
        ]:
            text_hint += f"[ERROR] The style {style} is not supported for English, which should be in ['default', 'whispering', 'shouting', 'excited', 'cheerful', 'terrified', 'angry', 'sad', 'friendly']\n"
            gr.Warning(
                f"The style {style} is not supported for English, which should be in ['default', 'whispering', 'shouting', 'excited', 'cheerful', 'terrified', 'angry', 'sad', 'friendly']"
            )
            return (
                text_hint,
                None,
                None,
            )

    speaker_wav = audio_file_pth

    if len(prompt) < 2:
        text_hint += "[ERROR] Please give a longer prompt text \n"
        gr.Warning("Please give a longer prompt text")
        return (
            text_hint,
            None,
            None,
        )
    if len(prompt) > 200:
        text_hint += "[ERROR] Text length limited to 200 characters for this demo, please try shorter text. You can clone our open-source repo and try for your usage \n"
        gr.Warning(
            "Text length limited to 200 characters for this demo, please try shorter text. You can clone our open-source repo for your usage"
        )
        return (
            text_hint,
            None,
            None,
        )

    # note diffusion_conditioning not used on hifigan (default mode), it will be empty but need to pass it to model.inference
    try:
        # 修改了源代码，增加了model_path参数
        target_se, audio_name = se_extractor.get_se(
            speaker_wav,
            tone_color_converter,
            target_dir="processed",
            vad=True,
            model_path=os.path.join(os.getcwd(), "snakers4/"),
        )
    except Exception as e:
        text_hint += f"[ERROR] Get target tone color error {str(e)} \n"
        gr.Warning("[ERROR] Get target tone color error {str(e)} \n")
        return (
            text_hint,
            None,
            None,
        )

    src_path = f"{output_dir}/tmp.wav"
    tts_model.tts(prompt, src_path, speaker=style, language=language)

    save_path = f"{output_dir}/output.wav"
    # Run the tone color converter
    encode_message = "@MyShell"
    tone_color_converter.convert(
        audio_src_path=src_path,
        src_se=source_se,
        tgt_se=target_se,
        output_path=save_path,
        message=encode_message,
    )

    text_hint += """Get response successfully \n"""

    return (
        text_hint,
        save_path,
        speaker_wav,
    )


examples = [
    [
        "今天天气真好，我们一起出去吃饭吧。",
        "default",
        "resources/demo_speaker1.mp3",
        True,
    ],
    [
        "This audio is generated by open voice with a half-performance model.",
        "whispering",
        "resources/demo_speaker2.mp3",
        True,
    ],
    [
        "He hoped there would be stew for dinner, turnips and carrots and bruised potatoes and fat mutton pieces to be ladled out in thick, peppered, flour-fattened sauce.",
        "sad",
        "resources/demo_speaker0.mp3",
        True,
    ],
]

with gr.Blocks(analytics_enabled=False) as demo:
    gr.Markdown(
        """
        <div style="text-align:center;">
            <span style="font-size:3em; font-weight:bold;">OpenVoice-语音克隆</span>
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
        with gr.Column():
            input_text_gr = gr.Textbox(
                label="文本提示词",
                info="每次输入最好一到两个句子，最多不要超过200个字符.",
                value="He hoped there would be stew for dinner, turnips and carrots and bruised potatoes and fat mutton pieces to be ladled out in thick, peppered, flour-fattened sauce.",
            )
            style_gr = gr.Dropdown(
                label="风格",
                info="请为合成的输出音频选择一种风格 (中文目前仅支持“default”)",
                choices=[
                    "default",
                    "whispering",
                    "shouting",
                    "excited",
                    "cheerful",
                    "terrified",
                    "angry",
                    "sad",
                    "friendly",
                ],
                max_choices=1,
                value="default",
            )
            ref_gr = gr.Audio(
                label="参考音频",
                info="点击 ✎ 按钮上传自定义的音频",
                type="filepath",
                value="resources/demo_speaker2.mp3",
            )

        with gr.Column():
            out_text_gr = gr.Text(label="提示信息")
            audio_gr = gr.Audio(label="合成的语音", autoplay=True)
            ref_audio_gr = gr.Audio(label="使用了的参考音频")

    tts_button = gr.Button("生成", elem_id="send-btn", visible=True)
    tts_button.click(
        predict,
        [input_text_gr, style_gr, ref_gr],
        outputs=[out_text_gr, audio_gr, ref_audio_gr],
    )

    gr.Examples(
        examples,
        label="参考样例",
        inputs=[input_text_gr, style_gr, ref_gr],
        outputs=[out_text_gr, audio_gr, ref_audio_gr],
        fn=predict,
        cache_examples=False,
    )

demo.queue()
demo.launch(debug=True, show_api=True, share=args.share)
