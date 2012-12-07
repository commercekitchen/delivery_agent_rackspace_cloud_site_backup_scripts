#!/usr/bin/env python

import time
import sys
import os
import subprocess
import conf
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
backup_log = conf.backup_log
backup_log_path = conf.backup_log_path


def pull_databases_from_mosso_cloud_sites():

    log.write("%s Starting to pull databases from rackspace \n" % (time.strftime("%m/%d/%Y %H:%M:%S")))
    log.flush()

    error_message = ""


    #Cycle through mosso sites to be backed up
    for site in sites_to_be_backed_up:

	error = ""

        if not site['db_ip'] or not site['db_user'] or not site['db_pass'] or not site['db_name'] or not site['site_name']:
          log.write("%s Error, missing file variables for site %s \n" % (time.strftime("%m/%d/%Y %H:%M:%S"), site['site_name']))
          log.flush()
          continue

        site_databases_destination_path = database_backup_dir + '/' + site['site_name']

        result = subprocess.Popen("rm -rf %s" % site_databases_destination_path, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=True)

	log.write(result.stdout.read())
        error += result.stderr.read()

        result = subprocess.Popen("mkdir -p %s" % site_databases_destination_path, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=True)

	log.write(result.stdout.read())
        error += result.stderr.read()

        result = subprocess.Popen("mysqldump -h %s -u%s -p'%s' --opt %s | gzip -9 > %s/%s.`date --iso-8601`.gz" % (site['db_ip'], site['db_user'], site['db_pass'], site['db_name'], site_databases_destination_path, site['db_name']), shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=True)

	log.write(result.stdout.read())
        error += result.stderr.read()

        if error:
            error_message += ("%s Error pulling database from mosso cloud site %s \n" % (time.strftime("%m/%d/%Y %H:%M:%S"), site['db_name']))
            error_message += error

#If errors occurred, log them and send an email notification
    if error_message:
        log.write(error_message)
        log.flush()
        send_mail(error_message)

    log.write("%s Finished pulling databases from rackspace \n" % time.strftime("%m/%d/%Y %H:%M:%S"))
    log.flush()


def pull_files_from_mosso_cloud_sites():

    log.write("%s Starting to pull files from rackspace \n" % (time.strftime("%m/%d/%Y %H:%M:%S")))
    log.flush()

    error_message = ""


    #Cycle through mosso sites to be backed up
    for site in sites_to_be_backed_up:

	error = ""

        if not site['site_name'] or not site['ftp_user'] or not site['ftp_pass'] or not site['ftp_address']:
          log.write("%s Error, missing file variables for site %s \n" % (time.strftime("%m/%d/%Y %H:%M:%S"), site['site_name']))
          log.flush()
          continue

	log.write("%s Starting to pull files for site %s \n" % (time.strftime("%m/%d/%Y %H:%M:%S"), site['site_name']))
        log.flush()

        site_files_destination_path = files_backup_dir + '/' + site['site_name']
        result = subprocess.Popen("mkdir -p %s ; touch %s" % (site_files_destination_path, site_files_destination_path), shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=True)

	log.write(result.stdout.read())
        error += result.stderr.read()

        result = subprocess.Popen("""lftp -vvv -c 'open -e "set ftp:list-options -a; mirror -a --parallel=10 -v %s %s" -u %s,%s %s'""" % (site['site_name'], site_files_destination_path, site['ftp_user'], site['ftp_pass'], site['ftp_address']), shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=True)
        
	log.write(result.stdout.read())
        error += result.stderr.read()

        if error:
            error_message += ("%s Error pulling files from rackspace cloud site %s \n" % (time.strftime("%m/%d/%Y %H:%M:%S"), site['db_name']))
            error_message += error

#If errors occurred, log them and send an email notification
    if error_message:
        log.write(error_message)
        log.flush()
        send_mail(error_message)

    log.write("%s Finished pulling files from rackspace \n" % time.strftime("%m/%d/%Y %H:%M:%S"))
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
    pull_databases_from_mosso_cloud_sites()

   #Get files from remote cloud sites
    pull_files_from_mosso_cloud_sites()

    # End log file
    t2 = time.time()
    log.write("Ending script at %s\n" % time.strftime("%m/%d/%Y %H:%M:%S"))
    log.flush()
    log.write("Time to run script: %s hours\n" % round((t2-t1)/3600, 2))
    log.close()

if __name__ == '__main__':
    sys.exit(main())

