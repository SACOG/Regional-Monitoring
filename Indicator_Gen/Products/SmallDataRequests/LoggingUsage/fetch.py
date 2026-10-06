

import shutil
from datetime import datetime
import chardet


def get_prev_month():

    year = datetime.now().year
    month = datetime.now().month
    if month == 1:
        month = str(12)
        year = year-1
    elif month > 10:
        month = str(month-1)
    else:
        month = f'0{month-1}'
    year = str(year)[2:]

    return f'{year}{month}'


def fetch_log_files(path_to_logs):

    prev_month = get_prev_month()
    print('\nFetching all log files from the previous month...')
    log_files = [log for log in path_to_logs.iterdir() if log.is_file() and prev_month in str(log.stem)]
    if len(log_files) >= 28:
        print(f'Number of log files: {len(log_files)}')
    else:
        print('WRONG NUMBER OF LOG FILES!!!')
    print(f'Example log file: {log_files[0]}')

    return log_files


def detect_encoding(txt_file):
    with open(txt_file, 'rb') as f:
        raw = f.read()
    encoding = chardet.detect(raw)['encoding']
    # text = raw.decode(enc)
    return encoding


def write_downloaded_files_to_txt(log_files):

    print('\nWriting downloaded file names to txt file...')
    dt_errors={}
    encodings={}
    with open("I:\Projects\Josh\Regional Monitoring\LoggingUsage\download_log_files\_DownloadedFiles.txt", "w") as file:
        for filelist in log_files:
            try:
                encoding = detect_encoding(filelist)
                encodings[filelist] = encoding
                with open(filelist, 'r', encoding=encoding) as fp:
                    lines = fp.readlines()
                    for line in lines:
                        if line.find('.xlsx') != -1:
                            parse = line.split()
                            # indexVal = len(parse)

                            theDate = parse[0]
                            theFile = parse[4]
                            theResult = theDate + " " + theFile
                            file.write(theResult + "\n")
            except Exception as e:
                print('How exceptional!', e)
                dt_errors[filelist] = e
    print('Done')
    print('View errors (if any):', dt_errors)


def archive_downloads_list(path_to_downloads_list):

    print('\nArchiving downloads list...')
    file_to_be_archived = path_to_downloads_list/'_DownloadedFiles.txt'
    archived_file_name  = path_to_downloads_list/f'_DownloadedFiles_20{get_prev_month()}.txt'
    shutil.copy(file_to_be_archived, archived_file_name)
    print('Done\n')
