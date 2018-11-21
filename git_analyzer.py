import sys
import urllib.request as rq
import concurrent.futures
from urllib import parse
import json
from datetime import datetime, timedelta, date
import re
import itertools
import functools
import argparse
import collections
import os
from base64 import b64encode

api_endpoint = 'https://api.github.com/'

headers = {}
if 'githubUsername' in os.environ:  
    user = os.environ['githubUsername']
    if 'githubToken' in os.environ:
        token = os.environ['githubToken']
        user_pass = b64encode(str.encode("%s:%s" % (user, token))).decode("ascii")
        headers = {'Authorization' : f'Basic {user_pass}'}

def process_args(args):
    global headers
    if args['since']:
        args['since'] = datetime.strptime(args['since'], "%d-%m-%Y")
    if args['until']:
        args['until'] = datetime.strptime(args['until'], "%d-%m-%Y")
    args['repo'] = parse.urlparse(args['repo']).path
    if args['user'] and args['token']:
        user_pass = b64encode(str.encode("%s:%s" % (args['user'], args['token']))).decode("ascii")
        headers = {'Authorization' : f'Basic {user_pass}'}
def get_commits_url(**args):
    """Parse params and return request url
    """
    # parsing args
    params = '?per_page=100'
    if args['since']:
        params += f'&since={args["since"].isoformat()}'
    if args['until']:
        params += f'&until={args["until"].isoformat()}'
    if args['branch']:
        params += f'&sha={args["branch"]}'
    return f'{api_endpoint}repos{args["repo"]}/commits{params}'

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
            url, v = val.split(";")
            return int(re.search(r'&page=(\d+)', url).group(1)) or 0
    except:
        pass
    return 0

def load_url_json(url, page = 1, timeout = 30):
    request = rq.Request(url+f'&page={page}', headers = headers)
    with rq.urlopen(request, timeout=timeout) as resp:
        return json.loads(resp.read())
    
def load_commits(**args):
    request_url = get_commits_url(**args)
    commits = []
    # an initial request
    try:
        request = rq.Request(request_url, headers = headers)
        resp = rq.urlopen(request)
        commits += json.loads(resp.read())
    except Exception as err:
        print(f'An error occured: {err}')
        exit(1)
    # determine count of pages
    pages_count = get_pages_count(resp.getheader('Link'))
    with concurrent.futures.ThreadPoolExecutor(max_workers = 5) as executor:
        partial = functools.partial(load_url_json, request_url, auth=True)
        res_map = executor.map(partial, list(range(2, pages_count+1)))
        commits += itertools.chain.from_iterable(res_map)
    return commits

def get_commits_count(**args):
    raw_commits = load_commits(**args)
    commits_email = [commit['commit']['author']['email']
        for commit in raw_commits]
    email_to_name = {
        commit['commit']['author']['email']: commit['commit']['author']['name']
        for commit in raw_commits}
    commiter_freq = collections.Counter(commits_email).most_common(30)
    return [(email_to_name[c[0]], c[1]) for c in commiter_freq]

def get_search_url(**args):
    # 1: is because we don't need leading '/'
    q = f'?q=type:{args["search"]}+repo:{args["repo"][1:]}'
    if args['since'] and args['until']:
        q += f'+created:{args["since"].isoformat()}..{args["until"].isoformat()}'
    elif args['since']:
        q += f'+created:>={args["since"].isoformat()}'
    elif args['until']:
        q += f'+created:<={args["until"].isoformat()}'
    if args['branch'] and args['search'] == 'pr':
        q += f'+base:{args["branch"]}'
    return f'{api_endpoint}search/issues{q}'

def get_pulls_count(**args):
    request_url = get_search_url(**args, search='pr')
    with concurrent.futures.ThreadPoolExecutor(max_workers = 2) as executor:
        res_map = list(executor.map(load_url_json,
            [request_url+'+state:open', request_url+'+state:closed']))
        opened = res_map[0]['total_count']
        closed = res_map[1]['total_count']
    return(opened, closed)

def get_old_pulls_count(**args):
    request_url = get_search_url(repo=args['repo'], branch = args['branch'],
        until = date.today()-timedelta(days=30), since = args['since'], search='pr')
    return load_url_json(request_url+'+state:open')['total_count']

def get_issues_count(**args):
    request_url = get_search_url(**args, search='issue')
    with concurrent.futures.ThreadPoolExecutor(max_workers = 2) as executor:
        res_map = list(executor.map(load_url_json,
            [request_url+'+state:open', request_url+'+state:closed']))
        opened = res_map[0]['total_count']
        closed = res_map[1]['total_count']
    return(opened, closed)

def get_old_issues(**args):
    request_url = get_search_url(repo=args['repo'], branch = None,
        until = date.today()-timedelta(days=14), since = args['since'], search='issue')
    return load_url_json(request_url+'+state:open')['total_count']


descr = """Get some statistics about github repository.
Note: if you recive 403 forbidden, unauthorized requests limit to github api
exceeded. You may authorize yourself be passing --user and --token arguments
or by setting githubUsername and githubToken envs
"""
def main(args):
    # params = parse_params(args)
    # raw_commits = load_commits(**params)
    parser = argparse.ArgumentParser(prog='git_analyzer',
        description=descr)
    parser.add_argument('repo')
    parser.add_argument('--since', required=False, help='Date in format dd-mm-yyyy')
    parser.add_argument('--until', required=False, help='Date in format dd-mm-yyyy')
    parser.add_argument('--branch', required=False, default = 'master')
    parser.add_argument('--user', required=False, help='Github user name')
    parser.add_argument('--token', required=False, help='Github token or password')
    args = vars(parser.parse_args())
    process_args(args)

    print(f'\nSummary\nRepo: {args["repo"]}\nBranch: {args["branch"]}')
    if args['since']:
        print(f'Since {args["since"].strftime("%d-%m-%Y")}')
    if args['until']:
        print(f'Until {args["until"].strftime("%d-%m-%Y")}')
    commits_counts = get_commits_count(**args)
    print(f'\nTop commiters:\n{"Name":30}{"Commits made":30}')
    for c in commits_counts:
        print(f'{c[0]:30}{c[1]:<30}')
    pulls_count = get_pulls_count(**args)
    print(f'\n{"Open pull requests:":30}{pulls_count[0]:<30}')
    print(f'{"Closed pull requests:":30}{pulls_count[1]:<30}')
    old_pulls = get_old_pulls_count(**args)
    print(f'{"Old pull requests:":30}{old_pulls:<30}')
    issues_count = get_issues_count(**args)
    print(f'\n{"Open issues:":30}{issues_count[0]:<30}')
    print(f'{"Closed issues:":30}{pulls_count[1]:<30}')
    old_issues = get_old_issues(**args)
    print(f'{"Old issues:":30}{old_issues:<30}')

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f'Not enought arguments. Usage:')
        exit(1)
    main(sys.argv[1:])