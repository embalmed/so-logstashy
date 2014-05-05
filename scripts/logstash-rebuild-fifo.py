#!/usr/bin/python
# logstash rebuild logs script
# takes 2 dates and tries to re-index those logs into a local fifo
# --createfifo output shows supporting logstash config
import os, threading, argparse
from datetime import datetime, date, timedelta as td

#configurables
#directory to look for files
filedir = "/opt/log/remote-bytype/"
#dict of file types to look for
files = [ 'arbor', 'tippingpt', 'netscaler', 'comware', 'vpn', 'apigee', 'firewall', 'misc' ]
#directory to create fifo sockets
sockdir = "/tmp"

#parse arguments from commandline
parser = argparse.ArgumentParser()
parser.add_argument("startDate", help="Earliest Logfile Date year-month-day (2014-04-01)")
parser.add_argument("endDate", help="Oldest Logfile Date year-month-day (2014-04-01)")
parser.add_argument("--createfifo", help="Create FIFO pipes and display logstash input info", action="store_true")
args = parser.parse_args()

#parse date string to date object
date_start = datetime.strptime(args.startDate, "%Y-%m-%d").date()
date_end = datetime.strptime(args.endDate, "%Y-%m-%d").date()
dates = []
delta = date_end - date_start
#compose an array of file dates to look for from delta
for i in range(delta.days +1):
    dates.append(date_start + td(days=i))

#create fifos
def create_fifos(files):
  print "##### logstash input configuration ####"
  print "input {"
  for x in files:
    sock = sockdir + "/" + x
    if not os.path.exists(sock):
      os.mkfifo(sock)
    print "  pipe {"
    print "    command => 'tail -f /tmp/"+x+"'"
    print "    type => '"+x+"'"
    print "  }"
  print "}"
  print "pausing in case you need to restart logstash with these settings...."
  raw_input("Press Enter to continue...")

#process logs
def chomp_logs(dates,type):
  print "starting processing for " + type
  sock = sockdir + "/" + type
  for y in dates:
    file = 0
    filename = type + "-" +  y.isoformat() + ".log"
    fullpath = filedir + filename
    if os.path.isfile(fullpath):
      file = 1
      cmd = "cat " + fullpath + " > " + sock
    fullpath = fullpath + ".bz2"
    if os.path.isfile(fullpath):
      file = 1
      cmd = "bzcat " + fullpath + " > " + sock
    if file:
      print "Sending " + fullpath + " to logstash:" + sock
      os.system(cmd)
    else:
      print "Skipping " + fullpath

if __name__ == "__main__":
  if args.createfifo:
    create_fifos(files)
  for x in files:
    threading.Thread(target=chomp_logs, args=(dates,x), name='chomp_logs_'+x).start()
