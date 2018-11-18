import sys
import urllib.request as rq
from urllib.error import URLError, HTTPError
from urllib import parse
import json
from datetime import datetime
import re

api_endpoint = 'https://api.github.com/'

def parse_params(args):
    """Parse params and return request url
    """
    # parsing args
    params = '?per_page=100'
    if len(args) > 1:
        params += f'&since={datetime.strptime(args[1], "%d-%m-%Y")}'
    if len(args) > 2:
        params += f'&until={datetime.strptime(args[2], "%d-%m-%Y")}'
    if len(args) > 3:
        params += f'&sha={args[3]}'

    repo = parse.urlparse(args[0]).path
    return f'{api_endpoint}repos{repo}/commits{params}'

def get_next_link(header):
    for val in re.split(",", header):
        if not 'rel="next"' in val:
            continue
        url, rel = val.split(";")
        return url.strip("<> ")
    return None

def main(args):
    request_url = parse_params(args)
    print(f'Getting {request_url}...')
    commits = []
    while request_url:
        try:
            resp = rq.urlopen(request_url)
            print(resp.info()['Link'])
        except HTTPError as e:
            print('The server couldn\'t fulfill the request.')
            print('Error code: ', e.code)
        except URLError as e:
            print('We failed to reach a server.')
            print('Reason: ', e.reason) 
        commits += json.loads(resp.read())
        request_url = get_next_link(resp.getheader('Link'))
    

usage = ''
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f'Not enought arguments. Usage: {usage}')
        exit(1)
    main(sys.argv[1:])   