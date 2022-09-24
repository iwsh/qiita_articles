<!-- tag: React.js,fastAPI -->
<!-- private: False -->

# 概要

勉強のためにリアルタイムで更新が行われる簡単なチャットアプリを実装してみました。

ソースコードはこちらです
https://github.com/iwsh/http-chat/tree/v1.0

# 構成

- バックエンド(api): Python (FastAPI + sqlite)
- フロントエンド(ui): React.js

の 2 つの AP が HTTP 通信のシンプルな Web API で連携する構成となっています。

```
.
├── README.md
├── docker-compose.yml
├── init.sh					Init containers (api, ui)
├── api/					Backend (FastAPI + SQLite)
│   ├── modules/
│   ├── main.py
│   ├── init.sh
│   └── requirements.txt
└── ui/						Frontend (React.js)
    ├── package-lock.json
    ├── package.json
    ├── public/
    └── src/
```

## フロントエンド

![frontend screen](https://raw.githubusercontent.com/iwsh/assets/main/assets/qiita/article_4/frontend_v1.0.png)

Create React App で作成したひな形をもとに実装しています

メッセージをリアルタイムに更新するため、1 秒ごとに Web API にアクセスしてメッセージ一覧を取得して`msgs`に set しています

一般的にリアルタイムのデータ更新を行う際にはポーリングや websocket などの双方向通信が使われますが、まずは簡易な実装を試したかったため単純な GET リクエストで実装しました。

ui/src/App.js

```javascript
useEffect(() => {
  const interval = setInterval(() => {
    axios.get("http://127.0.0.1:8000/messages/").then((res) => {
      console.log(res);
      setMsgs(res.data);
    });
  }, 1000);
  return () => clearInterval(interval);
}, []);
```

## バックエンド

FastAPI で`/messages/`の URL に対する GET, POST を受け付け、SQLite で`api/main.db`にデータ格納・取得しています

躓いたポイントとして、CORS ポリシーというものに引っ掛かりフロントエンドと通信ができなくなっていました。
十分には理解できていないですが、どうやらセキュリティのために通信を許可するフロントエンドを FastAPI のパラメータとして登録する必要があるようです。
（参考: https://qiita.com/att55/items/2154a8aad8bf1409db2b）

api/main.py

```python
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

```python
@app.get("/messages/")
def read_item():
    df_msg = message_manager.get_messages()
    return df_msg.to_dict("records")


@app.post("/messages/")
def post_item(msg: Msg):
    df_msg = message_manager.post_messages(msg)
    return df_msg.to_dict("records")
```

# 起動

`init.sh` を実行することで起動します

- docker を使用するので必要に応じて sudo 権限で実行してください
- docker compose v2 が必要です。
  docker compose v1 で実行する場合は`init.sh`を以下のように編集してください

  ```bash
  docker-compose run ui npm install
  docker-compose up
  ```

- フロントエンド・バックエンドについて、それぞれパッケージをインストールしてサーバを起動しています

# おわりに

初めてリアルタイムに更新される画面アプリを作成したので、複数画面でメッセージのやりとりができているのを確認できたときの感動は大きかったです。

ひとまず性能などは無視して毎秒リクエストを飛ばしてメッセージ全量をもってくるという力技を実装しましたが、
今後より妥当な手段となりそうな websocket を使用しての実装も試してみたいと思います。
