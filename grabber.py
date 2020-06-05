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

status = 'not done yet'
danbooru_folder = os.getcwd() + '/Pictures/'
send_count = 0
post_url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=011b602e-8a5d-4829-909f-df8f17d5667e"
danbooru_url = "https://danbooru.donmai.us"  # type: str
queryStr = "tags=azur_lane+-rating:safe+order:score&limit=1000"
dict_cache = {}
pic_in_url = ""
pic_out_url = ""
dict_url = ""
sleep_time = 180


def file_extension(path):
    return os.path.splitext(path)[1]


def download(id):
    global dict_url
    try:
        proxies = {'http': 'http://localhost:1080', 'https': 'http://localhost:1080'}
        r = requests.get(danbooru_url + '/posts/' + id + ".json", proxies=proxies)
        jsonPost = r.json()

        print("Download file:" + jsonPost["file_url"])
        sys.stdout.flush()
        request = requests.get(jsonPost["file_url"], timeout=90, proxies=proxies)
        file_size = int(jsonPost["file_size"])

        global pic_in_url
        global pic_out_url

        with open(pic_in_url, "wb") as f:
            f.write(request.content)

        im = Image.open(pic_in_url)
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
            im.save(pic_out_url)

            f = open(pic_out_url, "rb")
            imgData = f.read()
            f.close()
        except BaseException:
            if file_size < 2048 * 1024:
                imgData = request.content
            else:
                dict_cache[id] = 1
                f = open(dict_url, 'w')
                f.write(str(dict_cache))
                return

        base64_data = base64.b64encode(imgData)
        md = hashlib.md5()
        md.update(imgData)
        res1 = md.hexdigest()

        headers = {"Content-Type": "text/plain"}
        data = {
            "msgtype": "image",
            "image": {
                "base64": base64_data,
                "md5": res1
            }
        }
        global post_url
        requests.post(post_url, headers=headers, json=data)
        sourceStr = ""
        if u"source" in jsonPost:
            sourceStr = jsonPost[u"source"]
        data = {
            "msgtype": "text",
            "text": {
                "content": '{post_url}{id}\n角色:{character}\n作者:{artist}\n出处:{source}'.format(
                    post_url="https://danbooru.me/posts/", id=str(id), artist=jsonPost["tag_string_artist"],
                    character=jsonPost["tag_string_character"],
                    source=sourceStr
                )
            }
        }
        requests.post(post_url, headers=headers, json=data)
        dict_cache[id] = 1

        print("Download complete")
        sys.stdout.flush()

        f = open(dict_url, 'w')
        f.write(str(dict_cache))
        f.close()

    except requests.exceptions.RequestException as e:
        print(e)


# request json, get urls of pictures and download them
def grabber(query_str):
    global danbooru_url
    global dict_cache

    proxies = {'http': 'http://localhost:1080', 'https': 'http://localhost:1080'}
    r = requests.get(danbooru_url + '/post/index.xml?' + query_str, proxies=proxies)
    xml = parse(r.text, r.apparent_encoding)

    streams = xml["posts"]["post"]
    # check if all pages have been visited
    if len(streams) == 0:
        print("All pictures have been downloaded!")
        global status
        status = 'done'
    else:
        # check if directory already exists
        if not os.path.exists(danbooru_folder):
            os.mkdir(danbooru_folder)

        url = []
        for post in streams:
            if ('@file_url' in post) and ('@score' in post):
                extension = file_extension(post['@file_url'])
                if (post['@score'] >= 20) and (extension == ".jpg" or extension == ".png"):
                    url.append(post)

        # download
        for post in url:
            id = post["@id"]
            if not (id in dict_cache):
                download(id)
                global send_count
                send_count = send_count + 1
                if send_count >= 3:
                    global sleep_time
                    time.sleep(sleep_time)
                    send_count = 0
                else:
                    time.sleep(10)

            # urllib.urlretrieve(url, path)


def main():
    global queryStr
    global post_url
    global pic_in_url
    global pic_out_url
    global dict_url
    global dict_cache
    global sleep_time

    reload(sys)
    sys.setdefaultencoding('utf-8')

    queryStr = "tags=" + sys.argv[1] + "+-rating:safe" #sys.argv[1] + "+-rating:safe"  # "tags=azur_lane+-rating:safe+order:score&limit=1000"  # '
    post_url = sys.argv[2]
    sleep_time = int(sys.argv[3])

    timeStr = "_" + sys.argv[1].split("+", 1)[0]

    pic_in_url = "in" + timeStr + ".jpg"
    pic_out_url = "out" + timeStr + ".jpg"
    dict_url = "dict" + timeStr + ".txt"

    if not os.path.exists(dict_url):
        f = open(dict_url, 'w')
        f.write("{}")
        f.close()

    f = open(dict_url, 'r')
    dict_cache = eval(f.read())
    f.close()

    n = 1
    while n <= 1000 and status == 'not done yet':
        query = queryStr + "&page=" + str(n)
        print(query)
        sys.stdout.flush()
        grabber(query)
        n = n + 1

    print('Download successful!')


if __name__ == '__main__':
    main()
