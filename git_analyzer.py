import sys
import urllib.request as rq
from urllib.error import URLError, HTTPError
from urllib import parse
import json
from datetime import datetime

api_endpoint = 'https://api.github.com/'

def main(args):
    # parsing args
    params = '?per_page=100'
    if len(args) > 1:
        params += f'&since={datetime.strptime(args[1], "%d-%m-%Y")}'
    if len(args) > 2:
        params += f'&until={datetime.strptime(args[2], "%d-%m-%Y")}'
    if len(args) > 3:
        params += f'&sha={args[3]}'
    repo = parse.urlparse(args[0]).path
    request_url = f'{api_endpoint}repos{repo}/commits{params}'
    print(f'Getting {request_url}...')
    try:
        resp = rq.urlopen(request_url)
        print(resp.info()['Link'])
    except HTTPError as e:
        print('The server couldn\'t fulfill the request.')
        print('Error code: ', e.code)
    except URLError as e:
        print('We failed to reach a server.')
        print('Reason: ', e.reason) 
    commits = json.loads(resp.read())
    # print(commits)

usage = ''
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f'Not enought arguments. Usage: {usage}')
        exit(1)
    main(sys.argv[1:])   