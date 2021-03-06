#!/usr/bin/python3

#python3 -m pip install requests, tabulate
import argparse
import requests
import sys
import glob
import concurrent
import concurrent.futures
from tqdm import tqdm
from itertools import repeat
import csv
from tabulate import tabulate
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Interface class to display terminal messages
class Interface():
    def __init__(self):
        self.red = '\033[91m'
        self.green = '\033[92m'
        self.white = '\033[37m'
        self.yellow = '\033[93m'
        self.bold = '\033[1m'
        self.end = '\033[0m'

    def header(self):
        print(f"\n {self.bold}*************** Source Code Mapping ***************{self.end}")
        print(f"@initroot \n")

    def info(self, message):
        print(f"[{self.white}*{self.end}] {message}")

    def warning(self, message):
        print(f"[{self.yellow}!{self.end}] {message}")

    def error(self, message):
        print(f"[{self.red}x{self.end}] {message}")

    def success(self, message):
        print(f"[{self.green}✓{self.end}] {self.bold}{message}{self.end}")


def sendGet(url, debug):
    #debug = False;
    try:
        if debug is True:
            proxies = {'http': 'http://127.0.0.1:8080', 'https': 'http://127.0.0.1:8080'}
            r = requests.get(url, proxies = proxies,verify=False)
            pot = analyseVuln(r)
            output.info([r.url, r.status_code,len(r.content),pot])
        else:
            r = requests.get(url,verify=False)
            pot = analyseVuln(r)
    except requests.exceptions.ProxyError:                 
        r = requests.get(url,verify=False)
        pot = analyseVuln(r)
        output.info([r.url, r.status_code,len(r.content),pot])
        return [r.url, r.status_code,len(r.content),pot]

    return [r.url, r.status_code,len(r.content),pot]


def analyseVuln(rqResponse):
    if "<form action" in str(rqResponse.content):
        return "InputForm"
    elif "<form name" in str(rqResponse.content):
        return "InputForm"
    elif 'type="submit"' in str(rqResponse.content):
        return "SubmitForm"
    else:
        return ""


def remDuplicates(x):
  return list(dict.fromkeys(x))

def main():
    # Parse Argumentsxs
    parser = argparse.ArgumentParser()
    parser.add_argument('-w', '--dir',	 help='Root directory holding the source code', required=True)
    parser.add_argument('-t', '--target', help='Target web application URL e.g. http://localhost', required=True)
    parser.add_argument('-d', '--debug', help='Instruct our web requests to use our defined proxy', action='store_true', required=False)
    parser.add_argument('--wordlist', help='Only creates the wordlist based on source files',action='store_true')
    parser.add_argument('-o', '--output', help='Write results to output file', required=False)
    args = parser.parse_args()

    # Instantiate our interface class
    global output
    output = Interface()

    # Banner
    output.header()

    # Debugging
    if args.debug:
        for k,v in sorted(vars(args).items()):
            if k == 'debug':
                output.warning(f"Debugging Mode: {v}")
            else:
                output.info(f"{k}: {v}")

    #Let's get a list of all files in the dir
    exts = ['*.txt', '*.json', '*.xml', '*.config', '*.svc','*.asmx', '*.sql', '*.conf', '*.zip', '*.php', '*.ini', '*.cs', '*.js', '*.aspx', '*.asp', '*.java', '*.dll', '*.dat', '*.ascx', '*.html']
    files = [f for ext in exts 
         for f in glob.glob(args.dir + '/**/' + ext, recursive=True)]
    output.info('List of files generated with success!')
    #Lets convert it to our target
    potUrls = [file.replace(args.dir,args.target) for file in files]
    potUrls = [url.replace('\\','/') for url in potUrls]
       
    #Let's now check access
    if args.wordlist:
        print(*potUrls, sep="\n")
        output.success('Done!')
    else:
        output.info('Now checking each file against ' + str(len(potUrls)) + ' targets, please wait:\n')
        with concurrent.futures.ThreadPoolExecutor(10) as executor:
            #accessible = executor.map(sendGet, potUrls, repeat(args.debug))
            accessible = list(tqdm(executor.map(sendGet, potUrls, repeat(args.debug)), total=len(potUrls)))        
            output.info(tabulate(accessible))
            if args.output:
                output_file = args.output             
                with open(output_file, 'w') as file:
                    write = csv.writer(file) 
                    write.writerows(accessible)
        output.success('Done!') 
    
if __name__ == '__main__':
    main()
