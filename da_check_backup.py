#!/usr/bin/env python

import time
import sys
import os
import subprocess
import conf
# import cloudfiles
import gzip
import datetime
from datetime import timedelta
from datetime import date
from subprocess import Popen, PIPE

def nodot(item): return item[0] != '.'



#Configurables
alert_email = conf.alert_email
path_to_sendmail = conf.path_to_sendmail
mail_from_address = conf.mail_from_address
main_backup_dir = conf.main_backup_dir
database_backup_dir = ('%s/databases' % main_backup_dir)
files_backup_dir = ('%s/files' % main_backup_dir)
sites_to_be_backed_up = conf.backup_enabled_sites
backup_log_path = conf.backup_log_path
backup_log = backup_log_path + '/backup_check.log'


def check_databases():
    log.write("%s Starting to check database backups from rackspace \n" % (time.strftime("%m/%d/%Y %H:%M:%S")))
    log.flush()

    error_message = ""

    #Cycle through mosso sites to be backed up
    for site in sites_to_be_backed_up:
    
        if not site['db_ip'] or not site['db_user'] or not site['db_pass'] or not site['db_name'] or not site['site_name']:
          log.write("%s Not backing up the database for site %s because it's missing db params \n" % (time.strftime("%m/%d/%Y %H:%M:%S"), site['site_name']))
          log.flush()
          continue

	error_message = ""
        site_databases_destination_path = database_backup_dir + '/' + site['site_name']
	yesterday = date.today() - timedelta(1)

        #Check timestamp to ensure databases are being backed up
          
	if not os.path.exists(site_databases_destination_path):
  	  error_message += "The database backup directory for site  %s does not exist \n" % site['site_name']

        elif not os.listdir(site_databases_destination_path):
  	  error_message += "The database backup file for site  %s does not exist \n" % site['site_name']
	   
        #Check timestamp to ensure databases are being backed up
	elif os.path.getmtime(site_databases_destination_path) < time.mktime(yesterday.timetuple()):
  	  error_message += "The database for %s is either old or does not exist \n" % site['site_name']

	if error_message:
	  log.write(error_message)
	  log.flush()
          send_mail(error_message)

    log.write("%s Finished checking database backups from rackspace \n" % (time.strftime("%m/%d/%Y %H:%M:%S")))
    log.flush()



def check_files():
    log.write("%s Starting to check file backups from rackspace \n" % (time.strftime("%m/%d/%Y %H:%M:%S")))
    log.flush()


    #Cycle through mosso sites to be backed up
    for site in sites_to_be_backed_up:

    
        if not site['db_ip'] or not site['db_user'] or not site['db_pass'] or not site['db_name'] or not site['site_name']:
          log.write("%s Error, missing file variables for site %s \n" % (time.strftime("%m/%d/%Y %H:%M:%S"), site['site_name']))
          log.flush()
          continue

        error_message = ""
        site_files_destination_path = files_backup_dir + '/' + site['site_name']
	yesterday = date.today() - timedelta(1)

        #Check timestamp to ensure databases are being backed up          
	if not os.path.exists(site_files_destination_path):
  	  error_message += "The file backup file for site  %s does not exist \n" % site['site_name']

        #Check timestamp to ensure databases are being backed up
	elif os.path.getmtime(site_files_destination_path) < time.mktime(yesterday.timetuple()):
  	  error_message += "The file for %s is old and appears to not be updating \n" % site['site_name']

	if error_message:
	  log.write(error_message)
	  log.flush()
          send_mail(error_message)

    log.write("%s Finished checking file backups from rackspace \n" % (time.strftime("%m/%d/%Y %H:%M:%S")))
    log.flush()


def send_mail(error_message):

        MAIL = path_to_sendmail

        msg = "To: %s\r\nFrom: %s\r\nSubject: Backup Error\r\n\r\n" % (alert_email, mail_from_address)
        msg += error_message

        p = os.popen("%s -t" % MAIL, 'w') # Send email
        p.write(msg)
        exitcode = p.close()


def main():
    global log

    # Get log ready for writing
    result = subprocess.Popen("mkdir -p %s ; touch %s ; chmod 775 -R %s" % (backup_log_path, backup_log, backup_log_path), shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=True)

    #Hacky fix to ensure that the file is actually created prior to attempting to open it
    time.sleep(1)

    log = open(backup_log,'a')
    log.write("Starting script at %s\n" % time.strftime("%m/%d/%Y %H:%M:%S"))
    log.flush()
    t1 = time.time()

    #Get Databases from cloud sites
    check_databases()

   #Get files from remote cloud sites
    check_files()

    # End log file
    t2 = time.time()
    log.write("Ending script at %s\n" % time.strftime("%m/%d/%Y %H:%M:%S"))
    log.flush()
    log.write("Time to run script: %s hours\n" % round((t2-t1)/3600, 2))
    log.close()

if __name__ == '__main__':
    sys.exit(main())

