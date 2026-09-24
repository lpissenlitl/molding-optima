# 文件下载接口优化方案

## 📋 问题分析

### **原有设计的限制**

```python
# 原接口：必须登录才能下载
@method_decorator(require_login)
def get(self, request, uuid):
    return file_service.download_file(request.user, uuid, ...)
```

**问题：**
1. ❌ 客户上传的文件无法提供下载链接（客户没有系统账号）
2. ❌ 分享文件给外部人员困难
3. ❌ API 调用需要维护 session/cookie
4. ❌ 依赖 `user.company.tenant_slug`，没有 user 对象时无法工作

---

## ✅ 解决方案：双重访问控制

### **方案 A：内部用户（需要登录）**

保持原有接口不变，适用于系统内部用户。

**接口：**
- `GET /api/files/{uuid}/download/` - 下载（需登录）
- `GET /api/files/{uuid}/preview/` - 预览（需登录）

**特点：**
- ✅ 基于用户身份验证
- ✅ 自动获取 tenant_slug
- ✅ 适合内部管理系统

---

### **方案 B：外部客户（使用 Token）**

新增无需登录的下载接口，使用加密 Token 验证租户权限。

**接口：**
- `GET /api/customer/files/{uuid}/download/` - 下载（Token 验证）
- `GET /api/customer/files/{uuid}/preview/` - 预览（Token 验证）

**特点：**
- ✅ 无需登录，使用 Token 验证
- ✅ 租户隔离保证安全
- ✅ 适合客户上传场景
- ✅ 可提供公开下载链接

---

## 🔧 实现细节

### **1. Service 层新增方法**

```python
# filecenter/services/file_service.py

def download_file_by_token(tenant_slug: str, uuid: str, dispose_type: str = "attachment"):
    """
    下载文件（通过 Token 验证）- 无需登录
    
    Args:
        tenant_slug: 租户标识（从 Token 解密获得）
        uuid: 文件 UUID
        dispose_type: 处置类型（attachment=下载, inline=预览）
    """
    from identity.models import Company
    
    # 验证租户是否存在
    company = Company.objects.get(tenant_slug=tenant_slug)
    
    # 获取文件
    file = _get_file_by_uuid(uuid)
    
    # 验证文件归属（租户隔离）
    if file.company_id != company.id:
        raise BizException(ERROR_DATA_NOT_FOUND, "文件不存在或无权访问")
    
    # 构建文件路径并返回
    file_path = build_file_path(tenant_slug, file.storage_path)
    # ... 返回 FileResponse
```

---

### **2. View 层新增视图**

```python
# filecenter/views.py

class CustomerFileDownloadView(BaseView):
    """客户文件下载（通过 Token 验证，无需登录）"""
    
    def get(self, request, uuid):
        # 验证租户 Token
        token = request.META.get('HTTP_X_TENANT_TOKEN')
        tenant_slug = TenantTokenCrypto.decrypt_tenant_slug(token)
        
        # 调用 Service 层
        return file_service.download_file_by_token(
            tenant_slug=tenant_slug,
            uuid=uuid,
            dispose_type="attachment"
        )
```

---

### **3. URL 路由**

```python
# filecenter/urls.py

urlpatterns = [
    # 内部接口（需要登录）
    path("files/<uuid:uuid>/download/", views.FileDownloadView.as_view()),
    path("files/<uuid:uuid>/preview/", views.FilePreviewView.as_view()),
    
    # 客户接口（Token 验证）
    path("customer/files/<uuid:uuid>/download/", views.CustomerFileDownloadView.as_view()),
    path("customer/files/<uuid:uuid>/preview/", views.CustomerFilePreviewView.as_view()),
]
```

---

## 🚀 使用示例

### **场景 1：内部用户下载（原有方式）**

```bash
# 需要登录 cookie/session
curl -X GET http://localhost:8000/api/files/550e8400-e29b-41d4-a716-446655440000/download/ \
  -b "sessionid=xxx" \
  -o downloaded_file.txt
```

---

### **场景 2：客户下载文件（新方式）**

#### **步骤 1：上传文件后获取 UUID**

```bash
# 上传文件
POST /api/customer/moldflow/results/456/upload/
Header: X-Tenant-Token: a1b2c3d4-e5f6-7890-abcd-ef1234567890

Response:
{
    "data": {
        "file_info": {
            "uuid": "550e8400-e29b-41d4-a716-446655440000",
            "name": "analysis.txt"
        }
    }
}
```

#### **步骤 2：生成下载链接**

```python
# 后端生成下载链接
uuid = "550e8400-e29b-41d4-a716-446655440000"
token = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"

download_url = f"/api/customer/files/{uuid}/download/?token={token}"
# 或在 Header 中传递 token
```

#### **步骤 3：客户下载文件**

**方式 A：Header 传递 Token（推荐）**
```bash
curl -X GET http://localhost:8000/api/customer/files/550e8400-e29b-41d4-a716-446655440000/download/ \
  -H "X-Tenant-Token: a1b2c3d4-e5f6-7890-abcd-ef1234567890" \
  -o analysis.txt
```

**方式 B：URL 参数传递 Token**
```bash
curl -X GET "http://localhost:8000/api/customer/files/550e8400-e29b-41d4-a716-446655440000/download/?token=a1b2c3d4-e5f6-7890-abcd-ef1234567890" \
  -o analysis.txt
```

---

### **场景 3：前端浏览器下载**

```javascript
// 方式 1：直接打开链接（浏览器会自动处理）
const downloadUrl = `/api/customer/files/${uuid}/download/`;
window.open(downloadUrl, '_blank');

// 方式 2：使用 fetch + Blob
fetch(downloadUrl, {
    headers: {
        'X-Tenant-Token': uploadToken
    }
})
.then(response => response.blob())
.then(blob => {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
});

// 方式 3：在 <img> 标签中预览
<img src={`/api/customer/files/${uuid}/preview/`} 
     style={{ maxWidth: '100%' }}
/>
```

---

## 🔐 安全特性

### **1. 租户隔离**

```python
# 验证文件归属
if file.company_id != company.id:
    raise BizException(ERROR_DATA_NOT_FOUND, "文件不存在或无权访问")
```

**效果：**
- ✅ 租户 A 无法访问租户 B 的文件
- ✅ 即使知道 UUID，也无法跨租户访问

---

### **2. Token 验证**

```python
# 解密 Token
tenant_slug = TenantTokenCrypto.decrypt_tenant_slug(token)

# 验证租户存在
company = Company.objects.get(tenant_slug=tenant_slug)
```

**效果：**
- ✅ Token 加密防篡改
- ✅ 租户不存在时拒绝访问
- ✅ Token 可设置过期时间

---

### **3. 文件存在性检查**

```python
file_path = build_file_path(tenant_slug, file.storage_path)
if not os.path.exists(file_path):
    raise BizException(ERROR_DATA_NOT_FOUND, "文件不存在")
```

**效果：**
- ✅ 防止路径遍历攻击
- ✅ 确保文件真实存在

---

## 📊 接口对比

| 特性 | 内部接口 | 客户接口 |
|------|---------|---------|
| **路径** | `/api/files/{uuid}/download/` | `/api/customer/files/{uuid}/download/` |
| **认证方式** | Session/Cookie | X-Tenant-Token Header |
| **需要登录** | ✅ 是 | ❌ 否 |
| **租户隔离** | ✅ 自动 | ✅ Token 验证 |
| **适用场景** | 内部管理 | 客户上传/分享 |
| **安全性** | 高 | 高 |

---

## ⚠️ 注意事项

### **1. Token 安全**

```python
# ✅ 推荐：Header 传递
headers = {"X-Tenant-Token": token}

# ⚠️ 谨慎：URL 参数传递（可能记录在日志中）
url = f"/api/customer/files/{uuid}/download/?token={token}"
```

**建议：**
- ✅ 优先使用 Header 传递 Token
- ✅ HTTPS 传输加密
- ✅ 定期轮换 Token
- ❌ 不要在日志中打印完整 Token

---

### **2. CORS 配置**

如果前端跨域访问，需要配置 CORS：

```python
# settings.py
CORS_ALLOW_HEADERS = [
    'x-tenant-token',  # 允许 Token Header
    # ... 其他 headers
]
```

---

### **3. Nginx 配置（生产环境）**

如果使用 X-Accel-Redirect，需要配置 Nginx：

```nginx
location /files/ {
    internal;  # 禁止外部直接访问
    alias /path/to/storage/;
}
```

---

## 🎯 最佳实践

### **1. 为客户提供下载链接**

```python
# 上传成功后返回
{
    "data": {
        "file_info": {
            "uuid": "550e8400-...",
            "download_url": "/api/customer/files/550e8400-.../download/",
            "preview_url": "/api/customer/files/550e8400-.../preview/"
        }
    }
}

# 客户使用时添加 Token Header
```

---

### **2. 临时下载链接（可选增强）**

如果需要更安全的临时链接，可以：

```python
# 生成短期有效的签名
import hmac
import time

def generate_temp_download_url(uuid, tenant_slug, expiry_seconds=3600):
    timestamp = int(time.time()) + expiry_seconds
    signature = hmac.new(
        SECRET_KEY.encode(),
        f"{uuid}:{tenant_slug}:{timestamp}".encode(),
        hashlib.sha256
    ).hexdigest()
    
    return f"/api/customer/files/{uuid}/download/?ts={timestamp}&sig={signature}"
```

---

## 📝 总结

### **改进前**
- ❌ 必须登录才能下载
- ❌ 客户无法访问上传的文件
- ❌ 分享困难

### **改进后**
- ✅ 双重访问控制（登录 + Token）
- ✅ 客户可便捷下载文件
- ✅ 租户隔离保证安全
- ✅ 灵活的集成方式

---

**实施日期**: 2024-01-15  
**版本**: v1.1.0
