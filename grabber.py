#!/usr/bin/python
# coding:utf-8
import json
import os  # path manipulation
import urllib as urllib

import requests
from xmltodict import parse

status = 'not done yet'
danbooru_folder = os.getcwd() + '/Pictures/'


def file_extension(path):
    return os.path.splitext(path)[1]


def download(url, path):
    try:
        request = requests.get(url, timeout=30)

        with open(path, "wb") as f:
            f.write(request.content)
    except requests.exceptions.RequestException as e:
        print(e)


# request json, get urls of pictures and download them
def grabber(query_str):
    r = requests.get('https://danbooru.me/post/index.xml?' + query_str)
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
            extension = file_extension(post['@file_url'])
            fileName = str(post['@id']) + extension

            url = "https://danbooru.me/data/" + post['@file_url'].split('/')[-1]
            path = danbooru_folder + '/' + fileName
            print("Download file:" + url)
            download(url, path)
            #urllib.urlretrieve(url, path)


def main():
    queryStr = "tags=azur_lane+-rating:safe+order:score&limit=1000"  # 'sys.argv[1]

    n = 1
    while n <= 1000 and status == 'not done yet':
        query = queryStr + "&page=" + str(n)
        print(query)
        grabber(query)
        n = n + 1

    print('Download successful!')


if __name__ == '__main__':
    main()
