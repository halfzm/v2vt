import torch
import langid

import OpenVoice.se_extractor as se_extractor
from OpenVoice.api import BaseSpeakerTTS, ToneColorConverter
from microsoft_tts import MSTTS

device = "cuda" if torch.cuda.is_available() else "cpu"

class VoiceClone():
    def __init__(self):
        self.en_ckpt_base = "openvoice_checkpoints/base_speakers/EN"
        self.zh_ckpt_base = "openvoice_checkpoints/base_speakers/ZH"
        self.ckpt_converter = "openvoice_checkpoints/converter"

        # load models
        self.en_base_speaker_tts = BaseSpeakerTTS(f"{self.en_ckpt_base}/config.json", device=device)
        self.en_base_speaker_tts.load_ckpt(f"{self.en_ckpt_base}/checkpoint.pth")
        # self.zh_base_speaker_tts = BaseSpeakerTTS(
        #     f"{self.zh_ckpt_base}/config.json", device=device
        # )
        # self.zh_base_speaker_tts.load_ckpt(f"{self.zh_ckpt_base}/checkpoint.pth")
        self.tone_color_converter = ToneColorConverter(
            f"{self.ckpt_converter}/config.json", device=device
        )
        self.tone_color_converter.load_ckpt(f"{self.ckpt_converter}/checkpoint.pth")

        # load speaker embeddings
        self.en_source_default_se = torch.load(
            f"{self.en_ckpt_base}/en_default_se.pth"
        ).to(device)
        self.en_source_style_se = torch.load(f"{self.en_ckpt_base}/en_style_se.pth").to(
            device
        )
        self.zh_source_se = torch.load(f"{self.zh_ckpt_base}/zh_default_se.pth").to(
            device
        )

    def clone_voice(
        self,
        prompt,
        tgt_audio_fp,
        style='default',
        src_audio_fp= "./tmp/tts.wav",
        out_audio_fp="./tmp/output.wav",
    ):
        # first detect the input language
        language_predicted = langid.classify(prompt)[0].strip()
        # print(f"检测到的语种为:{language_predicted}")
        if language_predicted == "zh":
            tts_model = MSTTS()
            source_se = self.zh_source_se
            language = "Chinese"
        else:
            tts_model = self.en_base_speaker_tts
            if style == "default":
                source_se = self.en_source_default_se
            else:
                source_se = self.en_source_style_se
            language = "English"

        target_se, audio_name = se_extractor.get_se(
            tgt_audio_fp,
            self.tone_color_converter,
            target_dir="processed",
            vad=True,
        )

        # generate source speak voice
        # tts_model.tts(prompt, src_audio_fp, speaker=style, language=language)

        # 中文语音的话则调用微软的TTS
        if language_predicted == 'zh':
            tts_model.text_to_speech(prompt, src_audio_fp)
        else:
            tts_model.tts(prompt, src_audio_fp, speaker=style, language=language)

        # Run the tone color converter
        encode_message = "@二分之一的子木"
        self.tone_color_converter.convert(
            audio_src_path=src_audio_fp,
            src_se=source_se,
            tgt_se=target_se,
            output_path=out_audio_fp,
            message=encode_message,
        )


if __name__ == '__main__':
    cloner = VoiceClone()
    # prompt = "He hoped there would be stew for dinner, turnips and carrots and bruised potatoes and fat mutton pieces to be ladled out in thick, peppered, flour-fattened sauce."
    prompt = "今天的天气很冷，注意保暖！"
    tgt_audio_fp = "./OpenVoice/resources/demo_speaker2.mp3"
    style = "default"
    cloner.clone_voice(prompt=prompt, tgt_audio_fp=tgt_audio_fp, style=style)
