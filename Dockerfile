FROM python:3.10-slim

RUN apt-get update && apt-get install -y ffmpeg wget && \
    rm -rf /var/lib/apt/lists/*

# Download and install rtsp-simple-server
RUN wget https://github.com/aler9/rtsp-simple-server/releases/download/v0.22.0/rtsp-simple-server_v0.22.0_linux_amd64.tar.gz && \
    tar -zxvf rtsp-simple-server_v0.22.0_linux_amd64.tar.gz && \
    mv rtsp-simple-server/rtsp-simple-server /usr/local/bin/ && \
    rm -rf rtsp-simple-server*

WORKDIR /app

COPY mqtt_to_rtsp.py .

RUN pip install --no-cache-dir paho-mqtt numpy opencv-python-headless

CMD ["sh", "-c", "rtsp-simple-server & python3 mqtt_to_rtsp.py"]