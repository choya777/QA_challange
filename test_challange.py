import pytest

from docker import DockerHandler
from httphandler import HttpHadler

# external IP / hostname of the remoite machine
url = '127.0.0.1'
# the name of the image that will be pulled from docker hub
image = 'nginx'
# username for ssh
user = 'qa'
# password for ssh
password = 'Challenge'
# ssh private ke location, mandatory for login to GCE machine
ssh_key = 'C:\google_ubuntu.ppk'


def check_response_code(response, expected_stauts, data=None):
    # test utility to compare between response code and expected code and data to baseline
    # response - httplib response object
    # expected result - int , the response status code number
    # data - baseline of the expected body in response.
    body = response.read()
    assert response.status == expected_stauts
    print('\n << response status ' + format(response.status) + ' is as expected: ' + format(expected_stauts))
    assert response.reason is not None
    if data:
        assert data == body
    else:
        return True


@pytest.fixture()
def http_connection():
    # will be used by all test as precondition
    # http connection initiator
    return HttpHadler(url)


@pytest.fixture()
def ssh_connection():
    return DockerHandler(url, user, password, ssh_key=None)


@pytest.fixture()
def e2e():
    docker = DockerHandler(url, user, password, ssh_key)
    # stop running docker if exists
    docker.stop(image)
    # removes image if exists.
    docker.remove_image(image)
    return docker


def test_docker(ssh_connection):
    assert ssh_connection.is_exists(image)
    assert ssh_connection.is_running(image)


def test_stop_docker(ssh_connection):
    print('\n stopping ' + image + ' at the  first time')
    assert ssh_connection.stop(image)
    print('\n trying to stop already stopped machine')
    assert ssh_connection.stop(image) == False


def test_start_docker(ssh_connection):
    print('\n starting ' + image + ' at the  first time')
    assert ssh_connection.run_docker(port='80:80', image=image)
    print('\n trying to start again should failed')
    # this is due to docker bug. see: https://github.com/docker/swarm/issues/2835
    assert ssh_connection.run_docker(port='80:80', image=image) == False


def test_docker_run(ssh_connection):
    assert ssh_connection.run_docker(port='80:80', image=image)


def test_get(http_connection):
    print('\n1. Simple GET request.')
    res = http_connection.execute()
    print()
    assert check_response_code(res, 200) == True
    res = http_connection.execute(path="/doesnt exists")
    assert check_response_code(res, 404) == True


def test_post(http_connection):
    # this test will fail (response 405 from server) as the ngnix server doesn't know how to handle POST request.
    # there is a workaround - TODO : http://invalidlogic.com/2011/04/12/serving-static-content-via-post-from-nginx/
    print('\n2. Simple POST request.')
    res = http_connection.execute(data='Hello World')
    assert check_response_code(res, 405) == True


def test_browsers(http_connection):
    print('3. Different browser compatibility ')
    for k in iter(http_connection.user_agents.keys()):
        print('\n using User-Agent of ' + k)
        header = http_connection.headers_generator(browser=k)
        res = http_connection.execute(headers=header)
        assert check_response_code(res, 200) == True
        res = http_connection.execute(path="/doesnt exists")
        assert check_response_code(res, 404) == True


def test_get_v1():
    print('Send an HTTP GET request using HTTP version 1.0')
    req = HttpHadler(url, version='1.0')
    res = req.execute()
    assert check_response_code(res, 200) == True
    res = req.execute(path="/doesnt exists")
    assert check_response_code(res, 404) == True


def test_post_v1():
    print('Send an HTTP POST request using HTTP version 1.0')
    req = HttpHadler(url, version='1.0')
    res = req.execute(data='Hello World')
    assert check_response_code(res, 405) == True


def test_e2e(e2e):
    try:
        print('### Testing E2E ###')
        print('\n 1. pulling nginx from docker hub')
        assert e2e.pull(image)
        assert e2e.is_exists(image), image + " doesnt' exists \n"
        print('\n 2. starting docker ')
        assert e2e.run_docker(port='80:80', image=image)
        print('running few http tests \n')
        test_get_v1()
        assert test_browsers(http_connection())
        print('\n 3. stopping docker ')
        assert e2e[0].stop(image)
        print('\n verify that docker is down ')
        assert e2e[0].is_running('ngninx')
    except AssertionError as e:
        e2e.stop(image)
        raise e
