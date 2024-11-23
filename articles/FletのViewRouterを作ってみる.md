<!-- tag: Flet,Python -->
<!-- private: False -->

# はじめに

フロントエンドといえば JavaScript (または TypeScript) で作るものという図式が完全に出来上がってしまっていますが、どうにも Javascript が好きになれないもので、Python で実戦的にフロントエンド書けるフレームワークはないのかとを探していました。

調べて一番出てくるのは Streamlit ですが、Python コードをサーバ側で処理するものなので、いわゆるフロントエンドとは別物ですよね。

そんな中、[Flet](https://flet.dev/docs/publish/web) というフレームワークが Static website としてホスティングすることができる (WebAssembly としてブラウザ上で Python code を動かせる！!) ということで「これは面白そうだ」と触ってみたのです。


# 画面を宣言的に書きたい

触っていく中でも困ったのが router のようなものが存在しないことでした。
公式ドキュメントの [Navigation and routing](https://flet.dev/docs/getting-started/navigation-and-routing) の例では以下のような実装が示されています。
```python
import flet as ft

def main(page: ft.Page):
    page.title = "Routes Example"

    def route_change(route):
        page.views.clear()
        page.views.append(
            ft.View(
                "/",
                [
                    ...(中略)
                ],
            )
        )
        if page.route == "/store":
            page.views.append(
                ft.View(
                    "/store",
                    [
                        ...(中略)
                    ],
                )
            )
        page.update()

    def view_pop(view):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go(page.route)


ft.app(main, view=ft.AppView.WEB_BROWSER)
``` 

main 関数の route_change 関数が route 変更イベントに対して条件分岐でどのような View のスタックを作成するか書いて行っています。

この例だと `/` の View は必ずスタックされ、route が `/store` のときには加えてもう一層の View がスタックされています。 

この手続き的な書き方続けるのはだいぶ厳しいので、自前の ViewRouter class を作成して宣言的に View を書けるようにしてみました。
 

# Router を使用したコード

以下のような全体像になりました
```
|-- core
|   `-- routed_view.py
|-- main.py
|-- requirements.txt
|-- router
|   |-- __init__.py
|   `-- router.py
`-- views
    |-- users
    |   `-- index.py
    `-- index.py
```

## main関数
entrypoint となる main.py のファイルはこのようになりました。

```python
import flet as ft

import router


def main(page: ft.Page):
    page.title = "Example"

    r = router.ViewRouter(page)

    def view_pop(view):
        page.views.pop()
        if len(page.views) > 1:
            page.update()
        else:
            page.go("/")

    page.on_route_change = r.route_change
    page.on_view_pop = view_pop

    page.go(page.route)


ft.app(target=main)
```

on_route_change では ViewRouter のメソッドを呼び出しています

## ViewRouter
router/router.py で ViewRouter を定義しています。

```python
import time

import flet as ft

from core.routed_view import RoutedView
from views.user.index import User
from views.index import Home

VIEWS: list[type[RoutedView]] = [
    Home,
    User,
]


class ViewRouter:
    page: ft.Page
    routes: dict[str, RoutedView] = {}

    def __init__(self, page: ft.Page):
        self.page = page
        for view in VIEWS:
            self.routes[view.get_path()] = view

    def route_change(self, route: ft.RouteChangeEvent):
        self.page.views.clear()

        head_view = None

        tr = ft.TemplateRoute(route.route)
        for path, view in self.routes.items():
            if matched := tr.match(path):
                head_view = view
                break

        if not matched:
            self.page.views.append(
                ft.View(
                    "/not_found",
                    [ft.Text(value="NOT FOUND. Redirect to Home in 3 seconds")],
                )
            )
            self.page.update()
            time.sleep(3)
            self.page.go(Home.get_path())
            return

        stack = head_view.gen_view_stack(self.page)

        while len(stack) > 0:
            self.page.views.append(stack.pop())

        self.page.update()
```

VIEWS に Application に追加する RoutedView を継承した class を登録して、これをもとに path に対する RoutedView の対応を持っておきます。

route が変更されると route と match する RoutedView を特定し、最前面に表示される `head_view` とします。

RoutedView は gen_view_stack メソッドを持っていて、これにより `head_view` から一つづつ背後にあるべき View に遡る形でページに追加する全ての View を取得します。
これを list の逆順に全て page に追加し、ページの更新を更新します。

# RoutedView

RoutedView は以下のような抽象クラスとなっていて、これを各 View の内容を示す class が継承しています。

core/routed_view.py

```python
from abc import ABC, abstractmethod
from typing import Optional

import flet as ft
from flet_core import Control


class RoutedView(ABC, ft.View):
    path: str
    parent: Optional["RoutedView"]

    @classmethod
    def get_path(cls) -> str:
        return cls.path

    @classmethod
    def generate(cls, page) -> ft.View:
        contents = cls.get_contents(page)
        view = cls(cls.path, contents)
        return view

    @classmethod
    def gen_view_stack(cls, page, stack=[]) -> list["RoutedView"]:
        stack.append(cls.generate(page))
        if cls.parent is None:
            return stack
        return cls.parent.gen_view_stack(page, stack)

    @classmethod
    @abstractmethod
    def get_contents(cls, page) -> list[Control]:
        raise NotImplementedError()

```

RoutedView はディレクトリのような階層構造を持っていて、例えば `/users` の path を持つ `Users` は、`/`を表す `Home` を `parent` としています。`Home` は一番先頭の階層となるので `parent` を持ちません

`gen_view_stack` は各クラスで定義された `get_contents` を呼び出すことで View を生成し、その後 `parent` で指定されている class の `gen_view_stack` を呼び出すことを再帰的に実行して先頭の階層までを View をスタックしたものを返します。


views/index.py
```python
import flet as ft
from flet_core.control import Control

from core.routed_view import RoutedView


class Home(RoutedView):
    path = "/"
    parent = None

    @classmethod
    def get_contents(self, page) -> list[Control]:
        def open_users_screen(e):
            page.go("/users")

        contents = [
            ft.AppBar(title=ft.Text("Flet app"), bgcolor=ft.colors.SURFACE_VARIANT),
            ft.ElevatedButton("Go to users", on_click=open_users_screen),
        ]

        return contents

```

views/users/index.py
```python
import flet as ft
from flet_core.control import Control
import requests

from core.routed_view import RoutedView
from views.index import Home


class Users(RoutedView):
    path = "/users"
    parent = Home

    @classmethod
    def get_contents(cls, page) -> list[Control]:
        contents = [
            ft.AppBar(title=ft.Text("ユーザ管理"), bgcolor=ft.colors.SURFACE_VARIANT),
            ...(中略)
        ]

        return contents

```

# おわりに

ViewRouter が個別のアプリケーションのglobal変数読んでいたり、気持ち悪いところが残っているので、今後改善していこうと思います。

（そもそも flet 自体に Router の機能存在していてほしかったんですが、需要無いんでしょうかね...？）
