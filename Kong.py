# coding:utf-8
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Kong:
    def __init__(self, restful_url, proxy_url):
        self.restful_url = restful_url + '/' if restful_url[-1] != '/' else restful_url
        self.proxy_url = proxy_url[:-1] if proxy_url[-1] == '/' else proxy_url
        self.proxy = {'http': '127.0.0.1:8080', 'https': '127.0.0.1:8080'}  # 方便在burp中快速查看请求与测试
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.94 Safari/537.36"}
        self.timeout = 15

    def re_replace(self, path):
        path = path.replace('$', '')
        path = path.replace('\S+', 'test')
        return path

    def check(self):
        try:
            res = requests.head(url=self.restful_url, verify=False, headers=self.headers, timeout=self.timeout, allow_redirects=False, proxies=self.proxy)
            if 'X-Kong-Admin-Latency' not in res.headers.keys():
                print(f'[-]restful_url貌似不是正确url: {self.restful_url}')
                return False
        except:
            print(f'[-]restful_url请求失败: {self.restful_url}')
            return False
        try:
            res = requests.head(url=self.proxy_url, verify=False, headers=self.headers, timeout=self.timeout, allow_redirects=False, proxies=self.proxy)
            if 'X-Kong-Response-Latency' not in res.headers.keys():
                print(f'[-]proxy_url貌似不是正确url: {self.proxy_url}')
                return False
        except:
            print(f'[-]proxy_url请求失败: {self.proxy_url}')
            return False
        return True

    def endpoints(self):
        endpoint_list = []
        try:
            res = requests.get(url=self.restful_url + 'routes', verify=False, headers=self.headers, timeout=self.timeout, allow_redirects=False, proxies=self.proxy)
            data_list = res.json()['data']
            for endpoint in data_list:
                protocols = endpoint.get('protocols', [])  # 协议
                if 'http' in protocols or 'https' in protocols:
                    name = endpoint.get('name', '无')  # 端点名称
                    methods = endpoint.get('methods', 'GET')  # 默认为GET
                    hosts = endpoint.get('hosts', [])  # 默认任意host
                    paths = endpoint.get('paths', ['/'])  # 默认为 '/'
                    print(f"name: {name}, protocols: {protocols}, Methods: {methods}, Hosts: {hosts}, Paths: {paths}")
                    endpoint_list.append({'protocols': protocols, 'methods': methods, 'hosts': hosts, 'paths': paths})
            print(f'[*]收集到端点{len(endpoint_list)}条')
        except:
            print(f'[-]Admin Restful API 请求错误')

        return endpoint_list

    def req(self, endpoint_list):
        if endpoint_list:
            print(f'[*]开始自动请求端点路由')
            r = requests.session()
            headers = self.headers.copy()
            # 遍历端点
            for endpoint in endpoint_list:
                if endpoint['hosts']:
                    headers['Host'] = endpoint['hosts'][0]
                if endpoint['methods'] is None:  # 没有指明请求类型的默认get/post
                    endpoint['methods'] = ['GET', 'POST']
                # 遍历请求方式
                for methods in endpoint['methods']:
                    if methods == 'POST':
                        for path in endpoint['paths']:
                            path = self.re_replace(path)
                            try:
                                res = r.post(url=f'{self.proxy_url}{path}', verify=False, headers=headers, timeout=self.timeout, allow_redirects=False, proxies=self.proxy)
                                print(f"[*]{endpoint['methods'][0]:<6}|{res.status_code:<3}|{self.proxy_url}{path}")
                            except:
                                print(f"[-]请求错误|{endpoint['methods'][0]:<6}|{self.proxy_url}{path}")
                    elif methods == 'PUT':
                        for path in endpoint['paths']:
                            path = self.re_replace(path)
                            try:
                                res = r.put(url=f'{self.proxy_url}{path}', verify=False, headers=headers, timeout=self.timeout, allow_redirects=False, proxies=self.proxy)
                                print(f"[*]{endpoint['methods'][0]:<6}|{res.status_code:<3}|{self.proxy_url}{path}")
                            except:
                                print(f"[-]请求错误|{endpoint['methods'][0]:<6}|{self.proxy_url}{path}")
                    elif methods == 'DELETE':
                        for path in endpoint['paths']:
                            path = self.re_replace(path)
                            try:
                                res = r.delete(url=f'{self.proxy_url}{path}', verify=False, headers=headers, timeout=self.timeout, allow_redirects=False, proxies=self.proxy)
                                print(f"[*]{endpoint['methods'][0]:<6}|{res.status_code:<3}|{self.proxy_url}{path}")
                            except:
                                print(f"[-]请求错误|{endpoint['methods'][0]:<6}|{self.proxy_url}{path}")
                    else:
                        for path in endpoint['paths']:
                            path = self.re_replace(path)
                            try:
                                res = r.get(url=f'{self.proxy_url}{path}', verify=False, headers=headers, timeout=self.timeout, allow_redirects=False, proxies=self.proxy)
                                print(f"[*]{endpoint['methods'][0]:<6}|{res.status_code:<3}|{self.proxy_url}{path}")
                            except:
                                print(f"[-]请求错误|{endpoint['methods'][0]:<6}|{self.proxy_url}{path}")

    def run(self):
        if self.check():
            endpoint_list = self.endpoints()
            self.req(endpoint_list)


if __name__ == '__main__':
    # 分别为Admin Restful API url、Proxy url
    k = Kong('http://xxx/', 'http://xxx/')
    k.run()
