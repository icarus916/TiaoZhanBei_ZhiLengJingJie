from useful import Robot,SpeechSynthesis
from XGO import XGOEDU
from xgolib import XGO
g_car = XGO("xgorider")   #实例化运动模型
XGO_edu = XGOEDU()
history = []  #对话历史
robot = Robot(XGO_edu,g_car)
Speech = SpeechSynthesis()
print(robot.chat_with_gpt("8+3等于几","你是一个回答小朋友生活上疑问的智能助手"))