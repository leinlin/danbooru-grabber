#!/usr/bin/python
# coding:utf-8
import json
import os  # path manipulation
import sys
import urllib as urllib
import time
import requests
from xmltodict import parse
import base64
import hashlib
from PIL import Image
import time
import urllib3

status = 'not done yet'
danbooru_folder = os.getcwd() + '/Pictures/'
send_count = 0
post_url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=011b602e-8a5d-4829-909f-df8f17d5667e"
danbooru_url = "https://danbooru.donmai.us"  # type: str
sleep_time = 180


def file_extension(path):
    return os.path.splitext(path)[1]


def download(id):
    try:
        headers = {"Content-Type": "text/plain"}
        proxies = {'http': 'http://localhost:1080', 'https': 'http://localhost:1080'}
        global post_url

        r = requests.get(danbooru_url + '/posts/' + id + ".json", proxies = proxies, verify = False)
        print(r.content)
        jsonPost = r.json()

        if jsonPost["fav_count"] < 100 and jsonPost["score"] < 50:
            return False

        if jsonPost["score"] < 20:
            return False

        file_url = jsonPost["file_url"]

        if (not file_url.endswith(".jpg")) and (not file_url.endswith(".png")):
            return False

        rating = jsonPost["rating"]

        # if rating == "e":
        #     sourceStr = ""
        #     if u"source" in jsonPost:
        #         sourceStr = jsonPost[u"source"]
        #     data = {
        #         "msgtype": "text",
        #         "text": {
        #             "content": '{post_url}{id}\n角色:{character}\n作者:{artist}\n出处:{source}\n涩度:我好了，你也想好吗？（{rating}）\n评分:{score}\n喜欢:{fav_count}'.format(
        #                 post_url="https://danbooru.me/posts/", id=str(id), artist=jsonPost["tag_string_artist"],
        #                 character=jsonPost["tag_string_character"],
        #                 source=sourceStr,
        #                 rating="https://danbooru.donmai.us/posts/" + str(id),
        #                 score=jsonPost["score"],
        #                 fav_count=jsonPost["fav_count"]
        #             )
        #         }
        #     }
        #     requests.post(post_url, headers=headers, json=data)
        #     return False

        if rating == "s":
            rating = "吉良吉影觉得很(b)ok(i)"
        elif rating == "q":
            rating = "画画的老师说要把欧派想象成注水的气球"
        elif rating == "e":
            rating = "我好了，你也想好吗？"

        print("Download id:" + str(id))
        print("Download file:" + jsonPost["file_url"])
        request = requests.get(jsonPost["file_url"], timeout=90, proxies=proxies)
        file_size = int(jsonPost["file_size"])
        file_url = "Pictures/" + id + ".jpg"
        with open(file_url, "wb") as f:
            f.write(request.content)

        print(1)
        im = Image.open(file_url)
        x, y = im.size
        if x > 1920:
            y = y * 1920 / x
            x = 1920
            im = im.resize((x, y), Image.ANTIALIAS)
        elif y > 1920:
            x = x * 1920 / y
            y = 1920
            im = im.resize((x, y), Image.ANTIALIAS)

        if x >= y * 13 / 10:
            im = im.transpose(Image.ROTATE_270)

        im.mode = "RGB"
        try:
            im.save(file_url)

            f = open(file_url, "rb")
            imgData = f.read()
            f.close()
        except BaseException as e:
            print(e)
            if file_size < 2048 * 1024:
                imgData = request.content
            else:
                return False

        base64_data = base64.b64encode(imgData)
        md = hashlib.md5()
        md.update(imgData)
        res1 = md.hexdigest()

        data = {
            "msgtype": "image",
            "image": {
                "base64": base64_data,
                "md5": res1
            }
        }
        requests.post(post_url, headers=headers, json=data)
        sourceStr = ""
        if u"source" in jsonPost:
            sourceStr = jsonPost[u"source"]

        data = {
            "msgtype": "text",
            "text": {
                "content": '{post_url}{id}\n角色:{character}\n作者:{artist}\n出处:{source}\n涩度:{rating}\n评分:{score}\n喜欢:{fav_count}'.format(
                    post_url="https://danbooru.me/posts/", id=str(id), artist=jsonPost["tag_string_artist"],
                    character=jsonPost["tag_string_character"],
                    source=sourceStr,
                    rating=rating,
                    score=jsonPost["score"],
                    fav_count=jsonPost["fav_count"]
                )
            }
        }
        requests.post(post_url, headers=headers, json=data)
        print("Download complete")
        sys.stdout.flush()
        return True
    except BaseException as e:
        print(e)


def main():
    global post_url
    global sleep_time
    urllib3.disable_warnings()
    requests.adapters.DEFAULT_RETRIES = 5

    reload(sys)
    sys.setdefaultencoding('utf-8')

    sleep_time = 60
    id_file = open("id.txt", "r")
    id = int(id_file.readline()) + 1

    while id <= 400000001 and status == 'not done yet':
        try:
            id = id + 1
            if download(str(id)):
                id_file = open("id.txt", "w")
                id_file.write(str(id))
                time.sleep(sleep_time)
        except BaseException as e:
            time.sleep(1)
            print(e)

    print('Download successful!')


if __name__ == '__main__':
    main()
