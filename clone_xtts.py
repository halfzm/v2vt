import os
import re
import uuid
import time
import subprocess

import langid
import torch
import torchaudio
import gradio as gr
from TTS.tts.models.xtts import Xtts
from TTS.tts.configs.xtts_config import XttsConfig

from utils import timer_decorator

class XTTSClone:
    def __init__(self):
        print('loading xtts model...')
        model_name = "tts_models/multilingual/multi-dataset/xtts_v2"
        model_path = os.path.join(
            'tts_models', model_name.replace("/", "--")
        )

        config = XttsConfig()
        config.load_json(os.path.join(model_path, "config.json"))

        self.model = Xtts.init_from_config(config)
        self.model.load_checkpoint(
            config,
            checkpoint_dir=model_path,
            checkpoint_path=os.path.join(model_path, "model.pth"),
            vocab_path=os.path.join(model_path, "vocab.json"),
            eval=True,
            use_deepspeed=False,
            # use_deepspeed=True,
        )
        self.model.cuda()

        self.supported_languages = config.languages

    @timer_decorator
    def clone_voice(
        self,
        prompt,
        tgt_audio_fp,
        out_audio_fp='./tmp/tgt.wav',
        voice_cleanup=False,
        speed=1.0,
    ):

        language_predicted = langid.classify(prompt)[
            0
        ].strip()  # strip need as there is space at end!
        
        # tts expects chinese as zh-cn
        if language_predicted == "zh":
            # we use zh-cn
            language_predicted = "zh-cn"

        # 模型不支持语言
        if language_predicted not in self.supported_languages:
            print(f"Language you put {language_predicted} in is not in is not in our Supported Languages, please choose from dropdown")

            return

        speaker_wav = tgt_audio_fp

        # Filtering for microphone input, as it has BG noise, maybe silence in beginning and end
        # This is fast filtering not perfect

        # Apply all on demand
        lowpassfilter = trim = True

        if lowpassfilter:
            lowpass_highpass = "lowpass=8000,highpass=75,"
        else:
            lowpass_highpass = ""

        if trim:
            # better to remove silence in beginning and end for microphone
            trim_silence = "areverse,silenceremove=start_periods=1:start_silence=0:start_threshold=0.02,areverse,silenceremove=start_periods=1:start_silence=0:start_threshold=0.02,"
        else:
            trim_silence = ""

        if voice_cleanup:
            try:
                out_filename = (
                    speaker_wav + str(uuid.uuid4()) + ".wav"
                )  # ffmpeg to know output format

                # we will use newer ffmpeg as that has afftn denoise filter
                shell_command = f"ffmpeg -y -i {speaker_wav} -af {lowpass_highpass}{trim_silence} {out_filename}".split(
                    " "
                )

                command_result = subprocess.run(
                    [item for item in shell_command],
                    capture_output=False,
                    text=True,
                    check=True,
                )
                speaker_wav = out_filename
                print("Filtered microphone input")
            except subprocess.CalledProcessError:
                # There was an error - command exited with non-zero code
                print("Error: failed filtering, use original microphone input")
        else:
            speaker_wav = speaker_wav

        if len(prompt) < 2:
            gr.Warning("Please give a longer prompt text")
            return (
                None,
                None,
                None,
                None,
            )

        metrics_text = ""
        # note diffusion_conditioning not used on hifigan (default mode), it will be empty but need to pass it to model.inference
        try:
            (
                gpt_cond_latent,
                speaker_embedding,
            ) = self.model.get_conditioning_latents(
                audio_path=speaker_wav,
                gpt_cond_len=30,
                gpt_cond_chunk_len=4,
                max_ref_length=60,
            )
        except Exception as e:
            print("Speaker encoding error", str(e))
            gr.Warning(
                "It appears something wrong with reference, did you unmute your microphone?"
            )
            return (
                None,
                None,
                None,
            )
        # temporary comma fix
        prompt = re.sub("([^\x00-\x7F]|\w)(\.|\。|\?)", r"\1 \2\2", prompt)

        print("I: Generating new audio...")
        t0 = time.time()
        out = self.model.inference(
            prompt,
            language_predicted,
            gpt_cond_latent,
            speaker_embedding,
            repetition_penalty=5.0,
            temperature=0.75,
            speed=speed,
        )
        inference_time = time.time() - t0
        print(f"I: Time to generate audio: {round(inference_time*1000)} milliseconds")
        metrics_text += (
            f"Time to generate audio: {round(inference_time*1000)} milliseconds\n"
        )
        real_time_factor = (time.time() - t0) / out["wav"].shape[-1] * 24000
        print(f"Real-time factor (RTF): {real_time_factor}")
        metrics_text += f"Real-time factor (RTF): {real_time_factor:.2f}\n"

        torchaudio.save(out_audio_fp, torch.tensor(out["wav"]).unsqueeze(0), 24000)


if __name__ == "__main__":
    cloner = XTTSClone()
    prompt = "大家好，今天的演讲主题是关于某一个人"
    tgt_audio_fp = './tmp/src.wav'
    cloner.clone_voice(prompt, tgt_audio_fp)
