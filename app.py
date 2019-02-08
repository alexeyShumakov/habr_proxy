import requests
import re
from flask import Flask, Response
from flask import request as flask_req
from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag


HABR_HOST = 'https://habr.com'
LOCAL_HOST = 'http://localhost:5000'
SEARCH_PATTERN = re.compile(f'^{HABR_HOST}')
REPLACE_TAG_PROP_TUPLE = (
    ('a', 'href'),
    ('form', 'action'),
    ('use', 'xlink:href'),
    ('script', 'src')
)


app = Flask(__name__)


def replace_host(tag, prop):
    tag[prop] = tag[prop].replace(HABR_HOST, LOCAL_HOST)


def update_element(bs_instance, tag_name, prop):
    elements = bs_instance.find_all(tag_name, **{prop: SEARCH_PATTERN})
    [replace_host(element, prop) for element in elements]


def recursive_replace(tag):
    for child in tag.contents:
        if type(child) is NavigableString:
            fixed_text = re.sub(r'\b(\w{6})\b', '\g<1>\N{TRADE MARK SIGN}', child.string)
            child.replace_with(fixed_text)
        elif type(child) is Tag:
            if child.name != 'script':
                recursive_replace(child)


@app.errorhandler(404)
def root(_e):
    habr_url = flask_req.url.replace(LOCAL_HOST, HABR_HOST)
    resp = requests.get(habr_url)
    resp_content_type = resp.headers.get('content-type', '')
    if 'text/html' in resp_content_type:
        bs_instance = BeautifulSoup(resp.content, 'html.parser')

        recursive_replace(bs_instance)
        for tag_name, prop in REPLACE_TAG_PROP_TUPLE:
            update_element(bs_instance, tag_name, prop)

        return Response(str(bs_instance), resp.status_code, mimetype=resp_content_type)

    return Response(resp.content, resp.status_code, mimetype=resp_content_type)


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)