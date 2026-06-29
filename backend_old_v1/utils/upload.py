import hashlib
from django.core.files.uploadedfile import UploadedFile


def calculate_md5(file: UploadedFile) -> str:
    """计算 文件的 MD5 值"""
    hash_md5 = hashlib.md5()
    
    # 保存当前位置
    if hasattr(file, "seek"):
        file.seek(0)
    
    for chunk in file.chunks():
        hash_md5.update(chunk)
    
    # 恢复位置
    if hasattr(file, "seek"):
        file.seek(0)
    
    return hash_md5.hexdigest()