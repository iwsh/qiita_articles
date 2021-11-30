初投稿です。  

3日坊主とならずにQiita投稿を継続するために、CI/CD（継続的インテグレーション/デリバリー）のような要領でGitからシームレスにQiita記事の投稿を目指したいと思います。  
同じような取り組みをしている方は沢山いると思いますが、勉強のために公式ドキュメントなどの一次情報を見て取り組んでいきます。 


# 目標
一旦以下のような仕組みを目標とします。

1. ローカル (WSL2-Ubuntu20.04) で記事をmarkdownファイルで作成
1. stgブランチに変更をcommit
1. GithubにpushするとQiitaに記事が限定公開で投稿される
1. stagingからmainのプルリクがマージされると、privateから通常の公開に変更される


# 課題
解決が必要な技術課題は以下の3つ。

1. APIによるQiitaの操作

1. Githubの更新をトリガーにロジックを実行する方法

    知識はないが Github Actions などで実施できそう

本記事では1項目目のAPIによるQiitaの操作を説明します。

# APIによるQiitaの操作
Qiitaのページ下部のリンクからAPIドキュメントを参照できます。  
このAPIを使ってどのようにQiit投稿を操作できるか試していきます。  

APIのテストツールとしては Postman が定番ですが、今回は VS Code の REST Client 拡張機能を使用しました

## 前準備
まずはQiitaをAPIで操作するための認証tokenを発行します

1. Qiitaにログインし、右上にあるアイコンをクリック > 設定 > アプリケーション と進む
1. 「個人用アクセストークン」の欄から「新しくトークンを発行する」をクリック
1. アクセストークンの説明を入力、スコープの「read_qiita」「write_qiita」にチェックして「発行する」をクリック
1. 表示される個人用アクセストークンをコピペして保存しておく（トークンはこの時の画面でしか表示されないので注意）

続いてAPI動作確認のためにVS Codeを設定していきます。
1. 左のメニューから拡張機能を開き、「REST Client」をインストール
1. `Ctrl + ,` で設定画面を開き、`settings.json` を開く
1. REST Client の環境変数としてhost, tokenを記述
    ```
    {
        "rest-client.environmentVariables": {
            "$shared": {},
            "qiita": {
                "host": "qiita.com",
                "token": "コピーしたtoken文字列"
            }
        }
    }
    ```
1. `.http`拡張子のファイルを作成し、VS Codeで開く
1. `Ctrl + Alt + e` でREST Clientの環境を `qiita` に設定

この `*.http` ファイルにAPIリクエストの内容を記述するとリクエストを送信するボタンが現れ、リクエストの送信ができます。  
1ファイルの中で複数のリクエストを書く際には`###`でブロックを分割して記入します

また、`{{host}}`のようにブランケット2個で囲うことにより、上記で設定した変数を利用することができます。  
（もちろんべた書きでも動作しますが、今回は資材をgitで管理する都合上`token`を環境変数に持たせています。）

以下のリクエストは[こちらのファイル](https://github.com/iwsh/qiita_articles/blob/main/api_test/qiita_api.http)にあるリクエストを実行したものです

## 記事の投稿
[POSTリクエスト](https://qiita.com/api/v2/docs#post-apiv2items)で限定公開の記事を投稿します。

レスポンス内容
```
HTTP/1.1 201 Created
Date: Sat, 27 Nov 2021 06:28:08 GMT
Content-Type: application/json; charset=utf-8
Transfer-Encoding: chunked
Connection: close
Server: nginx

...(省略)
```

## 記事一覧の取得
[GETリクエスト](https://qiita.com/api/v2/docs#get-apiv2authenticated_useritems)で自分の作成した記事の一覧を取得します

レスポンス内容
```
HTTP/1.1 200 OK
Date: Tue, 30 Nov 2021 12:55:30 GMT
Content-Type: application/json; charset=utf-8
Transfer-Encoding: chunked
Connection: close
Server: nginx
(中略)
[
    {
        \\ key-valueの記事情報
    },
    {
        \\ max(記事数, per_pageのクエリ)だけkey-valueがリスト内に並ぶ
    }
]
```

## 記事の更新
[PATCHリクエスト](https://qiita.com/api/v2/docs#patch-apiv2itemsitem_id)で記事を更新します。

レスポンス内容
```
HTTP/1.1 200 OK
Date: Tue, 30 Nov 2021 14:26:23 GMT
Content-Type: application/json; charset=utf-8
Transfer-Encoding: chunked
Connection: close
Server: nginx
```

# 続く
後編は Github Actions 中心に書く予定です