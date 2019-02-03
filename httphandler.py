import httplib
from random import choice


class HttpHadler:
    # http request handler, by initiation it construct urllib2.Request object that can be passed further.
    # kwargs - for usage of more options of urllib2.Request
    # url - the url to check
    # version - http version, by default is 1.1
    # ua - User-Agent that will be added to the headers. a dict.
    user_agents = {
        'chrome': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
        'firefox': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:64.0) Gecko/20100101 Firefox/64.0',
        'ie': 'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko'
    }

    def __init__(self, url, version='1.1', **kwargs):
        self.version = version
        self.url = url
        if '1.0' not in self.version:
            print(' >> using http version ' + self.version)
            self.client = httplib.HTTPConnection(url, timeout=5, **kwargs)
        else:
            httplib.HTTPConnection._http_vsn = 10
            httplib.HTTPConnection._http_vsn_str = 'HTTP/1.0'
            self.client = httplib.HTTPConnection(url, timeout=5, **kwargs)

    def execute(self, path="/", data=None, headers={}):
        # if data=None 'get' request will be sent, if data="" post request will be sent
        # path - the path of the http directory
        # headers to use in request, will be generated if none
        if headers:
            self.headers = headers
        else:
            self.headers = self.headers_generator()
        try:
            if data:
                self.client.request("POST", path, data, headers=self.headers)
                return self.client.getresponse()
            else:
                self.client.request("GET", path, headers=self.headers)
                return self.client.getresponse()
        except httplib.error as e:
            raise e

    def user_agent_gen(self, browser=''):
        # generates a default user-agent for the headers, by default random UA will be used.
        # browser - when specified, UA if this browser wil be returned
        return self.user_agents.setdefault(browser, choice(self.user_agents.values()))


    def headers_generator(self, **kwargs):
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'en-US,en;q=0.5',
            'Cache - Control': 'max - age = 0',
            'Connection': 'keep-alive',
            'User-Agent': self.user_agent_gen(**kwargs),
        }
        print('\n >> Using UA : ' + headers['User-Agent'])
        return headers
