import configparser
import os
import shutil
import tarfile
import subprocess
from zipfile import ZipFile
from rarfile import RarFile


def read_config(config_file='config.ini'):
    """
    Read the configuration file.

    :param str config_file: Path to the configuration file.
    :return:
    """
    if os.path.isfile(config_file) is False:
        raise NameError(config_file, 'not found')
    config = configparser.ConfigParser()
    config.read(config_file)
    return config


def download_files(config_folder,
                   raw_data_folder):
    dataset_folders = list()
    list_files = list()

    for folder in os.listdir(config_folder):
        complete_folder = os.path.join(config_folder, folder)
        if os.path.isdir(complete_folder):  # It could be a .csv
            dataset_folders.append(folder)
            config_file = os.path.join(complete_folder, 'config.ini')
            list_files.append(config_file)
            config = read_config(config_file)
            try:
                data_name = config['info']['name']
                final_filename = os.path.join(complete_folder, data_name)
                if not os.path.isfile(final_filename):
                    # URL file
                    data_url = config['info']['data_url']
                    data_download = os.path.split(config['info']['data_url'])[-1]
                    download_filename = os.path.join(complete_folder, data_download)
                    # Download file
                    bash_command = ['wget', '-nc', data_url, '-O', download_filename]
                    subprocess.run(bash_command)
                    # Extract data if necessary
                    if '.tar.gz' == data_download[-7:] or '.tgz' == data_download[-4:]:
                        tar_name = config.get('info', 'tar_name', fallback=data_name)
                        extract_tar(complete_folder=complete_folder,
                                    tar_file=data_download,
                                    tar_name=tar_name,
                                    data_name=data_name)
                    elif '.zip' == data_download[-4:]:
                        zip_name = config.get('info', 'zip_name', fallback=data_name)
                        extract_zip(complete_folder=complete_folder,
                                    zip_file=data_download,
                                    zip_name=zip_name,
                                    data_name=data_name)
                    elif '.rar' == data_download[-4:]:
                        rar_name = config.get('info', 'rar_name', fallback=data_name)
                        extract_rar(complete_folder=complete_folder,
                                    rar_file=data_download,
                                    rar_name=rar_name,
                                    data_name=data_name)
                    elif data_name != data_download:
                        os.rename(download_filename,
                                  final_filename)
                else:
                    pass
                # Copy file to raw data folder
                final_filename_2 = os.path.join(raw_data_folder, data_name)
                shutil.copyfile(final_filename, final_filename_2)
            except Exception as e:
                print('Error in', folder, ':', e)


def extract_tar(complete_folder, tar_file, tar_name, data_name):
    """
    Extract tar.gz file and get the data.
    """
    tar_file_path = os.path.join(complete_folder, tar_file)
    tf = tarfile.open(tar_file_path)
    tar_inside = tf.getnames()
    for t_i in tar_inside:
        if tar_name in t_i:
            tf.extract(t_i, path=complete_folder)
            shutil.move(os.path.join(complete_folder, t_i), os.path.join(complete_folder, data_name))
            break
    try:
        shutil.rmtree(os.path.join(complete_folder, t_i.split('/')[0]))
    except:
        pass


def extract_zip(complete_folder, zip_file, zip_name, data_name):
    """
    Extract zip.gz file and get the data.
    """
    zip_file_path = os.path.join(complete_folder, zip_file)
    tf = ZipFile(zip_file_path)
    zip_inside = tf.namelist()
    for t_i in zip_inside:
        if zip_name in t_i:
            tf.extract(t_i, path=complete_folder)
            shutil.move(os.path.join(complete_folder, t_i), os.path.join(complete_folder, data_name))
            break
    try:
        shutil.rmtree(os.path.join(complete_folder, t_i.split('/')[0]))
    except:
        pass


def extract_rar(complete_folder, rar_file, rar_name, data_name):
    """
    Extract rar.gz file and get the data.
    """
    rar_file_path = os.path.join(complete_folder, rar_file)
    rf = RarFile(rar_file_path)
    rar_inside = rf.namelist()
    for t_i in rar_inside:
        if rar_name in t_i:
            rf.extract(t_i, path=complete_folder)
            shutil.move(os.path.join(complete_folder, t_i), os.path.join(complete_folder, data_name))
            break
    try:
        shutil.rmtree(os.path.join(complete_folder, t_i.split('/')[0]))
    except:
        pass


def remove_files(config_folder):
    """
    Remove files from configuration folders.
    """
    for folder in os.listdir(config_folder):
        complete_folder = os.path.join(config_folder, folder)
        if os.path.isdir(complete_folder):  # It could be a .csv
            files = os.listdir(complete_folder)
            for file in files:
                if '.ini' not in file:
                    os.remove(os.path.join(complete_folder, file))


def check_folder(folder):
    """
    Create folder is necessary.

    :param str folder:
    """
    if not os.path.isdir(folder):
        os.mkdir(folder)


def remove_folder(folder):
    """
    Remove folder if it exists.

    :param str folder:
    """
    if os.path.isdir(folder):
        shutil.rmtree(folder, ignore_errors=True)


if __name__ == '__main__':
    try:
        parameter_config = read_config('parameter_config.ini')
    except NameError:
        print('Not custom parameter config file found, using default')
        parameter_config = read_config('default_config.ini')
    config_folders = parameter_config.get('DOWNLOAD',
                                          'config_folders').split(',')

    raw_data_folder = parameter_config.get('DOWNLOAD',
                                           'raw_folder',
                                           fallback='raw_data')
    check_folder(raw_data_folder)
    remove_older_raw = eval(parameter_config.get('DOWNLOAD',
                                                 'remove_older',
                                                 fallback='True'))

    for config_folder in config_folders:
        # A data folder per type of dataset (classification or regression)
        data_type = config_folder.split('/')[1]
        raw_subfolder = os.path.join(raw_data_folder, data_type)
        # Remove and create subfolder
        if remove_older_raw is True:
            remove_folder(raw_subfolder)
        check_folder(raw_subfolder)

        download_files(config_folder=config_folder,
                       raw_data_folder=raw_subfolder)
