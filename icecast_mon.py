#!/usr/bin/python2.7

# Created by Gonzalo Martinez (http://www.deploshark.com.ar)
# Maintained by Alejandro Ferrari (http://www.wmconsulting.info)

import sys
from subprocess import check_output
import subprocess
import shlex
import json
import time
import smtplib
import datetime
import os

try:
    URL_STREAM = sys.argv[1]
except:
    URL_STREAM = ""
SMTP_USER = "user@gmail.com"
SMTP_PASS = "PASSWORD"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
TO = "someone@gmail.com"
STATE_FILE = '/tmp/icecast_check.state'
AVPROBE_PATH = '/root/bin/avprobe'

def stdout_log(message):
    now = datetime.datetime.today().isoformat()
    print "%s - %s" % (now, message)

def message_by_state(state):
    if state == 'down':
        subject = "Alert - icemon : stream %s down by 30 seconds" % URL_STREAM
        msg = 'Streaming '+ URL_STREAM+ ' is down by 30 seconds on '+ datetime.datetime.today().strftime("%Y-%m-%d %H:%M")
    elif state == 'up':
        subject = "Recovery - icemon : stream %s up in last check" % URL_STREAM
        msg = 'Streaming '+ URL_STREAM+ ' is up in last check on '+ datetime.datetime.today().strftime("%Y-%m-%d %H:%M")
    return subject, msg

def sendmail(new_state):
        smtpobj = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        smtpobj.ehlo()
        smtpobj.starttls()
        smtpobj.login(SMTP_USER, SMTP_PASS)
        subject, message = message_by_state(new_state)
        header = 'To:' + TO + '\n' + 'From: ' + SMTP_USER + '\n' + 'Subject: ' + subject + ' \n'
        msg = header + '\n '+ message + ' \n\n'
        stdout_log("Sending message by mail to %s" % TO)
        smtpobj.sendmail(SMTP_USER, TO, msg)


def check_last_state(actual_state):
    if not os.path.exists(STATE_FILE):
        f = open(STATE_FILE, 'w+')
    else:
        f = open(STATE_FILE, 'r+')
    state = f.read().strip()
    if state <> actual_state:
        f.seek(0)
        f.write(actual_state)
        f.truncate()
        f.close()
        return True
    else:
        return False

def parse_avprobe_result(output):
    result =  json.loads(output)
    if "streams" in result:
        return True
    else:
        return False


def exec_avprobe(url):
    command = AVPROBE_PATH + " -loglevel quiet -show_streams %s -of json" % url
    stdout_log("Check streaming from %s" % url)
    try:
        out = check_output(shlex.split(command), stderr=subprocess.STDOUT)
    except:
        out = "{}"
    retry = 1
    while retry <= 3:
        if not parse_avprobe_result(out):
            time.sleep(10)
            print "%s - Retrying connect to streaming %s" % (datetime.datetime.today().isoformat(), url)
            try:
                out = check_output(shlex.split(command), stderr=subprocess.STDOUT)
            except:
                retry+=1
                success = False
        else:
            stdout_log("%s streaming is OK" % url)
            success = True
            break
    return success

def main():
    state = None
    if not exec_avprobe(URL_STREAM):
        stdout_log("Error on streaming %s" % URL_STREAM)
        state = "down"
    else:
        state = "up"
    if check_last_state(state):
        sendmail(state)
    else:
        stdout_log("Check not change from last status")

if __name__=="__main__":
    main()
