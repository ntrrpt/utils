#!/usr/bin/env -S uv run --script

# /// script
# dependencies = [
#   "requests",
#   "bs4",
#   "loguru",
# ]
# ///


import requests, os, time, subprocess, sys, re, random, string, pathlib
from bs4 import BeautifulSoup
from pprint import pp
from loguru import logger as log
trace, info, err, succ = (log.trace, log.info, log.error, log.success)
delay = time.sleep

ARIA2_FILENAME = ''.join(random.choice(string.ascii_letters) for x in range(10)) + '.txt'

links = [
    'http://nendoroid01.web.fc2.com/2008-03/',
    'http://nendoroid01.web.fc2.com/2008-04/',
    'http://nendoroid02.web.fc2.com/2008-05/',
    'http://nendoroid02.web.fc2.com/2008-06/',
    'http://nendoroid03.web.fc2.com/2008-07/',
    'http://nendoroid03.web.fc2.com/2008-08/',
    'http://nendoroid03.web.fc2.com/2008-09/',
    'http://nendoroid04.web.fc2.com/2008-10/',
    'http://nendoroid04.web.fc2.com/2008-11/',
    'http://nendoroid05.web.fc2.com/2008-12/',
    'http://nendoroid05.web.fc2.com/2009-01/',
    'http://nendoroid06.web.fc2.com/2009-02/',
    'http://nendoroid06.web.fc2.com/2009-03/',
    'http://nendoroid07.web.fc2.com/2009-04/',
    'http://nendoroid07.web.fc2.com/2009-05/',
    'http://nendoroid08.web.fc2.com/2009-06/',
    'http://nendoroid08.web.fc2.com/2009-07/',
    'http://nendoroid09.web.fc2.com/2009-08/',
    'http://nendoroid09.web.fc2.com/2009-09/'
]

log.remove(0)
log.add(
        sys.stderr,
        format = "<level>[{time:DD-MMM-YYYY HH:mm:ss}]</level> {message}",
        backtrace = True, diagnose = True, colorize = True, level = 5
    )
log.add(
        'log.txt',
        format = "[{time:DD-MMM-YYYY HH:mm:ss}] {message}",
        backtrace = True, diagnose = True, colorize = True, level = 5
    )

def fileDel(filename):
    rem_file = pathlib.Path(filename)
    rem_file.unlink(missing_ok=True)

def add(dir, bin):
    with open(dir, 'a', encoding='utf-8') as file:
        file.write(bin + '\n')

def find_max_page(url):
    soup = BeautifulSoup(requests.get(url).text, "html.parser")

    all = soup.find_all("tr")
    for i in all:
        if 'Page' not in str(i):
            continue
            
        all_num = i.find_all("a")
        match = re.search(r'index(\d+)\.html', all_num[-1].get('href'))
 
        return int(match.group(1))

for link in links:
    trace(link)
    img_urls = []
    
    url = link + 'index.html'
    pages = [url]

    max_page = find_max_page(url)
    trace("pages => %s" % max_page)
    
    for i in range(2, max_page+1):
        pages.append(link + "index%s.html" % i)
    
    for page in pages:
        info(page)
        delay(2)
        soup = BeautifulSoup(requests.get(page).text, "html.parser")
        images = soup.find_all('img', class_='image')
        
        img_urls.append(page)
        for i in images:
            img_urls.append(link + i.get('alt') + '.jpg')
    
    # http://nendoroid01.web.fc2.com/2008-03/ => 2008-03
    dir_name = link.rstrip('/').split('/')[-1] 

    aria2c_args = [
        'aria2c',
        f'--input-file={ARIA2_FILENAME}',
        f'--dir={dir_name}',
        '--max-connection-per-server=1',
        '--max-concurrent-downloads=2',
        '--auto-file-renaming=false',
        '--remote-time=true',
        '--log-level=error',
        '--console-log-level=error',
        '--download-result=hide',
        '--summary-interval=0',
        '--file-allocation=none',
        '--continue=true',
        #'--all-proxy=http://127.0.0.1:10809'
    ]
    
    fileDel(ARIA2_FILENAME)
    for img in img_urls:
        add(ARIA2_FILENAME, img)
    
    subprocess.run(aria2c_args)
    print('', end='\n', flush=True)
    fileDel(ARIA2_FILENAME)
    