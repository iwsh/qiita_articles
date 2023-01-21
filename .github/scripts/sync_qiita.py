#!/usr/bin/env python
import os
import re
import modules.qiita as qiita
from logging import getLogger, StreamHandler, Formatter, INFO

token_qiita = os.environ['QIITA_TOKEN']
dir_articles = "articles"

logger = getLogger(__name__)
logger.setLevel(INFO)
handler = StreamHandler()
formatter = Formatter('%(asctime)s - %(name)s [%(levelname)s] %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


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


def grouping_articles(df_qiita_articles):
    dic_groups = {
        "local_only": [],
        "both": [],
        "qiita_only": [],
    }
    # titleがQiita上の記事になければ新規記事として扱う
    # TODO: title変更対応

    # localの記事を取得
    l_articles_local = [
        file for file in os.listdir(dir_articles) if file.endswith(".md")
    ]
    l_articles_local.remove("README.md")

    logger.debug(l_articles_local)

    for article_local in l_articles_local:
        title = os.path.splitext(article_local)[0]
        if df_qiita_articles.empty:
            logger.info("There is no article in Qiita")
            # Qiitaに記事がなければ全て新規投稿対象
            article_info = {
                "title": title,
                "local_path": os.path.join(dir_articles, article_local),
            }
            dic_groups["local_only"].append(article_info)
        else:
            # タイトルが一致する記事があるか検索
            logger.debug(df_qiita_articles)
            qiita_article = df_qiita_articles.query(f"title == '{title}'")
            if qiita_article.empty:
                # Qiita上にないlocalの記事は新規投稿対象
                article_info = {
                    "title": title,
                    "local_path": os.path.join(dir_articles, article_local),
                }
                dic_groups["local_only"].append(article_info)
            elif qiita_article.shape[0] == 1:
                # Qiita・local両方にある場合は本文に更新があれば更新対象
                article_info = {
                    "id": qiita_article.iloc[0]["id"],
                    "title": title,
                    "local_path": os.path.join(dir_articles, article_local),
                    "qiita_article_body": qiita_article.iloc[0]["body"],
                }
                dic_groups["both"].append(article_info)
            else:
                raise Exception(
                    "There are multiple articles with the title:"
                    f"{title} in Qiita.")

    for _, row in df_qiita_articles.iterrows():
        if f"{row['title']}.md" not in l_articles_local:
            article_info = {
                "id": row["id"],
                "title": row["title"],
            }
            dic_groups["qiita_only"].append(article_info)
    return dic_groups


def post_articles(l_article_info):
    for article_info in l_article_info:
        title = article_info["title"]
        logger.info(f"Sending post request: {title}")
        logger.debug("local_path: %s", article_info["local_path"])
        with open(article_info["local_path"], "r") as f:
            str_body = f.read()
        try:
            tags = get_tags(str_body)
        except Exception:
            logger.error("Cannot get tags from %s", article_info["local_path"])
            raise Exception("Failed to post an article")
        private = is_private(str_body)
        # developへのpushの場合、新規記事は全てprivateとしてpostする
        if os.getenv("REF_NAME") == "develop" and not private:
            logger.info(
                "[develop mode] New article is handled with private flag")
            private = True
        res = qiita.post_article(title, str_body, token_qiita,
                                 tags=tags, private=private)
        logger.debug("status_code:%s", res.status_code)
        logger.info(f"{title} posted")
    logger.info(f"{len(l_article_info)} articles posted successfully")


def delete_articles(l_article_info):
    # developへのpushの場合、削除は行わない
    if os.getenv("REF_NAME") == "develop":
        logger.info(
            "[develop mode]" +
            f"DryRun: {len(l_article_info)} articles deleted successfully"
        )
        return
    for article_info in l_article_info:
        title = article_info["title"]
        id_article = article_info["id"]
        logger.info(f"Sending delete request: {title}")
        res = qiita.delete_articles(id_article, token_qiita)
        logger.debug("status_code:%s", res.status_code)
        logger.info(f"{title} deleted")
    logger.info(f"{len(l_article_info)} articles deleted successfully")


def patch_updated_articles(l_article_info):
    count_update = 0
    for article_info in l_article_info:
        title = article_info["title"]
        id_article = article_info["id"]
        qiita_article_body = article_info["qiita_article_body"]
        with open(article_info["local_path"], "r") as f:
            str_body = f.read()
        if str_body.rstrip() == qiita_article_body.rstrip():
            logger.info(f"{title} is NOT updated")
        else:
            logger.info(f"{title} is updated")
            count_update += 1
            try:
                tags = get_tags(str_body)
            except Exception:
                logger.error("Cannot get tags from %s",
                             article_info["local_path"])
                raise Exception("Failed to post an article")
            private = is_private(str_body)
            # developへのpushの場合、公開済みの記事のprivateフラグを維持する
            if os.getenv("REF_NAME") == "develop":
                private_in_qiita = is_private(qiita_article_body)
                if private != private_in_qiita:
                    logger.info(
                        "[develop mode]" +
                        f"Private flag change for {title} is ignored"
                    )
                    private = private_in_qiita
            res = qiita.patch_articles(id_article, title, str_body,
                                       token_qiita, tags=tags, private=private)
            logger.debug("status_code:%s", res.status_code)
            logger.info(f"{title} updated")
    logger.info(f"{count_update} articles updated successfully")


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


if __name__ == "__main__":
    main()
