import chardet

def detectCode(txt_path):
    with open(txt_path, 'rb') as file:
        data = file.read(200000)
        dicts = chardet.detect(data)
    return dicts["encoding"]
    