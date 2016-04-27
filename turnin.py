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

def turnin(args):
    if not os.path.isfile(args['code']):
        print('Error: Not a regular file: %s' % (args['code']))
        return
    if args['token'] is None:
        args['token'] = raw_input("Enter your token: ")
    if args['uuid'] is None:
        args['uuid'] = raw_input("Enter question's UUID: ")
    for lang in langs:
        if args['code'].endswith(lang):
            args['lang'] = langs[lang]
    if args['lang'] is None:
        args['lang'] = raw_input("Enter your Language(ex: C): ").lower()

    args['url-submit'] = args['url-submit'].format(**args)
    #print args['url-submit']
    data = {'language': args['lang']}
    files = {'code': open(args['code'])}
    headers = {'X-Requested-With': 'XMLHttpRequest'}
    response = requests.post(args['url-submit'], data = data, files = files, headers = headers)

    if response.status_code == 201:
        print("Success submitted")
        print response.json()
        data = response.json()
        args['id'] = data['id']
    elif response.status_code == 401:
        print("Error: Token Mismatch")
        args['token'] = None
        turnin(args)
    elif response.status_code == 403:
        print("Error: Test Not Start or Test End")
    elif response.status_code == 404:
        print("Error: Question Not Found")
    elif response.status_code == 422:
        print("Error: Language Not Support or File Error")
        print(response.text)
    elif response.status_code in (500, 520):
        print("Error: Server Error")
    else:
        print("Unknown Error(%d)! Please contact TA" % response.status_code)
        print(response.text)

def turnincheck(args):
    print("wait for judging:")
    args['url-view'] = args['url-view'].format(**args)
    headers = {'X-Requested-With': 'XMLHttpRequest'}
    for t in (1, 2, 2):
        time.sleep(t)
        response = requests.get(args['url-view'], headers = headers)
        data = response.json()
        if data['judge'] is not None:
            print "%s '%s': %s" % (data['id'], question['title'], judge['result'])
            print "\ttime: %s memory: %s" % (judge['time'], judge['memory'])
            print "\tmessage: %s" % (judge['judge_message'])
            break
    
def recent(args):
    print("last 10 submissions:")
    args['url-recent'] = args['url-recent'].format(**args)
    headers = {'X-Requested-With': 'XMLHttpRequest'}
    response = requests.get(args['url-recent'], headers = headers)
    res = response.json()
    for data in res['data']:
        judge = data['judge']
        question = data['question']
        if data['judge'] is not None:
            print "%s '%s': %s" % (data['id'], question['title'], judge['result'])
            print "\ttime: %s memory: %s" % (judge['time'], judge['memory'])
            print "\tmessage: %s" % (judge['judge_message'])
        else:
            print "%s '%s': Not Judge" % (data['id'], question['title'])

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
