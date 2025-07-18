import os
import cv2
import numpy as np
import paho.mqtt.client as mqtt
import subprocess
import time

# Read environment variables
MQTT_BROKER = os.environ['MQTT_BROKER']
MQTT_PORT = int(os.environ.get('MQTT_PORT', 1883))
MQTT_USERNAME = os.environ.get('MQTT_USERNAME')
MQTT_PASSWORD = os.environ.get('MQTT_PASSWORD')
MQTT_STREAM_MAP = os.environ['MQTT_STREAM_MAP']

# Parse mapping
topic_map = {}
for kv in MQTT_STREAM_MAP.split(','):
    try:
        topic, stream = kv.split(':')
        topic_map[topic.strip()] = stream.strip()
    except ValueError:
        raise RuntimeError(f"Invalid MQTT_STREAM_MAP mapping: '{kv}'")

FFMPEG_CMD_TEMPLATE = [
    "ffmpeg", "-re",
    "-f", "image2pipe",
    "-vcodec", "mjpeg",
    "-i", "-",
    "-vf", "fps=5",  # adjust as needed
    "-vcodec", "libx264",
    "-f", "rtsp",
    "-rtsp_transport", "tcp",
]

streams = {}

def on_connect(client, userdata, flags, rc):
    for topic in topic_map:
        client.subscribe(topic)

def on_message(client, userdata, msg):
    topic = msg.topic
    stream_name = topic_map.get(topic)
    if not stream_name:
        return  # ignore topics not in map
    stream_url = f"rtsp://localhost:8554/{stream_name}"

    if stream_name not in streams:
        ffmpeg_cmd = FFMPEG_CMD_TEMPLATE + [stream_url]
        print(f"Starting ffmpeg for topic {topic} -> {stream_url}")
        proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)
        streams[stream_name] = proc

    proc = streams[stream_name]
    img_array = np.frombuffer(msg.payload, np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    if img is not None:
        ret, jpeg = cv2.imencode('.jpg', img)
        if ret:
            try:
                proc.stdin.write(jpeg.tobytes())
            except Exception as e:
                print(f"Error writing frame for topic {topic}: {e}")

client = mqtt.Client()
if MQTT_USERNAME and MQTT_PASSWORD:
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    for proc in streams.values():
        proc.stdin.close()
        proc.wait()