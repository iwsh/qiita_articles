<!-- tag: OAuth,Github,React.js,fastAPI -->
<!-- private: True -->

# はじめに

[以前の記事](https://qiita.com/iwsh/items/2aa536e4984f4b78b6f4)で作成したチャット WEB アプリにログイン機能を作成したいと考えているのですが、パスワード認証だと面白みがないな...と思いソーシャルログインについて調べています。

勉強がてら Github のアカウントで簡単な OAuth を行うアプリケーションを作成したので、チュートリアルとして残しておきます。

ソースコードはこちらです
https://github.com/iwsh/oauth-tutorial/tree/v1.0.1

# 画面

![login successfully](https://github.com/iwsh/assets/blob/main/assets/qiita/article_5/login_successfully.png?raw=true)

# 実現したい処理の流れ

大きな流れとしては以下の 5 ステップです

1. Github の OAuth ページに移動
2. Github でアプリを許可し、アプリケーションにリダイレクトして一時 code を連携
3. 一時コードをバックエンドに連携
4. バックエンドで一時コードを使用して認証トークンを取得
5. 認証トークンを使用してユーザ情報を Guthub から取得し、ログイン情報として Cookie に格納する

今後実際にアプリに載せる際には、ユーザ情報をバックエンドで DB と照合してアプリケーションで持っているユーザ情報との紐づけを行うのがゴールになります。

![sequence](https://github.com/iwsh/assets/blob/main/assets/qiita/article_5/auth_sequence.png?raw=true)

# コード抜粋

## Github の OAuth ページに移動

フロントエンドにアクセスし、リンクから Github の OAuth ページに移動します。
リンクには自分のアプリケーションを識別する `client_id` と、OAuth によって実行できる権限を指定する `scope` を指定します

```js
// frontend/src/App.js

const github_client_id = process.env.REACT_APP_GITHUB_CLIENT_ID;
const github_oauth_url = `https://github.com/login/oauth/authorize?client_id=${github_client_id}&scope=user:read`;
```

```HTML
<a
    className='App-link'
    href={github_oauth_url}
>
    LOGIN with Github
</a>
```

`client_id` は Github で OAuth アプリを登録することで取得できます。

(参考)https://docs.github.com/developers/apps/building-oauth-apps/creating-an-oauth-app

ここでに Redirect 先としてフロントエンド ( `http://localhost:3000` ) を指定し、この URL にアプリの許可をクリック後にリダイレクトされるようになります。

リダイレクトされる際に `http://localhost:3000?code=6ad76ba1b90b43a` のようにクエリパラメータとして `code` が渡されます。

この `code` は API の認証に用いるトークンではなく、認証トークンを取得するための一時コードとなっています。
認証トークン取得のためにはこの一時コードに加えて、 OAuth アプリを登録時に発行される "Client Secret" が必要となるので、万一漏洩してしまっても単体ではアカウントの情報にアクセスしたり操作することはできません。

逆にいえば Client Secret は決して外に出してはならないので、フロントエンドに持たせることなくバックエンドに持たせて内々で利用します。

## 一時コードをバックエンドに連携

一時コードを受け取るための API エンドポイントを作成します。今回は FastAPI を使用しました。

```py
# backend/login/login.py

class LoginOauthRequest(BaseModel):
    code: str

class GithubOauth:
    router = APIRouter()
    client_id = os.getenv("GITHUB_CLIENT_ID")
    client_secret = os.getenv("GITHUB_CLIENT_SECRET")

    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.router.add_api_route("/login/oauth/github", self.login, methods=["POST"])

    def login(self, request: LoginOauthRequest, response: Response):
        code = request.code
        ...
```

このエンドポイントにフロントエンドから `axios` で `code` の値を送信します

```js
useEffect(() => {
  if (code && !message) {
    axios
      .post(
        backend_baseurl + "/login/oauth/github",
        {
          code: code,
        },
        {
          headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
          },
        }
      )
      .then((response) => {
        setMessage(response.data.message);
        setUsername(response.data.username);
        setAvatarUrl(response.data.avatar_url);
      })
      .catch((error) => {
        setMessage("Cannot login. Try Again.");
      });
  }
});
```

## バックエンドで認証トークンを取得

ユーザから連携された一時コードと `client_id`, `client_secret` を POST リクエストで Github に送信し、認証トークンを取得します。
このリクエストが一回実行されると一時コードは失効し、お役御免となります。

```py
def getGithubToken(self, code: str) -> str:
    url = "https://github.com/login/oauth/access_token"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    data = {
        "client_id": self.client_id,
        "client_secret": self.client_secret,
        "code": code
    }

    response = requests.post(url, headers=headers, json=data).json()
    return response["access_token"]
```

## ユーザ情報を Guthub から取得

取得した認証トークンを使用することでユーザとして Github の API を利用することができます。
実行できる API・アクセスできる情報は OAuth ページへのリンクに含まれていた`scope`によって決まります。

今回はユーザ情報を取得し、そこからユーザ名とアバター画像の URL を取得しています。

```py
def getGithubUser(self, token: str) -> str:
    url = "https://api.github.com/user"
    headers = {
        "Authorization": "Bearer {}".format(token),
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    response = requests.get(url, headers=headers).json()
    print(response)
    return response
```

## ログイン情報として Cookie に格納する

ログイン情報は JWT を暗号化して Cookie に格納するのが比較的安全なようです。
（この辺は目下勉強中ですので参考程度でお願いします。）

```py
payload = {"username": username}
token = jwt.encode(payload, self.secret_key, algorithm='HS256')
# JWTトークンをcookieとして設定します。
response.set_cookie(key="access_token", value=token)
```

## フロントエンドでの表示

OAuth が成功したことを確認するためにユーザ名・アバターをフロントエンドに渡して表示させています。

バックエンド側

```py
return {
    "message": "login successfully",
    "username": username,
    "avatar_url": avatar_url,
}
```

フロントエンド側

```js
{
  message ? (
    <div>
      <p>{message}</p>
    </div>
  ) : null;
}
{
  username ? (
    <div>
      <img src={avatar_url} alt="user_icon" height="100" />
      <p>Hello {username}.</p>
    </div>
  ) : null;
}
```

# おわりに

勉強を進めるにあたって ChatGPT にめっちゃ助けられました。今回のほとんどのコードは ChatGPT に書かせたものをマイナーチェンジ・デバッグしていくような形で作成しています。

典型的な実装やベストプラクティスを学ぶのにはものすごく便利で、手放せなくなってしまいますね
（たまに大嘘つきますが...笑）
