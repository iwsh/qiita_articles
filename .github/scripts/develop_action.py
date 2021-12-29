#!/usr/bin/env python
import requests
from modules import qiita
import os
import re
import logging

workspace = os.environ["GITHUB_WORKSPACE"]

def main():
    # Qiitaから投稿された記事一覧を取得
    l_articles_qiita = qiita.get_pages()

    # git上の記事一覧を取得
    l_article_private = os.listdir(os.path.join(workspace, "articles", "private"))
    l_article_public = os.listdir(os.path.join(workspace, "articles", "public"))

    # privateの記事を作成・更新
    for fname_article in l_article_private:
        id_article = get_id_from_article(fname_article)

        l_id = [article_qiita["id"] for article_qiita in l_articles_qiita]
        if id_article in l_id:
            # update処理
            pass
        else:
            pass
            # post処理

            # responseのidをコメントで記事の1行目に記載             


    # publicの記事は新規作成の場合のみ限定公開で作成
    for fname_article in l_article_private:
        id_article = get_id_from_article(fname_article)

        l_id = [article_qiita["id"] for article_qiita in l_articles_qiita]
        if id_article not in l_id:
            pass
            # post処理

    # 完了
    print("ends.")


def get_id_from_article(fname_article):
    # "<!-- Qiita記事を保管するリポジトリ -->"
    with open(fname_article, "r") as f:
        line = f.readline()
    id_article = re.findall("<!-- ID:(.*) -->", line)
    return id_article

if __name__ == "__main__":
    main()
