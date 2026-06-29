from django.http import FileResponse, HttpRequest, HttpResponse, JsonResponse
from django.db import transaction
from utils.object_utils import safe_get
from utils.upload import calculate_md5
from utils.request_utils import querydict_to_dict_with_type_convert
from identity.models import User
from filecenter.models import File, FileReference
from filecenter.utils import build_storage_path, build_file_path
from django.conf import settings
from extensions.exceptions import BizException, ERROR_UPLOAD_FILE_FAILED, ERROR_DATA_NOT_FOUND, ERROR_ILLEGAL_ARGUMENT
import re
import os
import json
import hashlib
import mimetypes
import shutil
import time
import logging
from urllib.parse import quote as url_quote

logger = logging.getLogger(__name__)


# ============================================================
# 文件上传
# ============================================================

def upload_file(request: HttpRequest):
    """
    【服务层】处理文件上传（单文件 or 分片）
    
    要求：
      - request.user 必须关联 company.tenant_slug
      - 文件通过 request.FILES['file'] 上传
      - 分片需提供 slice_order/slice_total/finally_md5
    
    返回：
      - 单文件：包含 file_md5, stored_file_id 等
      - 分片：{"status": "chunk_received", "order": N}
      - 合并完成：同单文件结构
    """
    file = request.FILES.get("file")
    if not file:
        raise BizException(ERROR_UPLOAD_FILE_FAILED, "上传文件不存在")
    
    user = request.user
    tenant_slug = safe_get(user, "company.tenant_slug")
    if not tenant_slug:
        raise BizException(ERROR_DATA_NOT_FOUND, "当前用户未关联租户信息")
    
    post = querydict_to_dict_with_type_convert(request.POST)
    business_id = post.get("business_id")
    business_type = post.get("business_type")
    usage_type = post.get("usage_type")
    
    slice_total = post.get("slice_total", 0)
    if slice_total > 0:
        # --- 处理分片上传 ---
        finally_md5 = post.get("finally_md5")
        if not finally_md5:
            raise BizException(ERROR_UPLOAD_FILE_FAILED, "分片上传缺少 finally_md5 参数")
        slice_order = post.get("slice_order")
        slice_md5 = post.get("slice_md5")
        filename = post.get("filename")
        return _handle_chunked_upload(
            tenant_slug=tenant_slug,
            user=user,
            file=file,
            filename=filename,
            slice_order=slice_order,
            slice_md5=slice_md5,
            slice_total=slice_total,
            finally_md5=finally_md5,
            business_id=business_id,
            business_type=business_type,
            usage_type=usage_type,
        )
    else:
        # --- 处理单文件上传 ---
        return _handle_single_file_upload(
            tenant_slug=tenant_slug,
            user=user,
            file=file,
            filename=file.name,
            business_id=business_id,
            business_type=business_type,
            usage_type=usage_type,
        )


def _handle_chunked_upload(
    tenant_slug: str,
    user: User,
    file,
    filename: str,
    slice_order: int,
    slice_md5: str,
    slice_total: int,
    finally_md5: str,
    business_id: str,
    business_type: str,
    usage_type: str = "unknown",
):
    tmp_dir = _build_temp_chunk_dir(tenant_slug, finally_md5)
    manifest_path = os.path.join(tmp_dir, ".manifest.json")
    chunk_path = os.path.join(tmp_dir, slice_md5)

    # --- 保存分片 ---
    if not os.path.exists(chunk_path):
        with open(chunk_path, "wb") as f:
            for chunk in file.chunks():
                f.write(chunk)
    
    # --- 更新 manifest
    manifest = _load_or_create_manifest(manifest_path, filename, slice_total, finally_md5)
    chunk_map = {c["md5"]: c for c in manifest["chunks"]}
    chunk_map[slice_md5] = {"md5": slice_md5, "order": slice_order}
    manifest["chunks"] = list(chunk_map.values())
    
    with open(manifest_path, "w") as f:
        json.dump(manifest, f)

    # --- 检查是否上传完成 ---
    if len(manifest["chunks"]) == slice_total:
        return _finalize_upload(
            tmp_dir=tmp_dir,
            manifest=manifest,
            tenant_slug=tenant_slug,
            user=user,
            business_id=business_id,
            business_type=business_type,
            usage_type=usage_type,
        )
    else:
        return {
            "status": "chunk_received",
            "ready": False,
            "received_chunks": len(manifest["chunks"]),
            "total_chunks": slice_total,
        }


def _build_temp_chunk_dir(tenant_slug: str, finally_md5: str) -> str:
    """
    构建分片临时存储路径：
        {STORE_PATH}/{tenant_slug}/temp/{YYYY-MM}/{finally_md5}
    """
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", tenant_slug):
        raise BizException(ERROR_ILLEGAL_ARGUMENT, "Invalid tenant_slug")
    if not re.fullmatch(r"[a-f0-9]{32}", finally_md5):
        raise BizException(ERROR_ILLEGAL_ARGUMENT, "Invalid finally_md5")
    
    # --- 构建路径 ---
    date_dir = time.strftime("%Y-%m")
    rel_dir = f"temp/{date_dir}/{finally_md5}"
    full_dir = os.path.join(settings.STORE_PATH, tenant_slug, rel_dir)

    # --- 确保目录存在 ---
    os.makedirs(full_dir, exist_ok=True)

    return full_dir

    
def _load_or_create_manifest(path: str, filename: str, total: int, finally_md5: str) -> dict:
    if os.path.exists(path):
        with open(path, "r") as f:
            data = json.load(f)
            # 兼容旧格式
            if "chunks" not in data:
                data["chunks"] = []
            return data
    else:
        return {
            "filename": filename,
            "slice_total": total,
            "finally_md5": finally_md5,
            "chunks": [],
        }


def _finalize_upload(
    tmp_dir: str,
    manifest: dict,
    tenant_slug: str,
    user: User,
    business_id: int,
    business_type: str,
    usage_type: str,
):
    try:
        # --- 按 order 排序 ---
        chunks = sorted(manifest["chunks"], key=lambda x: x["order"])
        
        # --- 合并分片 ---
        merged_md5 = hashlib.md5()
        finally_md5 = manifest["finally_md5"]
        filename = manifest["filename"]
        ext = _extract_ext(filename)
        abs_path, rel_path = build_storage_path(tenant_slug, finally_md5, ext, business_id, usage_type)
        with open(abs_path, "wb") as f:
            for chunk in chunks:
                chunk_path = os.path.join(tmp_dir, chunk["md5"])
                with open(chunk_path, "rb") as f_chunk:
                    while True:
                        data = f_chunk.read(1024 * 1024) # 1M buffer
                        if not data:
                            break
                        f.write(data)
                        merged_md5.update(data)
        
        # --- 验证文件 MD5 ---
        if merged_md5.hexdigest() != finally_md5:
            os.remove(abs_path)
            raise BizException(ERROR_UPLOAD_FILE_FAILED, "分片上传文件合并失败")

        # --- 创建文件记录 ---
        file_size = os.path.getsize(abs_path)
        with transaction.atomic():
            file = File.objects.create(
                company_id=user.company_id,
                organization_id=user.organization_id,
                filename=filename,
                type=_map_ext_to_usage(ext),
                size=file_size,
                md5=finally_md5,
                storage_path=rel_path,
                uploaded_by_id=user.id,
            )
            
            if business_id and business_type and usage_type:
                FileReference.objects.create(
                    file_id=file.id,
                    business_id=business_id,
                    business_type=business_type,
                    usage_type=usage_type,
                )
        
        # --- 清理临时目录 ---
        shutil.rmtree(tmp_dir, ignore_errors=True)

        return {
            **file.to_dict(),
            "is_completed": True
        }
    except Exception as e:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise e


def _handle_single_file_upload(
    tenant_slug: str,
    user: User,
    file,
    filename: str,
    business_id: int,
    business_type: str,
    usage_type: str = "unknown",
):
    ext = _extract_ext(filename)
    md5 = calculate_md5(file)
    
    abs_path, rel_path = build_storage_path(tenant_slug, md5, ext, business_id, usage_type)

    # --- 保存文件 ---
    with open(abs_path, "wb") as f:
        for chunk in file.chunks():
            f.write(chunk)
    
    file = File.objects.create(
        company_id=user.company_id,
        organization_id=user.organization_id,
        filename=filename,
        type=_map_ext_to_usage(ext),
        size=file.size,
        md5=md5,
        storage_path=rel_path,
        uploaded_by_id=user.id,
    )
    
    if business_id and business_type and usage_type:
        FileReference.objects.create(
            file_id=file.id,
            business_id=business_id,
            business_type=business_type,
            usage_type=usage_type,
        )
    
    return file.to_dict()


def _safe_int(value) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def _extract_ext(filename: str) -> str:
    if "." in filename:
        ext = filename.rsplit(".", 1)[-1].lower()
        return ext if re.fullmatch(r"[a-z0-9_-]+", ext) else "bin"
    return "bin"


def _map_ext_to_usage(ext: str) -> str:
    if ext in {"jpg", "jpeg", "png"}:
        return "trial_photo"
    elif ext in {"mp4", "mov"}:
        return "trial_video"
    elif ext == "pdf":
        return "inspection_report"
    elif ext == "txt":
        return "moldflow_log"
    elif ext == "ppt" or ext == "pptx":
        return "moldflow_report"
    else:
        return "other_file"


def _get_file_by_uuid(uuid: str) -> File | None:
    """获取文件"""
    file = File.objects.filter(uuid=uuid).first()
    if not file:
        raise BizException(ERROR_DATA_NOT_FOUND, "文件信息不存在")
    return file
    

# ============================================================
# 文件查询 / 删除
# ============================================================

def get_file_info(uuid: str) -> dict:
    """获取文件信息"""
    file = _get_file_by_uuid(uuid)
    return file.to_dict()


def delete_file(uuid: str) -> dict:
    """删除文件"""
    file = _get_file_by_uuid(uuid)
    file.soft_delete()


def get_file_list_by_business(
    company_id: int,
    business_id: str,
    business_type: str,
    usage_type: str,
):
    """
    获取文件列表

    业务关联存在 FileReference 中，通过 join File 表获取，
    并用 File.company_id 过滤租户。
    """
    if not business_id or not business_type or not usage_type:
        raise BizException(ERROR_ILLEGAL_ARGUMENT, "参数错误")

    file_refs = FileReference.objects.filter(
        business_id=business_id,
        business_type=business_type,
        usage_type=usage_type,
        file__company_id=company_id,
        file__is_deleted=False,
    ).select_related("file")

    data = [ref.file.to_dict() for ref in file_refs]
    return {"files": data}


# ============================================================
# 文件下载
# ============================================================

def download_file(company_id: int, tenant_slug: str, uuid: str, dispose_type: str) -> dict:
    """下载文件（代理）- 需要登录"""
    file = _get_file_by_uuid(uuid)
    
    # 租户隔离验证
    if file.company_id != company_id:
        raise BizException(ERROR_DATA_NOT_FOUND, "文件不存在或无权访问")
    
    return _serve_file(file, tenant_slug, dispose_type)


def upload_single_file(uploaded_file, tenant_slug: str, storage_dir: str, file_category: str = "other_file"):
    """
    上传单个文件（不依赖 HttpRequest，供 Service 层直接调用）
    
    Args:
        uploaded_file: Django UploadedFile 对象
        tenant_slug: 租户标识
        storage_dir: 存储目录（相对路径）
        file_category: 文件类别
        
    Returns:
        dict: 文件信息（含 uuid, storage_path 等）
    """
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", tenant_slug):
        raise BizException(ERROR_ILLEGAL_ARGUMENT, f"Invalid tenant_slug: {tenant_slug!r}")
    
    filename = uploaded_file.name
    ext = _extract_ext(filename)
    md5 = calculate_md5(uploaded_file)
    
    # 构建存储路径
    relative_path = os.path.join(storage_dir, f"{md5}.{ext}")
    abs_path = os.path.join(settings.STORE_PATH, tenant_slug, relative_path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    
    # 保存文件
    with open(abs_path, "wb") as f:
        for chunk in uploaded_file.chunks():
            f.write(chunk)
    
    # 获取 tenant company 信息
    from identity.models import Company
    try:
        company = Company.objects.get(tenant_slug=tenant_slug)
    except Company.DoesNotExist:
        os.remove(abs_path)
        raise BizException(ERROR_DATA_NOT_FOUND, "租户不存在")
    
    # 创建文件记录
    file = File.objects.create(
        company_id=company.id,
        organization_id=company.organization_id if hasattr(company, 'organization_id') else None,
        filename=filename,
        type=_map_ext_to_usage(ext),
        size=uploaded_file.size,
        md5=md5,
        storage_path=relative_path,
    )
    
    return file.to_dict()


def download_file_by_token(tenant_slug: str, uuid: str, dispose_type: str = "attachment"):
    """
    下载文件（通过 Token 验证）- 无需登录
    
    Args:
        tenant_slug: 租户标识（从 Token 解密获得）
        uuid: 文件 UUID
        dispose_type: 处置类型（attachment=下载, inline=预览）
        
    Returns:
        FileResponse 或 HttpResponse
        
    Raises:
        BizException: 文件不存在或无权访问
    """
    from identity.models import Company
    
    # 验证租户是否存在
    try:
        company = Company.objects.get(tenant_slug=tenant_slug)
    except Company.DoesNotExist:
        raise BizException(ERROR_DATA_NOT_FOUND, "租户不存在")
    
    # 获取文件
    file = _get_file_by_uuid(uuid)
    
    # 验证文件归属（租户隔离）
    if file.company_id != company.id:
        raise BizException(ERROR_DATA_NOT_FOUND, "文件不存在或无权访问")
    
    return _serve_file(file, tenant_slug, dispose_type)


def _serve_file(file: File, tenant_slug: str, dispose_type: str, mime_type: str = None):
    """
    提供文件服务（核心方法）
    
    根据环境自动选择返回方式：
    - DEBUG=True: 使用 Django FileResponse（开发环境）
    - DEBUG=False: 使用 Nginx X-Accel-Redirect（生产环境）
    
    Args:
        file: File 对象
        tenant_slug: 租户标识
        dispose_type: 处置类型（attachment=下载, inline=预览）
        mime_type: 可选，覆盖文件的 Content-Type
        
    Returns:
        FileResponse 或 HttpResponse
        
    Raises:
        BizException: 文件不存在
    """
    from django.utils.encoding import escape_uri_path
    
    # 构建文件路径
    file_path = build_file_path(tenant_slug, file.storage_path)
    if not os.path.exists(file_path):
        raise BizException(ERROR_DATA_NOT_FOUND, "文件不存在")
    
    content_type = mime_type or file.mime_type or "application/octet-stream"
    
    # 根据环境选择返回方式
    if settings.DEBUG:
        # 开发环境：Django 直接返回文件
        return FileResponse(
            open(file_path, "rb"),
            content_type=content_type,
            as_attachment=(dispose_type == "attachment"),
            filename=file.filename
        )
    else:
        # 生产环境：Nginx X-Accel-Redirect 代理
        response = HttpResponse()
        response['Content-Type'] = content_type
        response['Content-Disposition'] = f'{dispose_type}; filename="{escape_uri_path(file.filename)}"'
        
        # Nginx X-Accel-Redirect 路径
        # 注意：必须对路径做 URL 编码，确保值全为 ASCII 字符
        # 否则 Django 会对含中文的 header 值做 RFC 2047 编码，导致 Nginx 无法匹配 location
        encoded_path = url_quote(file.storage_path, safe='/')
        response['X-Accel-Redirect'] = f"/files/{tenant_slug}/{encoded_path}"
        
        # 可选：设置 Nginx 缓冲相关 Header
        response['X-Accel-Buffering'] = 'yes'  # 启用缓冲
        response['X-Accel-Limit-Rate'] = '0'   # 不限速（0表示不限制）
        
        return response


def serve_file_by_path(tenant_slug: str, storage_path: str, dispose_type: str = "attachment"):
    """
    根据路径提供文件服务（临时文件/报告等无 File 记录的场景）
    
    先验证文件存在，再委托给 _serve_file 处理
    
    Args:
        tenant_slug: 租户标识
        storage_path: 相对于租户根目录的存储路径
        dispose_type: 处置类型（attachment=下载, inline=预览）
        
    Returns:
        FileResponse 或 HttpResponse
        
    Raises:
        BizException: 文件不存在
    """
    # 构建文件路径，验证存在性
    file_path = build_file_path(tenant_slug, storage_path)
    if not os.path.exists(file_path):
        raise BizException(ERROR_DATA_NOT_FOUND, "文件不存在")
    
    filename = os.path.basename(file_path)
    mime_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    
    # 构建轻量对象，委托核心方法处理
    file = File(filename=filename, storage_path=storage_path)
    return _serve_file(file, tenant_slug, dispose_type, mime_type=mime_type)