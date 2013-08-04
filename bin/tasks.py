import json
# import os
import urllib2
# import subprocess
import time

from celery import Celery
from pymongo import MongoClient

# NETSNIFF_UTIL = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'tools', 'netsniff.js')
DEFAULT_SLEEP_TIME = 60
WEBPAGEREST_API_KET = "XXX"


celery = Celery('tasks')
celery.config_from_object('celeryconfig')

# @celery.task
# def processtest(content):
#     #try:
#     harcontent = subprocess.Popen(['phantomjs', NETSNIFF_UTIL, content['url'], content['agent']], stdout=subprocess.PIPE).communicate()[0]
#     #    harcontent = check_output(['phantomjs', NETSNIFF_UTIL, content['url'], content['agent']])
#     #except CalledProcessError:
#     #    print ' [x] Sub-process failed'
#     #    return False
#
#     try:
#         jscontent = json.loads(harcontent)
#     except:
#         print ' [x] Unable to parse JSON output'
#         return False
#
#     jscontent['site'] = content['site']
#     jscontent['agent'] = content['agent']
#
#     dbcon = MongoClient()
#     try:
#         dbcon.perfmonitor.har.insert(jscontent)
#         print ' [x] HAR response saved'
#
#         content['nb'] -= 1
#         if content['nb'] > 0:
#             print ' [x] More tests to do, sending back msg to queue'
#             processtest.delay(content)
#         return True
#     except:
#         print ' [x] Unable to save HAR response, sending back'
#         return False

@celery.task
def processtest(content):
    def getStatus(tid):
        r = urllib2.urlopen(('http://www.webpagetest.org/testStatus.php?f=json&test=%s' % (tid,)))
        try:
            js = json.dumps(r)
        except ValueError:
            print('JSON decode failure')
            return -1
        return js['statusCode']

    if content['agent'] is 'mobile':
        mobile = 1
    else:
        mobile = 0
    url = 'http://www.webpagetest.org/runtest.php?url=%s&f=json&r=%s&runs=%d&=mobile=%d' % \
          (content['url'], WEBPAGEREST_API_KET, content['nb'], mobile)
    print("url => %s" % (url,))
    response = urllib2.urlopen(url).read()
    # response = "{u'data': {u'testId': '091111_2XFH',u'userUrl': u'http://www.webpagetest.org/result/091111_2XFH/',u'xmlUrl': u'http://www.webpagetest.org/xmlResult/091111_2XFH/'},'u'requestId': 12345,u'statusCode': 200,u'statusText': u'OK'}"

    try:
        js = json.dumps(response)
    except ValueError:
        print('JSON decode failure')
        return False
    if js['statusCode'] is not 200:
        print("Error while processing data from remote API. Error code='%d', message='%s'" % (js['statusCode'], js['statusText']))
        return False

    testId = js['testId']

    while True:
        status = getStatus(js['data']['testId'])
        if status is 100:
            time.sleep(DEFAULT_SLEEP_TIME)
            continue
        elif status is 200:
            harharhar = urllib2.urlopen('http://httparchive.webpagetest.org/export.php?test=%s' % (testId,))
            try:
                harcontent = json.loads(harharhar)
            except ValueError:
                print('Cannot parse har file')
                return False

            harcontent['site'] = content['site']
            harcontent['agent'] = content['agent']

            dbcon = MongoClient()

            try:
                dbcon.perfmonitor.har.insert(harcontent)
                print ' [x] HAR response saved'
            except:
                print(' [x] Unable to save HAR response, sending back')
                return False

            return True
        else:
            print("Error while processing data from remote API. Error code='%d'" % (status,))
            return False



@celery.task
def processcron(minutes):
    print 'Running cron of tasks for every %d minutes' % (minutes)
    dbcon = MongoClient()
    rows = dbcon.perfmonitor.sites.aggregate([
        {
         '$match': {'interval': minutes}
        },
        {'$unwind': "$urls"}
    ])

    if not rows['result']:
        print 'No tasks found to run every %d minutes' % (minutes)
        return False

    for row in rows['result']:
        msg = {
            'url': str(row['urls']),
            'site': str(row['site']),
            'account': 'me',
            'type': 'har',
            'nb': int(row['nb']),
            'agent': str(row['agent'])
        }

        processtest.delay(msg)

    print 'Done running tasks for every %d minutes' % (minutes)
    return True
