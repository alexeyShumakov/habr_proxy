from unittest import mock
from app import app, PORT, replace_links, recursive_replace_text
from bs4 import BeautifulSoup

def setup():
    app.config['TESTING'] = True
    app.config['SERVER_NAME'] = f'localhost:{PORT}'

def generate_fake_response(content, content_type, status_code):
    fake_response = mock.Mock()
    fake_response.content = content
    fake_response.headers = {'content-type': content_type}
    fake_response.status_code = status_code
    return fake_response


@mock.patch('requests.get')
def test_default_behaviour(fake_get):
    fake_get.return_value = generate_fake_response('fake content', 'raw/text', 200)
    client = app.test_client()

    response = client.get('/')

    assert response.data == b'fake content'
    assert response.status_code == 200


@mock.patch('requests.get')
def test_requset_url(fake_get):
    fake_get.return_value = generate_fake_response('fake content', 'text/xml', 200)
    client = app.test_client()

    client.get('/path/to/file.xml')

    fake_get.assert_called_with('https://habr.com/path/to/file.xml')


@mock.patch('requests.get')
@mock.patch('app.recursive_replace_text')
@mock.patch('app.replace_links')
def test_function_calls(fake_replace_links, fake_replace_text, fake_get):
    fake_get.return_value = generate_fake_response(
        '<html><body><b>fake content</b></body></html>', 'text/html', 200)
    client = app.test_client()

    response = client.get('/')

    fake_replace_links.calls_count(3)
    fake_replace_text.calls_count(1)
    assert response.data == b'<html><body><b>fake content</b></body></html>'


def test_replace_links():
    html_str = '<a href="https://habr.com/path/to/post">hi!</a>'
    bs = BeautifulSoup(html_str, 'html.parser')
    replace_links(bs, 'a', 'href')
    assert str(bs) == '<a href="http://localhost:5000/path/to/post">hi!</a>'


def test_not_replace_links():
    html_str = '<b href="https://habr.com/path/to/post">hi!</b>'
    bs = BeautifulSoup(html_str, 'html.parser')
    replace_links(bs, 'a', 'href')
    assert str(bs) == html_str

    html_str = '<a href="https://habr1.com/path/to/post">hi!</a>'
    bs = BeautifulSoup(html_str, 'html.parser')
    replace_links(bs, 'a', 'href')
    assert str(bs) == html_str


def test_replace_text():
    html_str = '<div>foobar <div><b>foobar</b></div> foobar <script>foobar</script></div>'
    expected_str = '<div>foobar™ <div><b>foobar™</b></div> foobar™ <script>foobar</script></div>'
    bs = BeautifulSoup(html_str, 'html.parser')
    recursive_replace_text(bs)
    assert str(bs) == expected_str