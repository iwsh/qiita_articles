<!-- tag: Qiita,自動化,GitHub,GitHubAction,CICD -->
<!-- private: False -->

# はじめに

[前回](https://qiita.com/iwsh/items/744eeeeca72be919e859)に引き続いて、CI/CD の要領で Git で管理した記事をシームレスに Qiita に投稿することを目指したいと思います。  
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

## Qiita 自動投稿ワークフロー

今回作成したワークフローがこちらです

```YAML
# This is a basic workflow to help you get started with Actions

name: CD

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
  update_Qiita:
    # The type of runner that the job will run on
    runs-on: ubuntu-latest

    # Steps represent a sequence of tasks that will be executed as part of the job
    steps:
      # Checks-out your repository under $GITHUB_WORKSPACE, so your job can access it
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v2.2.2
        with:
          python-version: '3.x'
          architecture: 'x64'

      - name: Install python libraries
        run: pip install -r requirements.txt

      - name: Run python script
        run: python .github/scripts/sync_qiita.py
        env:
          QIITA_TOKEN: ${{ secrets.QIITA_TOKEN }}

```

1. リポジトリ資材を利用できるようにチェックアウト
1. Python3 をインストール
1. ライブラリのインストール
1. Qiita 投稿のための Python コード実行

という流れです。

## 記事一覧の取得

## 記事の更新

## 記事の削除

# 残課題
