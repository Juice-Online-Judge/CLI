#!/usr/local/bin/python
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
    elif s in ('WA', 'SE', 'CE', 'RE', 'TLE', 'MLE', 'OLE', 'RF'): return red(s)

def turnin(args):
    print(white("Turnin code:"))
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

    args['url-submit'] = args['url-submit'].format(**args)
    #print args['url-submit']
    data = {'language': args['lang']}
    files = {'code': open(args['code'])}
    headers = {'X-Requested-With': 'XMLHttpRequest'}
    response = requests.post(args['url-submit'], data = data, files = files, headers = headers)

    if response.status_code == 201:
        print(green("Success submitted"))
        print response.json()
        data = response.json()
        args['id'] = data['id']
    elif response.status_code == 401:
        print(red("Error: Token Mismatch"))
        args['token'] = None
        turnin(args)
    elif response.status_code == 403:
        print(red("Error: Test Not Start or Test End"))
    elif response.status_code == 404:
        print(red("Error: Question Not Found"))
    elif response.status_code == 422:
        print(red("Error: Language Not Support or File Error"))
        print(response.text)
    elif response.status_code in (500, 520):
        print(red("Error: Server Error"))
    else:
        print(red("Unknown Error(%d)! Please contact TA" % response.status_code))
        print(response.text)
    print("")

def turnincheck(args):
    print(white("wait for judging:"))
    args['url-view'] = args['url-view'].format(**args)
    headers = {'X-Requested-With': 'XMLHttpRequest'}
    for t in (1, 2, 2):
        time.sleep(t)
        response = requests.get(args['url-view'], headers = headers)
        data = response.json()
        if data['judge'] is not None:
            print "%s %s: %s" % (cyan(data['id']), yellow(question['title']), autocolor(judge['result']))
            print "\t%s %s %s %s" % (green("time:"), white(judge['time']), green("memory:"), white(judge['memory']))
            print "\t%s %s" % (green("message:"), white(judge['judge_message']))
            break
    print "%s %s: Not Judge" % (cyan(data['id']), yellow(question['title']))
    print("")
    
def recent(args):
    print(white("last 10 submissions:"))
    args['url-recent'] = args['url-recent'].format(**args)
    headers = {'X-Requested-With': 'XMLHttpRequest'}
    response = requests.get(args['url-recent'], headers = headers)
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
        'list': 0
    }
    Config = ConfigParser.ConfigParser(allow_no_value = True)
    for file in cfgfile:
        Config.read(cfgfile[file])
        if Config.has_section('defaults'):
            for tag in cfg:
                if(Config.has_option('defaults', tag)):
                    cfg[tag] = Config.get('defaults', tag)

    parser = argparse.ArgumentParser(description = "Turnin Code to Juice", prog = sys.argv[0])
    parser.add_argument('--url-submit', dest = 'url-submit', nargs = 1, help = "Submit Url")
    parser.add_argument('--url-view', dest = 'url-view', nargs = 1, help = "View Submit Url")
    parser.add_argument('--url-recent', dest = 'url-recent', nargs = 1, help = "Recent Url")
    parser.add_argument('-H', dest = 'host', nargs = 1, help = "Turnin Host")
    parser.add_argument('-L', dest = 'lang', nargs = 1, help = "Code Language")
    parser.add_argument('-t', dest = 'token', nargs = 1, help = "User's token (from webpage)")
    parser.add_argument('-u', dest = 'uuid', nargs = 1, help = "Question's UUID from (webpage)")
    parser.add_argument('-l', dest = 'list', nargs = 1, type=int, help = "List Turnin")
    parser.add_argument('code', nargs = '?', help = "Your Code")
    parser.set_defaults(**cfg)
    args = vars(parser.parse_args(sys.argv[1:]))

    args['id'] = None
    if args['code'] is not None:
        turnin(args)
    if args['id'] is not None:
        # Write Token
        cfg = open(cfgfile['home'], 'w+')
        Config = ConfigParser.ConfigParser()
        Config.read(cfg)
        if not Config.has_section('defaults'):
            Config.add_section('defaults')
        Config.set('defaults', 'token', args['token'])
        Config.write(cfg)

        turnincheck(args)
    #print args
    if args['list'] is not None:
        recent(args)
