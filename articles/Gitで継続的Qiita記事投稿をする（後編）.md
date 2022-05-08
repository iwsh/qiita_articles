<!-- tag: Qiita,自動化,GitHub,GitHubAction,CICD -->
<!-- private: False -->

# はじめに

[前編](https://qiita.com/iwsh/items/744eeeeca72be919e859)に引き続いて、CI/CD の要領で Git で管理した記事をシームレスに Qiita に投稿することを目指したいと思います。
勉強のためになるべく公式ドキュメントなどの一次情報を参照して取り組んでいきます。

# 目標 (再掲)

以下のような仕組みを目標とします。

1. ローカルで記事を markdown ファイルで作成
1. Github に push すると Qiita に記事が投稿される
1. 更新・削除を行って Github を更新すると Qiita の記事も同期して更新・削除が行われる

# 課題

解決が必要な技術課題は以下の 2 つ。(再掲)

1. API による Qiita の操作
1. Github の更新をトリガーに更新スクリプトを実行する方法

前編では 1. についてまとめました。
後編は 2. を実現するために Github Actions についてまとめ、実際に自動投稿処理を作成していきます。

# Github Actions とは

GitHub に備わっている CI/CD ツールです。
指定したブランチへの push やプルリクをトリガーに、GitHub 上でコードのビルド、テスト、デプロイ等の処理を実行することができます。
Free プランでもパブリックリポジトリであれば無料で利用可能です。

今回は Github Actions を使って、以下のような処理フローを構築したいと思います。

1. Github 上の main ブランチを更新する（push or プルリク）
1. Github Actions のワークフローが起動
   1. main ブランチ内の記事と Qiita との差分を確認し、変更箇所を特定
   1. Qiita の API で main ブランチに合わせて新規投稿・更新・削除を実行する

## ワークフローの作成

Github リポジトリのページの「Actions」タブから作成します。
![create workflow](https://github.com/iwsh/assets/raw/main/assets/qiita/article_2/create_workflow.png)

今回は「Simple workflow」をベースに作成していきます。

Configure をクリックすると、以下のようなデフォルトの YAML ファイルが表示されます。

```YAML
# This is a basic workflow to help you get started with Actions

name: CI

# Controls when the workflow will run
on:
  # Triggers the workflow on push or pull request events but only for the main branch
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

  # Allows you to run this workflow manually from the Actions tab
  workflow_dispatch:

# A workflow run is made up of one or more jobs that can run sequentially or in parallel
jobs:
  # This workflow contains a single job called "build"
  build:
    # The type of runner that the job will run on
    runs-on: ubuntu-latest

    # Steps represent a sequence of tasks that will be executed as part of the job
    steps:
      # Checks-out your repository under $GITHUB_WORKSPACE, so your job can access it
      - uses: actions/checkout@v3

      # Runs a single command using the runners shell
      - name: Run a one-line script
        run: echo Hello, world!

      # Runs a set of commands using the runners shell
      - name: Run a multi-line script
        run: |
          echo Add other actions to build,
          echo test, and deploy your project.

```

この YAML によってワークフローが定義されるという仕組みのようです。

構文の詳細はこちらに記載があります。
https://docs.github.com/ja/actions/using-workflows/workflow-syntax-for-github-actions

「build」という名前の job において Ubuntu 環境を起動し、steps に書かれた処理を順に実行するようです。

「uses」の記述が見慣れないですが、これはパブリックに公開されているコードを引っ張ってきてアクションを実行するものです。
`{owner}/{repo}@{ref}`という記法で、github のリポジトリとバージョンを指定しています。
上のコード例だと https://github.com/actions/checkout を参照していて、ワークフロー実施時にリポジトリ内の資材を利用できるようにローカルリポジトリを設定し、ブランチのチェックアウトを行っています。

このように汎用的なコードを先人の肩にのっかってサクッと取り込めるのは嬉しいところですね。

# Qiita 自動投稿の実装

ようやく本題です。
今回は Qiita 投稿処理自体は Python で作成し、Github Actions で Python 環境をセットアップしてスクリプトをキックします。

実際に運用しているリポジトリはこちらです。
https://github.com/iwsh/qiita_articles

## 全体構成

```
.
├── .github
│   ├── scripts
│   │   ├── modules
│   │   │   └── qiita.py
│   │   └── sync_qiita.py
│   └── workflows
│       └── blank.yml
├── articles
│   └── <記事タイトル>.md
└── requirements.txt
```

- qiita.py
  Qiita の API 処理を行うモジュール
- sync_qiita.py
  ワークフローで実行するスクリプト
- blank.yml
  Github Actions のワークフローを定義する YAML ファイル

## ワークフロー

前述のデフォルトのワークフローから以下のように steps 部分を変更しました。

```YAML
    steps:
      # リポジトリ資材を利用できるようにチェックアウト
      - uses: actions/checkout@v3

      # Python3 をインストール
      - name: Setup Python
        uses: actions/setup-python@v2.2.2
        with:
          python-version: '3.x'
          architecture: 'x64'

      # ライブラリのインストール
      - name: Install python libraries
        run: pip install -r requirements.txt

      # Qiita 投稿のための Python コード実行
      - name: Run python script
        run: python .github/scripts/sync_qiita.py
        env:
          QIITA_TOKEN: ${{ secrets.QIITA_TOKEN }}

```

Python3 のインストールはこちらのアクションを利用しています。
https://github.com/actions/setup-python

`Run python script` のステップにおいて API を利用するには、[前編](https://qiita.com/iwsh/items/744eeeeca72be919e859)で説明したように Qiita の認証トークンが必要となるため、環境変数として渡しています。

公開するコードに平文で書くわけにもいかないので安全な渡し方を調査したところ、Github に登録した secrets を`${{ secrets.QIITA_TOKEN }}`のように呼び出すことができるようです。
https://docs.github.com/ja/actions/security-guides/encrypted-secrets

AWS などのサービスを使う際にも、同じ要領でアクセスキーを渡す実装にするのが良さそうですね。

## Python スクリプト

記事では main 関数のみ抜粋します。
ソースコード全文は[リポジトリ](https://github.com/iwsh/qiita_articles/tree/main/.github/scripts)を参照してください

```Python
def main():
    logger.info("start")
    # Qiitaから投稿された記事の状態を取得
    df_qiita_articles = qiita.get_articles(token_qiita)
    logger.info("Get article data from Qiita")

    # Qiita記事とlocal上markdownの存在比較
    dic_groups = grouping_articles(df_qiita_articles)
    logger.info(f"Only in local: {len(dic_groups['local_only'])}")
    logger.info(f"Only in Qiita: {len(dic_groups['qiita_only'])}")
    logger.info(f"In both local and Qiita: {len(dic_groups['both'])}")

    # 新規投稿の実行
    post_articles(dic_groups["local_only"])

    # 削除の実行
    delete_articles(dic_groups["qiita_only"])

    # 更新の実行
    patch_updated_articles(dic_groups["both"])

    # 完了
    logger.info("end")
```

API で取得した記事一覧とローカルファイル (=リポジトリ上のファイル) をもとに記事を

1. ローカルのみにあるもの
2. Qiita 上にのみあるもの
3. ローカル・Qiita 上の両方にもあるもの

に分別し、1.は新規記事として POST し、2.は Qiita の記事を DELETE します。 3.については`patch_update_articles`内で本文に更新が行われているか判定し、更新があれば PATCH でローカルの記事に情報を更新します。

## 困った箇所

### 記事を一意に特定する方法

ローカルのどの記事と Qiita のどの記事が対応しているか判定する方法に悩みました。
Qiita に投稿すると各記事に ID が付与されるので、その ID で管理できるのが一番良いのですが、記事そのものとは別に記事のメタデータ管理が必要となってしまいます。

管理対象は Git リポジトリに閉じたいので、メタデータ管理を CSV 等で管理することも考えたのですが、以下のような不都合が生じてしまいます。

1. 管理ファイルを変更してコミットしてしまうことで故障が発生する可能性がある。
1. ワークフローが複雑化する
   ⇒ 管理ファイル更新のためリポジトリへの push をワークフロー内に実装する必要がある
   ⇒ この更新の push をトリガに再びワークフローが起動してしまう懸念がある
1. ブランチ間で管理ファイルの中身が違うことがバグの原因となる

結局、マークダウンのファイル名を記事タイトルとし、Qiita 上の記事タイトルと照合することで同じ記事かどうかを判定することにしました。
Qiita では同じタイトルで複数記事を投稿可能ですが、同じディレクトリに記事ファイルを配置する仕様のため、自動投稿で投稿された記事はタイトルによって一意に特定することができます。

以下のようにいくつか問題はあるものの、ひとまず目をつぶることにしました...**（よいアイデアがあれば教えてください！）**

- ブラウザなどから Qiita に既存記事と同名の記事を投稿してしまうと、リポジトリの記事と正しく同期できなくなる。
- 既存記事の記事タイトルを変更した場合、記事の更新ではなく「新規記事の投稿＋既存記事の削除」として扱われる。

### tag, private の扱い

Qiita の API では投稿の際に`tag`を設定することが必須となっており、また、記事を「限定公開」「一般公開」どちらにするかを決める`private`というパラメータもあります。
これが地味に厄介で、先述の通りメタデータを CSV 等で管理するのには様々な不都合があります。

ただ、これらの値は事前に決めて投稿処理ができるという点が記事 ID と異なっています。
今回は以下の例ように記事のマークダウンに HTML のコメントアウト記法でこれらのパラメータを埋め込み、投稿スクリプト内で正規表現で抽出する処理を実装しました。

```Markdown
<!-- tag: Qiita,自動化,GitHub,GitHubAction,CICD -->
<!-- private: True -->

# 記事ここから
冒頭のパラメータはHTMLで表示する際にはコメントアウトされる
...
```

Python で `tag` や `private` を抽出する処理は以下です。
`private` のコメントがない場合は限定公開記事として扱っています

```Python
def get_tags(str_body):
    tags = []
    str_tags = re.findall("<!-- tag: (.*) -->", str_body)
    if len(str_tags) == 0:
        logger.error("No tag in the local article.")
        raise Exception
    l_tags = str_tags[0].split(",")
    for tag in l_tags:
        tags.append({"name": tag})
    return tags


def is_private(str_body):
    str_private = re.findall("<!-- private: (.*) -->", str_body)
    if len(str_private) == 0:
        logger.warning(
            "Local article is not specified whether it is private or not")
        logger.warning("uploaded as private Article.")
        private = True
    else:
        private = eval(str_private[0])
    return private
```

# おわりに

多少の課題はあるものの、個人的にはある程度満足のいく仕組みを構築できました。
ただし、基本的には投稿前に限定公開記事で一旦上げてから確認しているので、main の更新頻度を下げるためにも限定公開での新規投稿は別のワークフローを作成した方が便利そうですね。

1. 記事を作成する
2. 限定公開でプレビューする
3. よさそうだったら main ブランチにマージ

今後対応していきたいと思います。

Qiita の API はドキュメントが不親切だったり、たまに変なレスポンスコードが返ってきたり、もう少し改善してほしいところです。
エンジニアのユーザが多いですし、一定の需要はあると思うんですが...

Github Actions は最初に見たときどのように処理実行されているか分かりづらいと感じましたが（特に`uses`の部分）、こういった簡単なものでも自力で組み立てると一気に理解が進みますね。
以前触ったことのある Jenkins と比べると非常にとっつきやすくて快適だなと感じました。ドキュメントも充実していますし、UI もさすがに見やすいですね。

並列処理や同期を含むような複雑なワークフローを構築する場合にこの使いやすさを保てるかどうかが気になるところです。
