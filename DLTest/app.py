import threading
import time
import requests
from flask import Flask
import os

app = Flask(__name__)

NACOS_IP = '192.168.10.1'
NACOS_PORT = '8848'
SERVICE_IP = '192.168.10.100'
SERVICE_PORT = '5000'
SERVICE_NAME = 'algorithm-service'


@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'


@app.route('/deepxplore')
def deepxplore():
    # exec script run deepxplore
    os.system('./doit')
    return 'demo'


def service_register():
    url = "http://" + NACOS_IP + ":" + NACOS_PORT + "/nacos/v1/ns/instance?serviceName=" \
          + SERVICE_NAME + "&ip=" + SERVICE_IP + "&port=" + SERVICE_PORT + "&ephemeral=false"
    res = requests.post(url)


def service_beat():
    while True:
        url = "http://" + NACOS_IP + ":" + NACOS_PORT + "/nacos/v1/ns/instance/beat?serviceName=" \
              + SERVICE_NAME + "&ip=" + SERVICE_IP + "&port=" + SERVICE_PORT + "&ephemeral=false"
        res = requests.put(url)
        time.sleep(5)


if __name__ == '__main__':
    service_register()
    threading.Timer(5, service_beat).start()
    app.run(host='0.0.0.0', port=5000, debug=True)
