import os
import json
from datetime import timedelta

import srt
from pydub import AudioSegment
from pydub.silence import detect_silence
from faster_whisper import WhisperModel
from transformers import M2M100ForConditionalGeneration, M2M100Tokenizer

from clone_voice import VoiceClone

class Speech2SpeechTranslation:
    def __init__(self):
        # load from local
        # self.translate_model = M2M100ForConditionalGeneration.from_pretrained(
        #     "m2m100_1.2B"
        # )
        # self.translate_tokenizer = M2M100Tokenizer.from_pretrained("m2m100_1.2B")
        # self.transcribe_model = WhisperModel(
        #     "fast-whisper", device="cuda", compute_type="float16"
        # )

        # load from url
        self.translate_model = M2M100ForConditionalGeneration.from_pretrained(
            "facebook/m2m100_1.2B"
        )
        self.translate_tokenizer = M2M100Tokenizer.from_pretrained(
            "facebook/m2m100_1.2B"
        )
        self.transcribe_model = WhisperModel(
            "large-v3", device="cuda", compute_type="float16"
        )
        self.voice_clone = VoiceClone()

    def transcribe(self, audio_fp):
        res = []
        segments, info = self.transcribe_model.transcribe(audio_fp, beam_size=5)
        print(f"检测到{info.language}的概率为{info.language_probability}")
        # for segment in segments:
        #     res.append(segment)
        for segment in segments:
            res.append(segment.text)
        res = "".join(res)
        return res, info.language

    def translate(self, txt, src_lang="en", tgt_lang="zh"):
        self.translate_tokenizer.src_lang = src_lang
        encoded_txt = self.translate_tokenizer(txt, return_tensors="pt")
        generated_tokens = self.translate_model.generate(
            **encoded_txt,
            forced_bos_token_id=self.translate_tokenizer.get_lang_id(tgt_lang),
        )
        return self.translate_tokenizer.batch_decode(
            generated_tokens, skip_special_tokens=True
        )[0]

    # 拼接配音片段 ,合并后的音频名字为  视频名字.wav 比如 1.mp4.wav
    def _merge_audio_segments(self, segments, start_times, total_duration, mp4name):
        # 创建一个空白的音频段作为初始片段
        merged_audio = AudioSegment.empty()
        # 检查是否需要在第一个片段之前添加静音
        if start_times[0] != 0:
            silence_duration = start_times[0]
            silence = AudioSegment.silent(duration=silence_duration)
            merged_audio += silence

        # 逐个连接音频片段
        for i in range(len(segments)):
            segment = segments[i]
            start_time = start_times[i]
            # 检查前一个片段的结束时间与当前片段的开始时间之间是否有间隔
            if i > 0:
                previous_end_time = start_times[i - 1] + len(segments[i - 1])
                silence_duration = start_time - previous_end_time
                # 可能存在字幕 语音对应问题
                if silence_duration > 0:
                    silence = AudioSegment.silent(duration=silence_duration)
                    merged_audio += silence
            # 连接当前片段
            merged_audio += segment
        # 检查总时长是否大于指定的时长，并丢弃多余的部分
        if len(merged_audio) > total_duration:
            merged_audio = merged_audio[:total_duration]
        merged_audio.export(f"./tmp/{mp4name}.wav", format="wav")
        return merged_audio

    # 修改速率
    def _speed_change(self, sound, speed=1.0):
        # Manually override the frame_rate. This tells the computer how many
        # samples to play per second
        sound_with_altered_frame_rate = sound._spawn(
            sound.raw_data, overrides={"frame_rate": int(sound.frame_rate * speed)}
        )
        # convert the sound with altered frame rate to a standard frame rate
        # so that regular playback programs will work right. They often only
        # know how to play audio at standard frame rate (like 44.1k)
        return sound_with_altered_frame_rate.set_frame_rate(sound.frame_rate)

    def _split_audio(self, audio_fp):
        normalized_sound = AudioSegment.from_wav(audio_fp)  # -20.0
        nonslient_file = "./tmp/detected_voice.json"

        if os.path.exists(nonslient_file):
            with open(nonslient_file, "r") as infile:
                nonsilent_data = json.load(infile)
        else:
            nonsilent_data = []
            audio_chunks = detect_silence(normalized_sound, min_silence_len=300)
            if len(audio_chunks) == 1 and (
                audio_chunks[0][1] - audio_chunks[0][0] > 60000
            ):
                # 一个，强制分割
                new_audio_chunks = []
                pos = 0
                while pos < audio_chunks[0][1]:
                    end = pos + 60000
                    end = audio_chunks[0][1] if end > audio_chunks[0][1] else end
                    new_audio_chunks.append([pos, end])
                    pos = end
                audio_chunks = new_audio_chunks

            for i, chunk in enumerate(audio_chunks):
                # print(chunk)
                start, end = chunk
                nonsilent_data.append([start, end, False])
            with open(nonslient_file, "w") as outfile:
                json.dump(nonsilent_data, outfile)
        return normalized_sound, nonsilent_data

    def speech_to_speech_translation(
        self,
        audio_fp,
        sub_fp,
    ):
        normalized_sound, nonsilent_data = self._split_audio(audio_fp)
        total_length = len(normalized_sound) / 1000

        subs = []
        segments = []
        start_times = []
        for i, duration in enumerate(nonsilent_data):
            start_time, end_time, buffered = duration
            start_times.append(start_time)
            chunk_filename = f"./tmp/c{i}_{start_time // 1000}_{end_time // 1000}.wav"
            add_vol = 0
            audio_chunk = normalized_sound[start_time:end_time] + add_vol
            audio_chunk.export(chunk_filename, format="wav")

            # recognize the chunk
            src_txt, language = self.transcribe(chunk_filename)
            if language == "zh":
                tgt_txt = self.translate(src_txt, src_lang="zh", tgt_lang="en")
            elif language == "en":
                tgt_txt = self.translate(src_txt, src_lang="en", tgt_lang="zh")

            # process the subtitle
            combo_txt = tgt_txt + "\n\n"
            if buffered:
                end_time -= 2000
            start = timedelta(milliseconds=start_time)
            end = timedelta(milliseconds=end_time)
            index = len(subs) + 1
            sub = srt.Subtitle(index=index, start=start, end=end, content=combo_txt)
            subs.append(sub)

            tmpname = f"./tmp/{start_time}-{index}.mp3"
            self.voice_clone.clone_voice(
                prompt=tgt_txt, tgt_audio_fp=audio_fp, out_audio_fp=tmpname
            )

            # adapt the voice speed
            try:
                audio_data = AudioSegment.from_file(tmpname, format="mp3")
                wavlen = end_time - start_time
                mp3len = len(audio_data)
                if mp3len - wavlen > 500:
                    # 最大加速2倍
                    speed = mp3len / wavlen
                    speed = 2 if speed > 2 else speed
                    audio_data = self._speed_change(audio_data, speed)
            except:
                audio_data = AudioSegment.silent(duration=end_time - start_time)
            segments.append(audio_data)
            os.unlink(tmpname)

        self._merge_audio_segments(segments, start_times, total_length * 1000, "tgt")

        final_srt = srt.compose(subs)
        with open(sub_fp, "w", encoding="utf-8") as f:
            f.write(final_srt)
