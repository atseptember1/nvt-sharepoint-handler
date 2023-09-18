import os
from fastapi import UploadFile


def _ensure_temp_dir():
    try:
        dir_path = os.path.dirname(os.path.realpath(__file__))
        temp_path = '../temp/'
        abs_temp_dir = os.path.join(dir_path, temp_path)
        if not os.path.exists(abs_temp_dir):
            try:
                os.makedirs(abs_temp_dir)
            except Exception as err:
                print(err)
    except Exception as err:
        raise(err)
    return abs_temp_dir


def write_to_file(file_name, file_bytes: UploadFile):
    try:
        temp_path = _ensure_temp_dir()
        file_path = os.path.join(temp_path, file_name)
        if os.path.exists(file_path):
            os.remove(file_path)
        with open(file_path, 'wb') as file:
            file.write(file_bytes.file.read())
            file.close()
    except Exception as err:
        raise(err)
    return file_path
