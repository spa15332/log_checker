# log_checker ver.1.1.1

## About
なんらかのログを見るための、ゆめかわツールです。
当ツールの使用にて生じた損害などに関しては一切の責任を負いかねます。
修正・改良の要望はのんびり対応します。
プルリク大歓迎。

## Requirements
### Dockerを使う場合
- Docker
    - Docker Compose
### 使わない場合
- Python
    - fastapi - Web framework
    - uvicorn - ASGI
    - jinja2 - テンプレートエンジン

## Run it
```console
$ docker-compose up
```

## Usage
1. logファイル配置
    - *.log を logs/ 配下に設置
    - (もしくは、main.pyの`LOGS_DIR`を好きなとこに変更)
2. ブラウザアクセス
    - 下記のURLにアクセスして、あとは流れでお願いします
    - http://127.0.0.1:8001/
3. 
    