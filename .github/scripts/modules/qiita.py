import json
import requests
import pandas as pd

host = "qiita.com"


def get_articles(authz_token):
    l_articles = []
    page = 1
    per_page = 10
    while True:
        res = get_articlePage(authz_token, page, per_page)
        page += 1
        l_articles_page = json.loads(res.text)
        if l_articles_page:
            l_articles.extend(l_articles_page)
        else:
            break
    df_articles = pd.DataFrame(l_articles)
    return df_articles


def get_articlePage(authz_token, page, per_page):
    path = "/api/v2/authenticated_user/items"
    query = {
        "page": page,
        "per_page": per_page
    }
    headers = {
        "Authorization": f"Bearer {authz_token}",
    }
    res = requests.get(f"https://{host}{path}",
                       params=query, headers=headers)
    # 異常な応答の場合エラーが発生　
    res.raise_for_status()
    return res


def post_article(title, str_body, authz_token, tags, private=True):
    path = "/api/v2/items"
    headers = {
        "Authorization": f"Bearer {authz_token}",
        "Content-Type": "application/json",
    }
    dic_data = {
        "title": title,
        "body": str_body,
        "private": private,
        "tags": tags,
        "tweet": False
    }
    json_data = json.dumps(dic_data)
    res = requests.post(f"https://{host}{path}",
                        data=json_data, headers=headers)
    res.raise_for_status()
    return res


def delete_articles(article_id, authz_token):
    path = f"/api/v2/items/{article_id}"
    headers = {
        "Authorization": f"Bearer {authz_token}",
    }
    res = requests.delete(f"https://{host}{path}", headers=headers)
    res.raise_for_status()
    return res


def patch_articles(article_id, title, str_body, authz_token, tags,
                   private=True):
    path = f"/api/v2/items/{article_id}"
    headers = {
        "Authorization": f"Bearer {authz_token}",
        "Content-Type": "application/json",
    }
    dic_data = {
        "title": title,
        "body": str_body,
        "private": private,
        "tags": tags,
        "tweet": False
    }
    json_data = json.dumps(dic_data)
    res = requests.patch(f"https://{host}{path}",
                         data=json_data, headers=headers)
    res.raise_for_status()
    return res
