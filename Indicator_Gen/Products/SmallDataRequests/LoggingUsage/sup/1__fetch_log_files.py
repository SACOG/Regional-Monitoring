

# Setup --------------------------------------------------------------------------------------------------------------------------


from pathlib import Path
import sys
sys.path.append(Path(__file__).parent)
import fetch


PATH_LOGS = Path(r'\\webmapping-svr\c$\inetpub\logs\LogFiles\W3SVC1')
PATH_I = Path(r'I:\Projects\Josh\Regional Monitoring\LoggingUsage\download_log_files')



print('\n'*2)


# Main ----------------------------------------------------------------------------------------------------------------------



if __name__ == '__main__':


    log_files = fetch.fetch_log_files(PATH_LOGS)
    fetch.write_downloaded_files_to_txt(log_files)
    fetch.archive_downloads_list(PATH_I)



