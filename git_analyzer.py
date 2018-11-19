import sys
import urllib.request as rq
import concurrent.futures
from urllib import parse
import json
from datetime import datetime
import re
import itertools
import functools

api_endpoint = 'https://api.github.com/'

def parse_params(args):
    """Parse params and return request url
    """
    # parsing args
    params = '?per_page=100'
    if len(args) > 1:
        params += f'&since={datetime.strptime(args[1], "%d-%m-%Y").isoformat()}'
    if len(args) > 2:
        params += f'&until={datetime.strptime(args[2], "%d-%m-%Y").isoformat()}'
    if len(args) > 3:
        params += f'&sha={args[3]}'

    repo = parse.urlparse(args[0]).path
    return f'{api_endpoint}repos{repo}/commits{params}'

def get_next_link(header):
    try:
        for val in re.split(",", header):
            if not 'rel="next"' in val:
                continue
            url, rel = val.split(";")
            return url.strip("<> ")
    except:
        pass
    return None

def get_pages_count(header):
    """Return pages count from github rest response header

    Args:
        header (str): Header string from HTTP response

    Returns:
        int: number of pages.
    """
    try:
        for val in re.split(",", header):
            if not 'rel="last"' in val:
                continue
            url, rel = val.split(";")
            return int(re.search('&page=(\d+)', url).group(1)) or 0
    except:
        pass
    return 0

def load_url_json(url, page = 1, timeout = 30):
    with rq.urlopen(url+f'&page={page}', timeout=timeout) as resp:
        return json.loads(resp.read())
    
def load_commits():
    request_url = parse_params(args)
    print(f'Getting {request_url}...')
    commits = []
    # an initial request
    try:
        resp = rq.urlopen(request_url)
        commits += json.loads(resp.read())
    except Exception as err:
        print(f'An error occured: {err}')
        exit(1)
    # determine count of pages
    pages_count = get_pages_count(resp.getheader('Link'))
    with concurrent.futures.ThreadPoolExecutor(max_workers = 5) as executor:
        partial = functools.partial(load_url_json, request_url)
        res_map = executor.map(partial, list(range(2, pages_count+1)))
        commits += itertools.chain.from_iterable(res_map)

def main(args):
    request_url = parse_params(args)
    print(f'Getting {request_url}...')
    commits = []
    # an initial request
    try:
        resp = rq.urlopen(request_url)
        commits += json.loads(resp.read())
    except Exception as err:
        print(f'An error occured: {err}')
        exit(1)
    # determine count of pages
    pages_count = get_pages_count(resp.getheader('Link'))
    with concurrent.futures.ThreadPoolExecutor(max_workers = 5) as executor:
        partial = functools.partial(load_url_json, request_url)
        res_map = executor.map(partial, list(range(2, pages_count+1)))
        commits += itertools.chain.from_iterable(res_map)
    print(f'{pages_count} pages total')
    print(f'got {len(commits)} commits')

    

usage = ''
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f'Not enought arguments. Usage: {usage}')
        exit(1)
    main(sys.argv[1:])   