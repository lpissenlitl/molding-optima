<template>
  <div class="single-image-uploader">
    <el-upload
      class="avatar-uploader"
      action="#"
      :show-file-list="false"
      :before-upload="beforeUpload"
      :http-request="handleRequest"
      :disabled="disabled"
      :on-remove="handleRemove"
    >
      <!-- 已上传：显示图片 + 删除按钮 -->
      <div v-if="file_info" class="uploaded-wrapper">
        <img :src="file_info.url" class="avatar" />
        <div class="action-mask">
          <i class="el-icon-delete delete-btn" @click.stop="confirmRemove"></i>
        </div>
      </div>

      <!-- 未上传：显示加号 -->
      <i v-else class="el-icon-plus avatar-uploader-icon"></i>
    </el-upload>
  </div>
</template>

<script>
import { uploadFile } from "@/api"
import { getFilePreviewUrl } from "@/utils/assert"

export default {
  name: "SingleImageUploader",
  props: {
    value: {
      type: Object,
      default: null,
    },
    disabled: {
      type: Boolean,
      default: false,
    },
    businessId: {
      type: Number,
      default: 0,
    },
    businessType: {
      type: String,
      default: "",
    },
    usageType: {
      type: String,
      default: "",
    },
  },
  data() {
    return {
      file_info: null,
    }
  },
  watch: {
    value: {
      handler(val) {
        if (val && val.uuid) {
          this.file_info = {
            ...val,
            url: getFilePreviewUrl(val.uuid),
          }
        } else if (val && val.url) {
          this.file_info = {
            ...val,
            url: val.url,
          }
        } else {
          this.file_info = null
        }
      },
      deep: true,
      immediate: true,
    }
  },
  methods: {
    beforeUpload(file) {
      const isImage = file.type.startsWith("image/")
      const isValidExt = /\.(jpg|jpeg|png|gif|webp)$/i.test(file.name)
      if (!isImage || !isValidExt) {
        this.$message.error("仅支持 JPG/PNG/GIF/WEBP 格式的图片")
        return false
      }
      return true
    },
    async handleRequest({ file }) {
      try {
        const formData = new FormData()
        formData.append("file", file)
        formData.append("business_id", this.businessId)
        formData.append("business_type", this.businessType)
        formData.append("usage_type", this.usageType)

        const res = await uploadFile(formData)
        if (res.status === 0) {
          this.file_info = {
            ...res.data,
            name: res.data.filename || file.name,
            url: getFilePreviewUrl(res.data.uuid),
          }
          this.$emit("input", this.file_info)
          this.$notify.success("图片上传成功")
        } else {
          throw new Error(res.message || "上传失败")
        }
      } catch (error) {
        this.$message.error("上传失败，请重试")
        console.error("Upload error:", error)
      }
    },
    handleRemove() {
      // 这个方法实际上不会被调用，因为我们没用 file-list
      // 删除逻辑由 confirmRemove 处理
    },
    confirmRemove() {
      if (this.disabled) return
      this.$confirm("确定要删除这张图片吗？", "提示", {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        type: "warning",
      })
        .then(() => {
          this.file_info = null
          this.$emit("input", null)
          this.$message.success("已删除")
        })
        .catch(() => {})
    },
  },
}
</script>

<style scoped>
.single-image-uploader {
  display: inline-block;
}

.avatar-uploader ::v-deep .el-upload {
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  width: 180px;
  height: 180px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.avatar-uploader ::v-deep .el-upload:hover {
  border-color: #409eff;
}

.uploaded-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
}

.avatar {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.action-mask {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  opacity: 0;
  transition: opacity 0.2s;
  cursor: pointer;
}

.uploaded-wrapper:hover .action-mask {
  opacity: 1;
}

.delete-btn {
  color: white;
  font-size: 20px;
}

.delete-btn:hover {
  color: #ff4d4f;
}

.avatar-uploader-icon {
  font-size: 28px;
  color: #8c939d;
  width: 178px;
  height: 178px;
  line-height: 178px;
  text-align: center;
}
</style>