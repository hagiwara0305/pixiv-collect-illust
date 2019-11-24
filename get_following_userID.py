from pixivpy3 import *
from time import sleep
from robobrowser import RoboBrowser
from bs4 import BeautifulSoup
import MySQLdb, json, ulid, sys, io, re, os, sys

connection = MySQLdb.connect(
    host='localhost',
    user='root',
    db='pixiv_image_collect',
    # passeord='',
    charset='utf8'
)

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
following_users_id = [4935]

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

    user_cursor = connection.cursor()
    user_cursor.execute(
        "INSERT INTO user (user_id, user_name, account_name, saving_direcory) VALUES (%s, %s, %s, %s)",
        (
            user_id,
            user_info_json.user.name,
            user_info_json.user.account,
            saving_direcory_path
        )
    )
    # connection.commit()

    # enumerate()を使うことでi:インデックス work_info:要素 でループ
    for i, work_info in enumerate(works_info.response):
        print(work_info)

        # 18禁はダメ
        if 'R-18' in work_info.tags:
          continue

        # ダウンロード
        work_title = work_info.title.replace("/", "-") # '/'はPathとして扱われるため回避

        print("Procedure: %d/%d" % (i + 1, works_info.pagination.total))
        print("Title: %s" % work_title)
        print("URL: %s" % work_info.image_urls.large)
        print("Caption: %s" % work_info.caption)
        print("Views_count: %s" % work_info.stats.views_count)
        print("Favorited_count: %s" % str(work_info.stats.favorited_count.public + work_info.stats.favorited_count.private))
        print(work_info.tags)
        print(separator)

        try:
            # 漫画以外のイラストデータを取得する
            if not "manga" if work_info.is_manga else "illust":
                # イラストの場合
                illust_name = str(ulid.new())+".jpg"

                illust_cursor = connection.cursor()
                illust_cursor.execute(
                    "INSERT INTO illust (illust_id, user_id, title, url, caption, illust_name, views_count, favorited_count, create_date, update_date)" +
                        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    [
                        work_info.id,
                        user_id,
                        work_title,
                        work_info.image_urls.large,
                        work_info.caption,
                        illust_name,
                        work_info.stats.views_count,
                        work_info.stats.favorited_count.public + work_info.stats.favorited_count.private,
                        work_info.created_time,
                        work_info.reuploaded_time
                    ]
                )
                # tagの確認
                for tag_item in work_info.tags:
                    tag_check_cursor = connection.cursor()
                    tag_check_cursor.execute("SELECT tag_id FROM tag WHERE tag_name=%s", [tag_item])

                    tag_id = tag_check_cursor.fetchone()
                    if tag_id is None:
                        tag_id = str(ulid.new())
                        illust_cursor.execute(
                            "INSERT INTO tag (tag_id, tag_name) VALUES (%s, %s)",
                            (
                                tag_id,
                                tag_item
                            )
                        )

                    illust_cursor.execute(
                        "INSERT INTO illust_tag (illust_id, tag_id) VALUES (%s, %s)",
                        (
                            work_info.id,
                            tag_id
                        )
                    )
                aapi.download(work_info.image_urls.large, path=saving_direcory_path, name=illust_name)
                connection.commit()
                sleep(2)
        except MySQLdb._exceptions.IntegrityError:
            print("uniqueが被りました...")

print("\nThat\'s all.")