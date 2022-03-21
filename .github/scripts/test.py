#!/usr/bin/env python
import os

print("hello python action")
print(len(os.environ["QIITA_TOKEN"]))