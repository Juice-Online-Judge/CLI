#!/usr/local/bin/python
#-*- coding: utf-8 -*-

import ConfigParser
import argparse
import sys
import os
import requests

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

    data = {'language': args['lang'], 'token': args['token']}
    files = {'code': open(args['code'])}
    response = requests.post(args['url'], data = data, files = files)
    if response.status_code == 201:
        print("Success submitted")
        cfg = open(cfgfile['home'], 'w+')
        Config = ConfigParser.ConfigParser()
        Config.read(cfg)
        if not Config.has_section('defaults'):
            Config.add_section('defaults')
        Config.set('defaults', 'token', args['token'])
        Config.write(cfg)
    elif response.status_code == 401:
        print("Error: Token Mismatch")
        args['token'] = None
        turnin(args)
    elif response.status_code == 404:
        print("Error: Question Not Found")
    elif response.status_code == 520:
        print("Error: Server Error")
    else:
        print("Unknown Error! Please contact TA")

if __name__ == "__main__":
    cfg = {
        'host': 'juice.cs.ccu.edu.tw',
        #'url': 'https://{host}/api/v1/jwt/submissions/{uuid}?token={token}',
        'url': 'https://{host}/api/v1/submissions/{uuid}/cli',
        'token': None,
        'uuid': None,
        'lang': None,
        'code': None,
    }
    Config = ConfigParser.ConfigParser(allow_no_value = True)
    for file in cfgfile:
        Config.read(cfgfile[file])
        if Config.has_section('defaults'):
            for tag in cfg:
                if(Config.has_option('defaults', tag)):
                    cfg[tag] = Config.get('defaults', tag)

    parser = argparse.ArgumentParser(description = "Turnin Code to Juice", prog = sys.argv[0])
    parser.add_argument('-U', dest = 'url', nargs = 1, help = "Web Url")
    parser.add_argument('-H', dest = 'host', nargs = 1, help = "Turnin Host")
    parser.add_argument('-l', dest = 'list', nargs = '?', type=int, help = "List Turnin")
    parser.add_argument('-L', dest = 'lang', nargs = 1, help = "Code Language")
    parser.add_argument('-t', dest = 'token', nargs = 1, help = "User's token (from webpage)")
    parser.add_argument('-u', dest = 'uuid', nargs = 1, help = "Question's UUID from (webpage)")
    parser.add_argument('code', nargs = '?', help = "Your Code")
    parser.set_defaults(**cfg)
    args = vars(parser.parse_args(sys.argv[1:]))
    args['url'] = args['url'].format(**args)
    print args
    if args['code'] is not None: turnin(args)
    print args
    #if args['list'] is not None: listall(args)
