import getpass
import logging
import logging.config
import os
import shutil
import urllib
from urllib.request import urlopen
import time
import subprocess


def create_path_str(path_list):
    full_path = '';
    for x in path_list:
        full_path = os.path.join(full_path,x)
    return full_path

def directory_exist(dir_name):
    return os.path.isdir(dir_name);

def file_exist(file_name):
    return os.path.exists(file_name)

def create_directory(dir_name):
    if (not file_exist(dir_name) and 
        not directory_exist(dir_name)):
        os.makedirs(dir_name)
        return True
    else:
        return False

def create_file(file_name):
    if (not file_exist(file_name) and 
        not directory_exist(file_name)):
        file = open(file_name, 'w')
        file.close()
        return True
    else:
        return False

def mv(src, dest):
    shutil.move(src, dest)

def rm(path_name):
    shutil.rmtree(path_name)

def rmf(path_name):
    os.remove(path_name)

def download_from_url(url, dest):
    response = urlopen(url)
    fh = open(dest, "w")
    fh.write(response.read().decode('utf-8'))
    fh.close()


def main():
 
    user = getpass.getuser()
    home =  os.path.expanduser('~')
       
    logconf_down_path = create_path_str([home, '.logging.conf.down'])
    logconf_file_path = create_path_str([home, 'logging.conf'])
    download_from_url('https://raw.githubusercontent.com/alepapadop/vimrc/master/logging.conf', logconf_down_path)
    if file_exist(logconf_down_path):
        mv(logconf_down_path, logconf_file_path)
        if file_exist(logconf_file_path):
            logging.config.fileConfig(logconf_file_path)
            log = logging.getLogger(__name__)
            log.setLevel(logging.DEBUG)
        else:
            print('could not set up logging process')
            return
    else :
        print('could not download: https://raw.githubusercontent.com/alepapadop/vimrc/master/logging.conf')
        return

    error = False
    ts = time.time()

    try:
        subprocess.check_call(['which','git'])
    except subprocess.CalledProcessError:
        log.info('git is not installed, the process will stop :(')
        return

    try:
        subprocess.check_call(['which','gcc'])
    except subprocess.CalledProcessError:
        log.info('gcc is not installed, the process will stop :(')
        return

    try:
        subprocess.check_call(['which','cmake'])
    except subprocess.CalledProcessError:
        log.info('cmake is not installed, the process will stop :(')
        return
    
    try:
        subprocess.check_call(['which','vim'])
    except subprocess.CalledProcessError:
        log.info('vim is not installed, the process will stop :(')
        return

    log.info('user: {0}'.format(user))
    log.info('home direcotry: {0}'.format(home))
   
    vim_dir_path = create_path_str([home, '.vim'])
    bundle_dir_path = create_path_str([vim_dir_path, 'bundle'])
    vundle_dir_path = create_path_str([bundle_dir_path, 'Vundle.vim'])
    vimrc_file_path = create_path_str([home, '.vimrc'])
    ycm_extra_conf_dir_path = create_path_str([vim_dir_path, 'ycm_extra_conf'])
    ycm_extra_conf_c_dir_path = create_path_str([ycm_extra_conf_dir_path, 'c'])
    ycm_extra_conf_c_file_path = create_path_str([ycm_extra_conf_c_dir_path, 'ycm_extra_conf.py'])
    ycm_extra_conf_cpp_dir_path = create_path_str([ycm_extra_conf_dir_path, 'cpp'])
    ycm_extra_conf_cpp_file_path = create_path_str([ycm_extra_conf_cpp_dir_path, 'ycm_extra_conf.py'])
    
    vim_dir_backup_path = create_path_str([home, '.vim.backup' + str(ts)])
    vimrc_file_backup_path = create_path_str([home, '.vimrc.backup' + str(ts)])

    vimrc_file_down_path = create_path_str([home, '.vim.down'])
    ycm_extra_conf_c_file_down_path = create_path_str([home, 'ycm_extra_conf.c.down'])
    ycm_extra_conf_cpp_file_down_path = create_path_str([home, 'ycm_extra_conf.cpp.down'])

    vimrc_url = 'https://raw.githubusercontent.com/alepapadop/vimrc/master/vimrc'
    ycm_extra_conf_c_url = 'https://raw.githubusercontent.com/alepapadop/vimrc/master/ycm_extra_conf_files/c/ycm_extra_conf.py'
    ycm_extra_conf_cpp_url = 'https://raw.githubusercontent.com/alepapadop/vimrc/master/ycm_extra_conf_files/cpp/ycm_extra_conf.py'

    if directory_exist(vim_dir_path):
        log.info('vim dir path: {0}'.format(vim_dir_path))
    else:
        log.info('No .vim directory detected')

    if file_exist(vimrc_file_path):
        log.info('vimrc path: {0}'.format(vimrc_file_path))
    else:
        log.info('No .vimrc file detected');
 
    #Download files from github
    download_from_url(vimrc_url, vimrc_file_down_path)
    download_from_url(ycm_extra_conf_c_url, ycm_extra_conf_c_file_down_path)
    download_from_url(ycm_extra_conf_cpp_url, ycm_extra_conf_cpp_file_down_path)
    if not file_exist(vimrc_file_down_path):
        error = True
        log.info('could not download: https://raw.githubusercontent.com/alepapadop/vimrc/master/vimrc')
    elif not file_exist(ycm_extra_conf_c_file_down_path):
        error = True
        log.info('could not download: https://raw.githubusercontent.com/alepapadop/vimrc/master/ycm_extra_conf_files/c/ycm_extra_conf.py')
    elif not file_exist(ycm_extra_conf_cpp_file_down_path):
        error = True
        log.info('could not download: https://raw.githubusercontent.com/alepapadop/vimrc/master/ycm_extra_conf_files/cpp/ycm_extra_conf.py ')
    else:
        log.info('all files downloaded :)')
    
    if error:
        log.info('sorry error in download, the process will stop :(')

    if not error:
        #Backup existing vim data
        if directory_exist(vim_dir_path):
            mv(vim_dir_path, vim_dir_backup_path) 
            log.info('vim dir backup path: {0}'.format(vim_dir_backup_path))
            if not directory_exist(vim_dir_backup_path):
                error = True
                log.info("could not backed up .vim")
            else: 
                log.info("backed up .vim")
        

        if file_exist(vimrc_file_path):
            mv(vimrc_file_path, vimrc_file_backup_path)
            log.info('vimrc backup path: {0}'.format(vimrc_file_backup_path))   
            if not file_exist(vimrc_file_backup_path):
                error = True
                log.info("back up .vimrc")
        
        if error:
            log.info('sorry error in backup, the process will stop :(')

        #create file structure
        if not error:

            create_directory(vim_dir_path)
            if not directory_exist(vim_dir_path):
                error = True
                log.info("could not creat: {0}".format(vim_dir_path))
            
            create_directory(bundle_dir_path)
            if not directory_exist(bundle_dir_path):
                error = True
                log.info("could not creat: {0}".format(bunle_dir_path))

            if not error:
                create_directory(ycm_extra_conf_dir_path)
            if not directory_exist(ycm_extra_conf_dir_path):
                error = True
                log.info("could not creat: {0}".format(ycm_extra_conf_dir_path))
            
            if not error:
                create_directory(ycm_extra_conf_c_dir_path)
            if not directory_exist(ycm_extra_conf_c_dir_path):
                error = True
                log.info("could not creat: {0}".format(ycm_extra_conf_c_dir_path))

            if not error:
                create_directory(ycm_extra_conf_cpp_dir_path)
            if not directory_exist(ycm_extra_conf_cpp_dir_path):
                error = True
                log.info("could not creat: {0}".format(ycm_extra_conf_cpp_dir_path))

            if error:
                log.info('sorry error in file structure, the process will stop :(')
            
            # move downloaded files to their destination
            if not error:
                mv(vimrc_file_down_path,vimrc_file_path)
                mv(ycm_extra_conf_c_file_down_path, ycm_extra_conf_c_file_path)
                mv(ycm_extra_conf_cpp_file_down_path, ycm_extra_conf_cpp_file_path)
 
    if not error and not file_exist(vundle_dir_path):
        try:
            subprocess.check_call(['git', 'clone', 'https://github.com/gmarik/Vundle.vim.git', create_path_str([bundle_dir_path, 'Vundle.vim'])])
        except subprocess.CalledProcessError:
            erro = True
            log.info('could not clone vundle, the process will stop :(')
                
    if not error:
        try:
            subprocess.check_call(['vim','+PluginInstall','+qall'])
        except subprocess.CalledProcessError:
            error = True
            log.info('could not install the plugins')
    
    if not error:
        try:
            os.chdir(create_path_str([bundle_dir_path, 'YouCompleteMe']))
            subprocess.check_call(['sh', 'install.sh', '--clang-completer'])
        except subprocess.CalledProcessError:
            error = True
            log.info('could not compile YouCompleteMe, the process will stop :(')

    #if something has gone wrong bring back the old vim data
    if error:
        log.info('An error occured during the installation')
        if directory_exist(vim_dir_path):
            rm(vim_dir_path)
            log.info('removing .vim directory')
        if file_exist(vimrc_file_path):
            rmf(vimrc_file_path)
            log.info('removing .vimrc file')
        if directory_exist(vim_dir_backup_path):
            mv(vim_dir_backup_path, vim_dir_path)
            log.info('restoring .vim directory')
        if file_exist(vimrc_file_backup_path):
            mv(vimrc_file_backup_path, vimrc_file_path)
            log.info('restoring .vimrc file')


    #remove downloaded data from temp directory
    if file_exist(vimrc_file_down_path):
        rmf(vimrc_file_down_path)
        log.info('removing downloaded .vimrc file')
    if file_exist(ycm_extra_conf_c_file_down_path):
        rmf(ycm_extra_conf_c_file_down_path)
        log.info('removing downloaded c ycm_extra_conf.py file')
    if file_exist(ycm_extra_conf_cpp_file_down_path):
        rmf(ycm_extra_conf_cpp_file_down_path);
        log.info('removing downloaded cpp ycm_extra_conf.py file')
    if file_exist(logconf_down_path):
        log.info('removing downloaded logging.conf file')
        rmf(logconf_down_path);
    if file_exist(logconf_file_path):
        log.info('removing  logging.conf file')
        rmf(logconf_file_path);


if __name__ == "__main__":
    main()

