import gzip
import sys

import requests
import base64

with open("example.png", "rb") as f:
    data = f.read()
    data = gzip.compress(data)
    data_bs64 = base64.b64encode(data).decode('utf-8')

data = {
    "data_bs64": data_bs64,
    "suffix": "png",
    "kind": 2,
}

try:
    response = requests.post("http://127.0.0.1:13000/infer", json=data)
    # response = requests.post("http://127.0.0.1:8200/ai/nsfw/check", json=data)
    print(response.json())
    print("成功")
    sys.exit(0)
except Exception as e:
    print("失败")
    print(str(e))
    sys.exit(1)
