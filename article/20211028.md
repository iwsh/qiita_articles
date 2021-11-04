# Gitで継続的Qiita記事投稿をする part.1

初投稿です。  

Qiita投稿を今後も継続するために(?)、CI/CD（継続的インテグレーション/デリバリー）のような要領でGitからシームレスにQiita記事の投稿を目指したいと思います。  
同じような取り組みをしている方は沢山いると思いますが、勉強のために公式ドキュメントなどの一次情報を見て取り組んでいく予定です。 


## 目標
一旦以下のような仕組みを目標とします。

1. ローカル (WSL2-Ubuntu20.04) で記事をmarkdownファイルで作成
1. stgブランチに変更をcommit
1. GithubにpushするとQiitaに記事がprivateで投稿される
1. stagingからmasterのプルリクがマージされると、privateから通常の公開に変更される


## 課題
解決が必要な技術課題は以下の3つ。

1. Githubの特定ブランチの更新(push, プルリクのマージ)をトリガーにQiita操作のためのロジックを実行する方法

    知識はないが Github Actions などで実施できそう

1. Qiitaに記事を投稿するためのAPI

    Qiitaのページ下部のリンクからAPIドキュメントを参照できる  
    [POSTリクエスト](https://qiita.com/api/v2/docs#post-apiv2items)で記事を投稿できそう

1. Qiitaのprivate記事を一般公開するためのAPI

    こちらも同じくAPIドキュメントを参照
    [PATCHリクエスト](https://qiita.com/api/v2/docs#patch-apiv2itemsitem_id)でprivateのフラグを更新することでprivate記事を一般公開できそう


まずは「Qiitaに記事を投稿するためのAPI」「Qiitaのprivate記事を一般公開するためのAPI」の使用に取り組み、本記事をAPIで投稿することを目指す。


