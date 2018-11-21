## Git analyzer

usage: git_analyzer [-h] [--since SINCE] [--until UNTIL] [--branch BRANCH]  
                    [--user USER] [--token TOKEN]  
                    repo  

Get some statistics about github repository. Note: if you recive 403
forbidden, unauthorized requests limit to github api exceeded. You may
authorize yourself be passing --user and --token arguments or by setting
githubUsername and githubToken envs

positional arguments:  
  repo

optional arguments:
  -h, --help       show this help message and exit  
  --since SINCE    Date in format dd-mm-yyyy  
  --until UNTIL    Date in format dd-mm-yyyy  
  --branch BRANCH  Github repo url  
  --user USER      Github user name  
  --token TOKEN    Github token or password  