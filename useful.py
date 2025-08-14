from openai import OpenAI
from pypinyin import lazy_pinyin
import os
import json
from urllib.request import urlopen, Request
from urllib.error import URLError
from urllib.parse import urlencode, quote_plus
import pyaudio
import wave
import io
import time
import cv2 as cv
from ultralytics import YOLO

class Robot:
    def __init__(self, XGO_edu, g_car):
        self.api_key = "sk-DxDhm5lxIKgCduiRdhHYtGZl6oSuatTRQSMjv1dYGCYdIeB0"
        self.base_url = "https://api.chatanywhere.tech"
        self.history = []
        self.XGO_EDU = XGO_edu
        self.G_CAR = g_car
        self.synthesis = SpeechSynthesis()
        self.vision_model = YOLO("yolo11s.pt")
        print("Init Done.")

    # 动态显示表情
    def run_show_image(self):
        os.system('python show_img.py')

    # 动态显示灯光
    def run_led(self):
        os.system('python led_show.py')

    # GPT对话模型
    #TODO 待删
    def chat_with_gpt(self, text, prompt):
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": text},
        ]
        self.history.extend(messages)
        client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        response = client.chat.completions.create(model="gpt-3.5-turbo", messages=self.history)
        re = response.choices[0].message.content
        return re

    # 文字转语音
    def speaking(self, text):
        self.synthesis.speech_synthesis(text)
        print(text)

    # 目标识别
    #TODO 待删
    def target_recognition(self):
        cap = cv.VideoCapture(0)

        _, image = cap.read()
        results = self.vision_model.predict(image)
        ret = ""
        for result in results:
            boxes = result.boxes.xyxy
            names = result.names
            clses = result.boxes.cls
            ret_list = []
            for i in range(boxes.shape[0]):
                width = float(boxes[i][2].item() - boxes[i][0].item())
                height = float(boxes[i][3].item() - boxes[i][1].item())
                ret_list.append((height * width, names[clses[i].item()]))
            ret_list.sort()
            while ret_list[-1][1] == 'person':
                ret_list.pop(0)
            if len(ret_list) == 0:
                cap.release()
                return None
            ret += ret_list[-1][1]
        cap.release()
        return ret


    # 动作表演
    def action(self, parm, a_speed=0, a_time=0, b_speed=0, b_time=0, c_height=0, d_speed=0, d_time=0, e_speed=0,
               e_time=0):
        '''
        parm = 0 向前移动  a_time:时间 a_speed:速度
        parm = 1 转圈      b_time:时间 b_speed:角速度
        parm = 2 高度变化   c_height:高度
        parm = 3 上下移动   d_speed:速度  d_time:持续时间
        parm = 4 左右摆动   e_speed:速度  e_time:持续时间
        '''
        if parm == 0:
            self.G_CAR.rider_move_x(a_speed, a_time)
        elif parm == 1:
            self.G_CAR.rider_turn(b_speed, b_time)
        elif parm == 2:
            self.G_CAR.rider_height(c_height)
        elif parm == 3:
            self.G_CAR.rider_periodic_z(d_speed)
            time.sleep(d_time)
            self.G_CAR.rider_periodic_z(0)
        elif parm == 4:
            self.G_CAR.rider_periodic_roll(e_speed)
            time.sleep(e_time)
            self.G_CAR.rider_periodic_roll(0)
        else:
            print('''
        parm = 0 向前移动  a_time:时间 a_speed:速度
        parm = 1 转圈      b_time:时间 b_speed:角速度
        parm = 2 高度变化   c_height:高度
        parm = 3 上下移动   d_speed:速度  d_time:持续时间
        parm = 4 左右摆动   e_speed:速度  e_time:持续时间
        ''')


class SpeechSynthesis:
    def __init__(self):
        # 百度语音合成API相关参数
        self.TTS_URL = 'http://tsn.baidu.com/text2audio'
        self.SCOPE = 'audio_tts_post'
        self.PER = 4144  # 发音人
        self.SPD = 5  # 语速，取值0-15，默认为5
        self.PIT = 5  # 语调，取值0-15，默认为5
        self.VOL = 90  # 音量，取值0-15，默认为5
        self.AUE = 6  # 音频格式，6为wav格式
        self.FORMATS = {3: "mp3", 4: "pcm", 5: "pcm", 6: "wav"}
        self.FORMAT = self.FORMATS[self.AUE]
        self.CUID = "123456PYTHON"  # 用户唯一标识

    def fetch_token(self):
        """获取百度语音合成API的token"""
        # 这里需要实现获取token的逻辑，根据百度API的文档进行
        # 示例：通过API请求获取token
        API_KEY = '9oghXkpEeYvRkm2Bi3pB0PMY'  # 替换为你的百度API Key
        SECRET_KEY = 'sjekOtzRMCGTjcaQevbN2cSznw5Hk3xS'  # 替换为你的百度Secret Key
        token_url = f"https://openapi.baidu.com/oauth/2.0/token?grant_type=client_credentials&client_id={API_KEY}&client_secret={SECRET_KEY}"
        try:
            response = urlopen(token_url)
            result = json.loads(response.read().decode('utf-8'))
            return result['access_token']
        except Exception as e:
            print(f"获取token失败: {e}")
            return None

    def play_audio_stream(self, audio_data):
        """播放音频流"""
        try:
            # 将字节数据转换为文件对象
            audio_file = io.BytesIO(audio_data)

            # 配置音频播放参数
            CHUNK = 1024
            wf = wave.open(audio_file, 'rb')
            p = pyaudio.PyAudio()
            stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                            channels=wf.getnchannels(),
                            rate=wf.getframerate(),
                            output=True)

            # 播放音频
            data = wf.readframes(CHUNK)
            while data:
                stream.write(data)
                data = wf.readframes(CHUNK)

            # 清理资源
            stream.stop_stream()
            stream.close()
            p.terminate()
            print("音频播放完成")
            return True
        except Exception as e:
            print(f"播放音频流失败: {e}")
            return False

    def speech_synthesis(self, text):
        """文字转语音主函数"""
        if not text:
            print("输入文本为空")
            return False

        # 获取token
        token = self.fetch_token()
        if not token:
            print("获取token失败，无法进行语音合成")
            return False

        # 构造请求参数
        tex = quote_plus(text)  # 对文本进行编码
        params = {
            'tok': token,
            'tex': tex,
            'per': self.PER,
            'spd': self.SPD,
            'pit': self.PIT,
            'vol': self.VOL,
            'aue': self.AUE,
            'cuid': self.CUID,
            'lan': 'zh',
            'ctp': 1
        }

        # 构造请求URL
        url = f"{self.TTS_URL}?{urlencode(params)}"

        try:
            # 发送请求
            response = urlopen(url)
            audio_data = response.read()

            # 检查返回内容是否为音频数据
            content_type = response.headers.get('Content-Type', '')
            if 'audio/' not in content_type:
                print("返回内容不是音频数据")
                return False

            # 直接播放音频流
            self.play_audio_stream(audio_data)
            return True
        except URLError as e:
            print(f"请求语音合成API失败: {e}")
            return False
        except Exception as e:
            print(f"语音合成过程中发生错误: {e}")
            return False


# 语言匹配函数：word1:目标文本；word2:目标词
def are_pronunciations_equal(word1, word2):
    pinyin1 = lazy_pinyin(word1)
    pinyin2 = lazy_pinyin(word2)
    for i in pinyin2:
        if i in pinyin1:
            pass
        else:
            return False
        if i == pinyin2[-1]:
            return True
    return False