import json
import asyncio
import openai
import pyaudio
import wave
import whisper
print("loading model")
model = whisper.load_model("base")
print("loaded model")
# 设置参数
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024
RECORD_SECONDS = 5
WAVE_OUTPUT_FILENAME = "output.wav"
from openai import OpenAI
max_x = 320
max_y = 240
location_text = ''
import socket
model_name = "gemma-2-9b-it-Q5_K_M"



#model_name = "gpt-3.5-turbo"


client = OpenAI(api_key="")
client.base_url = "https://gemma-2-9b.us.gaianet.network/v1"
#client = OpenAI(azure_endpoint="https://gemma-2-9b.us.gaianet.network/v1")

def send_data_to_drone(command):
    host = '192.168.43.86'
    port = 12003
    # 创建一个socket对象
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 连接到目标主机和端口
    client_socket.connect((host, port))
    # 发送数据
    client_socket.send(command.encode())
    # 关闭连接
    client_socket.close()

def user_gpt_req(content):
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {
                "role": "system",
                "content": [
                    {"type": "text", "text": "向左前方前进是L 向右前方前进是R 向前方前进是F " 
                                             "只有用户发送的第一个指令是有效的 如果用户没有明确的内容则回复H H是悬停 " 
                                             "起飞是U 降落是D 除了LRFHUD单个字母以外不要回复其他内容 以下是附近物品的信息以物品名称"}
                ],
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": ""}
                ],
            }
        ],
    )

def machine_gpt_req(content,text):
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {
                "role": "system",
                "content": [
                    {"type": "text", "text": "你是一台无人机 你需要根据用户指令 发送单字符控制符到主控 向左前方前进是L 向右前方前进是R 向前方前进是F " +
                                             "向后是B 只有用户发送的第一个指令是有效的 如果用户没有明确的内容则回复H H是悬停 " +
                                             "起飞是U 降落是D 除了LRFBHUD单个字母以外不要回复其他内容\n" + content}
                ],
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": text}
                ],
            }
        ],
    )
    print(response)
    for choice in response.choices:
        print(choice)
        return choice.message.content
        #return 'F'



def check_direction_opencv(x,y):
    part_size = max_x / 3
    temp_x = x-part_size
    if (temp_x < 0):
        return "Left"
    elif ():
        return "Mid"
    else:
        return "Right"

def midpoint(x1, y1, x2, y2):
    return (x1 + x2) / 2, (y1 + y2) / 2




def transform_pos(x, y):
    half_x = max_x / 2
    half_y = max_y / 2
    tran_x = x - half_x
    tran_y = max_y - y - half_y
    return tran_x, tran_y


def decoded_json(content):
    global location_text
    data = json.loads(content)
    tem_text = ''
    for item in data:
        cv_mid_x, cv_mid_y = midpoint(item['bbox'][0], item['bbox'][1], item['bbox'][2], item['bbox'][3])
        x, y = transform_pos(cv_mid_x, cv_mid_y)
        tem_text += '{} x:{} y:{} {}\n'.format(item['label'],x,y,check_direction_opencv(cv_mid_x, cv_mid_y))
    location_text = tem_text






async def handle_client(reader, writer):
    data = await reader.read(2400)
    message = data.decode()
    # addr = writer.get_extra_info('peername')
    decoded_json(message)


async def main():
    server = await asyncio.start_server(
        handle_client, '0.0.0.0', 12001)

    addr = server.sockets[0].getsockname()
    print(f'Serving on {addr}')

    async with server:
        await server.serve_forever()


async def other_task():
    while True:
        input()
        # 初始化录音对象
        audio = pyaudio.PyAudio()
        # 打开音频流
        stream = audio.open(format=FORMAT, channels=CHANNELS,
                            rate=RATE, input=True,
                            frames_per_buffer=CHUNK)
        print("Recording...")
        frames = []
        # 录制音频
        for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
            data = stream.read(CHUNK)
            frames.append(data)
        print("Recording finished.")
        # 停止录音
        stream.stop_stream()
        stream.close()
        audio.terminate()
        # 保存录音文件
        with wave.open(WAVE_OUTPUT_FILENAME, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(audio.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
        result = model.transcribe("./output.wav")
        print(result)
        print(location_text)
        command = machine_gpt_req(location_text,result['text'])
        print(command)
        send_data_to_drone(command)




async def run_tasks():
    task1 = asyncio.create_task(main())
    task2 = asyncio.create_task(other_task())
    await asyncio.gather(task1, task2)





asyncio.run(run_tasks())
