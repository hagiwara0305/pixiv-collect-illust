from pixivpy3 import *
import json
from time import sleep
import sys, io, re, os
import ulid
from robobrowser import RoboBrowser
from bs4 import BeautifulSoup

f = open("client.json", "r")
client_info = json.load(f)
f.close()

# pixivpyのログイン処理
api = PixivAPI()
api.login(client_info["pixiv_id"], client_info["password"])
aapi = AppPixivAPI()
aapi.login(client_info["pixiv_id"], client_info["password"])

# フォローユーザーの総数を取得
self_info = aapi.user_detail(client_info["user_id"])
following_users_num = self_info.profile.total_follow_users

# フォローユーザー一覧ページのページ数を取得
if(following_users_num%48 != 0):
    pages = (following_users_num//48)+1
else:
    pages = following_users_num//48

#タグ除去用
p = re.compile(r"<[^>]*?>")
# [jump:1]形式除去用
jump = re.compile(r"\[jump:.+\]")
#ファイルエンコード設定用
character_encoding = 'utf_8'

# Webスクレイパーのログイン処理
pixiv_url = 'https://www.pixiv.net'
browser = RoboBrowser(parser='lxml', history=True)
browser.open('https://accounts.pixiv.net/login')
form = browser.get_forms('form', class_='')[0]
form['pixiv_id'] = client_info["pixiv_id"]
form['password'] = client_info["password"]
browser.submit_form(form)

# フォローユーザー一覧ページのURLを設定
target_url = 'https://www.pixiv.net/bookmark.php?type=user&rest=show&p='

# 全てのフォローユーザーのユーザIDを取得
following_users_id = [5476137]

print(following_users_id)

print("\n▽▽▽\n")

##### ダウンロード処理 #####
# 絵師IDから絵師情報を取得
for user_id in following_users_id:

    # ユーザ情報（作品数、絵師名）を取得
    user_info_json = aapi.user_detail(int(user_id))
    total_illusts = user_info_json.profile.total_illusts
    total_manga = user_info_json.profile.total_manga
    illustrator_name = user_info_json.user.name

    # イラスト情報を取得（とりあえず300作品取得）
    works_info = api.users_works(int(user_id), page=1, per_page=300)

    separator = "============================================================"
    print("Artist: %s" % illustrator_name)
    print("Works: %d" % works_info.pagination.total)
    print(separator)

    saving_direcory_path = "./pixiv_images/"
    if not os.path.exists(saving_direcory_path + str(user_id)):
        os.mkdir(saving_direcory_path + str(user_id))

    saving_direcory_path += str(user_id)
    print(saving_direcory_path)

    # ダウンロード
    # enumerate()を使うことでi:インデックス work_info:要素 でループ
    for i, work_info in enumerate(works_info.response):

        # 18禁はダメ
        if 'R-18' in work_info.tags:
          continue

        # ダウンロード
        work_title = work_info.title.replace("/", "-") # '/'はPathとして扱われるため回避

        print("Procedure: %d/%d" % (i + 1, works_info.pagination.total))
        print("Title: %s" % work_title)
        print("URL: %s" % work_info.image_urls.large)
        print("Caption: %s" % work_info.caption)
        print(work_info.tags)
        print(separator)

        # 漫画の場合
        if not "manga" if work_info.is_manga else "illust":
        # # イラストの場合
            aapi.download(work_info.image_urls.large, path=saving_direcory_path, name=str(ulid.new())+".jpg")
            sleep(1)

print("\nThat\'s all.")