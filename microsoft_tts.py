import re
import uuid
from datetime import datetime

import asyncio
import websockets

class MSTTS:
    def __init__(self):
        pass

    # Fix the time to match Americanisms
    def _hr_cr(self, hr):
        corrected = (hr - 1) % 24
        return str(corrected)


    # Add zeros in the right places i.e 22:1:5 -> 22:01:05
    def _fr(self, input_string):
        corr = ""
        i = 2 - len(input_string)
        while i > 0:
            corr += "0"
            i -= 1
        return corr + input_string


    # Generate X-Timestamp all correctly formatted
    def _getXTime(self):
        now = datetime.now()
        return (
            self._fr(str(now.year))
            + "-"
            + self._fr(str(now.month))
            + "-"
            + self._fr(str(now.day))
            + "T"
            + self._fr(self._hr_cr(int(now.hour)))
            + ":"
            + self._fr(str(now.minute))
            + ":"
            + self._fr(str(now.second))
            + "."
            + str(now.microsecond)[:3]
            + "Z"
        )


    # Async function for actually communicating with the websocket
    async def transferMsTTSData(self, text, outputPath, voice_name='zh-CN-XiaoxiaoNeural'):
        req_id = uuid.uuid4().hex.upper()
        # print(req_id)
        # TOKEN来源 https://github.com/rany2/edge-tts/blob/master/src/edge_tts/constants.py
        # 查看支持声音列表 https://speech.platform.bing.com/consumer/speech/synthesize/readaloud/voices/list?trustedclienttoken=6A5AA1D4EAFF4E9FB37E23D68491D6F4
        TRUSTED_CLIENT_TOKEN = "6A5AA1D4EAFF4E9FB37E23D68491D6F4"
        WSS_URL = (
            "wss://speech.platform.bing.com/consumer/speech/synthesize/"
            + "readaloud/edge/v1?TrustedClientToken="
            + TRUSTED_CLIENT_TOKEN
        )
        endpoint2 = f"{WSS_URL}&ConnectionId={req_id}"
        async with websockets.connect(
            endpoint2,
            extra_headers={
                "Pragma": "no-cache",
                "Cache-Control": "no-cache",
                "Origin": "chrome-extension://jdiccldimpdaibmpdkjnbmckianbfold",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "en-US,en;q=0.9",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                " (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36 Edg/91.0.864.41",
            },
        ) as websocket:
            message_1 = (
                f"X-Timestamp:{self._getXTime()}\r\n"
                "Content-Type:application/json; charset=utf-8\r\n"
                "Path:speech.config\r\n\r\n"
                '{"context":{"synthesis":{"audio":{"metadataoptions":{'
                '"sentenceBoundaryEnabled":false,"wordBoundaryEnabled":true},'
                '"outputFormat":"audio-24khz-48kbitrate-mono-mp3"'
                "}}}}\r\n"
            )
            await websocket.send(message_1)

            pitch = 0
            rate = 0
            ssml_text = f'<speak version="1.0" xml:lang="en-US" xmlns="http://www.w3.org/2001/10/synthesis" xmlns:emo="http://www.w3.org/2009/10/emotionml" xmlns:mstts="http://www.w3.org/2001/mstts"> <voice name="{voice_name}"> <prosody pitch="{pitch}%" rate="{rate}%">{text}</prosody> </voice> </speak>'

            message_2 = (
                f"X-RequestId:{req_id}\r\n"
                "Content-Type:application/ssml+xml\r\n"
                f"X-Timestamp:{self._getXTime()}Z\r\n"  # This is not a mistake, Microsoft Edge bug.
                "Path:ssml\r\n\r\n"
                f"{ssml_text}"
            )
            await websocket.send(message_2)

            # Checks for close connection message
            end_resp_pat = re.compile("Path:turn.end")
            audio_stream = b""
            while True:
                response = await websocket.recv()
                print("\rreceiving...", end="")
                # print(response)
                # Make sure the message isn't telling us to stop
                if re.search(end_resp_pat, str(response)) is None:
                    # Check if our response is text data or the audio bytes
                    if isinstance(response, bytes):
                        # Extract binary data
                        try:
                            needle = b"Path:audio\r\n"
                            start_ind = response.find(needle) + len(needle)
                            audio_stream += response[start_ind:]
                        except:
                            pass
                else:
                    break
            with open(f"{outputPath}", "wb") as audio_out:
                audio_out.write(audio_stream)


    async def mainSeq(self, SSML_text, outputPath, voice_name='zh-CN-XiaoxiaoNeural'):
        await self.transferMsTTSData(SSML_text, outputPath, voice_name=voice_name)


    def text_to_speech(self, text, tgt_fp, voice_name='zh-CN-XiaoxiaoNeural'):

        asyncio.run(self.mainSeq(text, tgt_fp, voice_name=voice_name))
        print("completed!")


if __name__ == '__main__':
    ttsmodel = MSTTS()
    text = '这是一个测试句子'
    tgt_fp = "./output.wav"
    ttsmodel.text_to_speech(text, tgt_fp)