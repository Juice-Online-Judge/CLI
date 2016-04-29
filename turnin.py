#!/usr/bin/env python
#-*- coding: utf-8 -*-

import ConfigParser
import argparse
import sys
import os
import requests
import time

cfgfile = {
    'global': '/etc/turnin.rc',
    'home': os.path.expanduser('~/.turnin.rc'),
    'working': './.turnin.rc'
}
langs = {
    '.c': 'c',
    '.cpp': 'c++',
    '.java': 'java',
    '.py': 'python'
}

def red(s): return ("\033[1;31m%s\033[m" % s)
def green(s): return ("\033[1;32m%s\033[m" % s)
def yellow(s): return ("\033[1;33m%s\033[m" % s)
def blue(s): return ("\033[1;34m%s\033[m" % s)
def magenta(s): return ("\033[1;35m%s\033[m" % s)
def cyan(s): return ("\033[1;36m%s\033[m" % s)
def white(s): return ("\033[1;37m%s\033[m" % s)
def autocolor(s):
    if s in ('AC', ): return green(s)
    elif s in ('WA', 'SE', 'CE', 'RE', 'TLE', 'MLE', 'OLE', 'RF', 'NE'): return red(s)
    else: return s

def wrtok(args):
    cfg = open(cfgfile['home'], 'w+')
    Config = ConfigParser.ConfigParser()
    Config.read(cfg)
    if not Config.has_section('defaults'):
        Config.add_section('defaults')
    Config.set('defaults', 'token', args['token'])
    Config.write(cfg)
    cfg.close()

def turnin(args):
    if not os.path.isfile(args['code']):
        print(red('Error: Not a regular file: %s' % (args['code'])))
        return
    if args['token'] is None:
        args['token'] = raw_input(green("Enter your token: "))
    if args['uuid'] is None:
        args['uuid'] = raw_input(green("Enter question's UUID: "))
    for lang in langs:
        if args['code'].endswith(lang):
            args['lang'] = langs[lang]
    if args['lang'] is None:
        args['lang'] = raw_input(green("Enter your Language(ex: C): ").lower())

    url_submit = args['url-submit'].format(**args)
    #print url_submit
    data = {'language': args['lang']}
    files = {'code': open(args['code'])}
    headers = {'X-Requested-With': 'XMLHttpRequest'}
    response = requests.post(url_submit, data = data, files = files, headers = headers, timeout = 5)

    if response.status_code == 201:
        print(green("Success submitted"))
        data = response.json()
        args['id'] = data['id']
        wrtok(args)
    elif response.status_code == 401:
        print(red("Error: Token Mismatch"))
        args['token'] = None
        turnin(args)
    elif response.status_code == 403:
        print(red("Error: Test Not Start or Test End"))
    elif response.status_code in (404, 405):
        print(red("Error: Question Not Found"))
    elif response.status_code == 422:
        print(red("Error: Language Not Support or File Error"))
        #print(response.text)
    elif response.status_code in (500, 520):
        print(red("Error: Server Error"))
    else:
        print(red("Unknown Error(%d)! Please contact TA" % response.status_code))
        print(response.text)
    print("")

def turnincheck(args):
    url_view = args['url-view'].format(**args)
    headers = {'X-Requested-With': 'XMLHttpRequest'}
    for t in (1, 2, 2):
        time.sleep(t)
        response = requests.get(url_view, headers = headers, timeout = 5)
        if response.status_code != 200:
            print(red("Error: %d" % response.status_code))
            return
        data = response.json()
        judge = data['judge']
        question = data['question']
        if data['judge'] is not None:
            print "%s %s: %s" % (cyan(data['id']), yellow(question['title']), autocolor(judge['result']))
            print "\t%s %s %s %s" % (green("time:"), white(judge['time']), green("memory:"), white(judge['memory']))
            print "\t%s %s" % (green("message:"), white(judge['judge_message']))
            print("")
            return
    print "%s %s: Not Judge" % (cyan(data['id']), yellow(question['title']))
    print("")
    
def recent(args):
    if args['token'] is None:
        args['token'] = raw_input(green("Enter your token: "))
    url_recent = args['url-recent'].format(**args)
    data = {'page': args['page']}
    headers = {'X-Requested-With': 'XMLHttpRequest'}
    response = requests.get(url_recent, params=data, headers = headers, timeout = 5)
    if response.status_code == 200:
        wrtok(args)
        pass
    elif response.status_code in (400, 401):
        print(red("Error(%d): Token Mismatch" % (response.status_code)))
        args['token'] = None
        recent(args)
        return
    else:
        print(red("Error: %d" % response.status_code))
        return
    res = response.json()
    for data in res['data']:
        judge = data['judge']
        question = data['question']
        if data['judge'] is not None:
            print "%s %s: %s" % (cyan(data['id']), yellow(question['title']), autocolor(judge['result']))
            print "\t%s %s %s %s" % (green("time:"), white(judge['time']), green("memory:"), white(judge['memory']))
            print "\t%s %s" % (green("message:"), white(judge['judge_message']))
        else:
            print "%s %s: Not Judge" % (cyan(data['id']), yellow(question['title']))

if __name__ == "__main__":
    cfg = {
        'host': 'juice.cs.ccu.edu.tw',
        'url-submit': 'https://{host}/api/v1/submissions/{uuid}/cli?token={token}',
        'url-view': 'https://{host}/api/v1/submissions/{id}?token={token}',
        'url-recent': 'https://{host}/api/v1/submissions/recent?token={token}',
        'token': None,
        'uuid': None,
        'lang': None,
        'code': None,
        'page': 1
    }
    Config = ConfigParser.ConfigParser(allow_no_value = True)
    for file in cfgfile:
        Config.read(cfgfile[file])
        if Config.has_section('defaults'):
            for tag in cfg:
                if(Config.has_option('defaults', tag)):
                    cfg[tag] = Config.get('defaults', tag)

    parser = argparse.ArgumentParser(description = "Turnin Code to Juice", prog = sys.argv[0])
    parser.add_argument('--url-submit', dest = 'url-submit', help = "Submit Url")
    parser.add_argument('--url-view', dest = 'url-view', help = "View Submit Url")
    parser.add_argument('--url-recent', dest = 'url-recent', help = "Recent Url")
    parser.add_argument('-H', dest = 'host', help = "Turnin Host")
    parser.add_argument('-l', dest = 'lang', help = "Code Language")
    parser.add_argument('-t', dest = 'token', help = "User's token (from webpage)")
    parser.add_argument('-u', dest = 'uuid', help = "Question's UUID from (webpage)")
    parser.add_argument('-p', dest = 'page', type=int, help = "List Turnin Page")
    parser.add_argument('code', nargs = '?', help = "Your Code")
    parser.set_defaults(**cfg)
    args = vars(parser.parse_args(sys.argv[1:]))

    args['id'] = None
    if args['code'] is not None:
        print(white("Turnin code:"))
        turnin(args)
    if args['id'] is not None:
        print(white("wait for judging:"))
        turnincheck(args)
    if args['page'] is not None:
        print(white("last 5 submissions:"))
        recent(args)
