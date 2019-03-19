#!/usr/bin/env python3
import csv
import json
import requests
import time
import pandas
import config # keep your GitHub and ZenHub tokens here

"""
Exports Issues from a list of repositories to individual CSV files
Uses basic authentication (Github API Token and Zenhub API Token)
to retrieve Issues from a repository that token has access to.
Supports Github API v3 and ZenHubs current working API.
https://github.com/ZenHubIO/API

Derived from https://gist.github.com/Kebiled/7b035d7518fdfd50d07e2a285aff3977
"""

def get_releases(repo_name, repo_ID):
    zenhub_releases_url = 'https://api.zenhub.io/p1/repositories/' + \
        str(repo_ID) + '/reports/releases' + ACCESS_TOKEN
    zen_rel_r = requests.get(zenhub_releases_url).json()
    print(zen_rel_r)
    global ISSUES
    for rel in zen_rel_r:
        print("TITLE: ", rel['title'].encode('utf-8'), rel['release_id'])
        zen_releaseissues_url = 'https://api.zenhub.io/p1/reports/release/' + \
        str(rel['release_id']) + '/issues' + ACCESS_TOKEN
        zen_releaseissues_r = requests.get(zen_releaseissues_url).json()
        print(zen_releaseissues_r)
        for i in zen_releaseissues_r:
            if ISSUES[i['issue_number']]:
                print('*** issues in releases', ISSUES[i['issue_number']]) #.extend([rel['title'], rel['release_id']])

def write_issues(r, csvout, repo_name, repo_ID):
    if not r.status_code == 200:
        raise Exception(r.status_code)

    r_json = r.json()
    for issue in r_json:
        print(repo_name + ' issue Number: ' + str(issue['number']))
        zenhub_issue_url = 'https://api.zenhub.io/p1/repositories/' + \
            str(repo_ID) + '/issues/' + str(issue['number']) + ACCESS_TOKEN
        zen_r = requests.get(zenhub_issue_url).json()
        time.sleep(1) # avoid hitting API limit
        global Payload

        if 'pull_request' not in issue:
            global COUNT
            COUNT += 1
            sAssigneeList = ''
            sIsEpic = ''
            sLabels = ''
            sReleases = ''
            for i in issue['assignees'] if issue['assignees'] else []:
                sAssigneeList += i['login'] + ','
            for x in issue['labels'] if issue['labels'] else []:
                sLabels += x['name'] + ','
            lEstimateValue = zen_r.get('estimate', dict()).get('value', "")
            sPipeline = zen_r.get('pipeline', dict()).get('name', "")
            sIsEpic = zen_r.get('is_epic')

            #ISSUES[issue['number']] = [repo_name, repo_ID, issue['number'], issue['title'].encode('utf-8') if issue['title'] else "", sCategory, sTag, sPriority, sPipeline, issue['user']['login'], issue['created_at'], issue['milestone']['title'] if issue['milestone'] else "", sAssigneeList[:-1], issue['body'].encode('utf-8') if issue['body'] else "", lEstimateValue, sIsEpic, sLabels[:-1]]

            csvout.writerow([repo_name, repo_ID, issue['number'], issue['title'].encode('utf-8') if issue['title'] else "", sPipeline, issue['user']['login'], issue['milestone']['title'] if issue['milestone'] else "", sAssigneeList[:-1], issue['body'].encode('utf-8') if issue['body'] else "", lEstimateValue, sIsEpic, sLabels[:-1]])
        else:
            print('You have skipped %s Pull Requests' % COUNT)
    # get_releases(repo_name, repo_ID)
    # print('***HERE ARE YOUR ISSUES: ', ISSUES)
    # csvout.writerows(ISSUES)


def get_issues(repo_data):
    repo_name = repo_data[0]
    repo_ID = repo_data[1]
    issues_for_repo_url = 'https://api.github.com/repos/%s/issues' % repo_name
    r = requests.get(issues_for_repo_url, auth=AUTH)
    write_issues(r, FILEOUTPUT, repo_name, repo_ID)
    # more pages? examine the 'link' header returned
    if 'link' in r.headers:
        pages = dict(
            [(rel[6:-1], url[url.index('<') + 1:-1]) for url, rel in
             [link.split(';') for link in
              r.headers['link'].split(',')]])
        while 'last' in pages and 'next' in pages:
            pages = dict(
                [(rel[6:-1], url[url.index('<') + 1:-1]) for url, rel in
                 [link.split(';') for link in
                  r.headers['link'].split(',')]])
            r = requests.get(pages['next'], auth=AUTH)
            write_issues(r, FILEOUTPUT, repo_name, repo_ID)
            if pages['next'] == pages['last']:
                break

PAYLOAD = ""
REPO_LIST = [("1millionwomentotech/code-for-good", "176541127")]
# TODO: get repo ID

AUTH = ('token', config.GITHUB_TOKEN)
ACCESS_TOKEN = '?access_token=' + config.ZENHUB_TOKEN

TXTOUT = open('data.json', 'w')
COUNT = 0
ISSUES = {}
FILENAME = 'github_issues.csv'
OPENFILE = open(FILENAME, 'w')
FILEOUTPUT = csv.writer(OPENFILE)
FILEOUTPUT.writerow(('Repository', 'Repository ID', 'Issue Number', 'Issue Title', 'Pipeline', 'Issue Author', 'Milestone', 'Assigned To', 'Issue Content', 'Estimate Value', 'Is Epic', 'Labels', 'Release', 'Release ID'))
for repo_data in REPO_LIST:
    get_issues(repo_data)
    #get_releases(repo_data[0], repo_data[1])

json.dump(PAYLOAD, open('data.json', 'w'), indent=4)
TXTOUT.close()
OPENFILE.close()
