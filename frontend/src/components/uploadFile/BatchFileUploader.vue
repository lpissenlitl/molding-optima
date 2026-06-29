<template>
  <div class="upload-files">
    <!-- 上传触发区 -->
    <el-upload
      ref="uploader"
      action="#"
      :auto-upload="false"
      :multiple="true"
      :file-list="pendingFileList"
      :http-request="handleRequest"
      :before-upload="beforeUpload"
      :on-change="handleChange"
      list-type="text"
    >
      <el-button size="small" type="primary" icon="el-icon-upload">
        选择文件
      </el-button>
      <template #tip>
        <div class="el-upload__tip">
          单个文件 ≤{{ maxFileSize / 1024 / 1024 }}MB
        </div>
      </template>
    </el-upload>
    <!-- 文件列表 -->
    <div v-for="file in displayFileList" :key="file.uid" class="file-item">
      <div class="file-info">
        <!-- 文件图标 + 名称 -->
        <div class="file-icon">
          <i class="el-icon-document"></i>
        </div>
        <div class="file-meta">
          <div class="filename">
            {{ file.filename }}
          </div>
          <div class="size">
            {{ formatFileSize(file.size) }}
          </div>
        </div>
      </div>
      <!-- 上传中 -->
      <div v-if="file.uploading" class="action-area">
        <el-progress
          :percentage="file.percentage || 0"
          :stroke-width="12"
          style="width: 120px; margin-right: 8px"
        />
        <el-button type="text" size="mini" @click="abortUpload(file)">
          取消
        </el-button>
      </div>
      <!-- 上传失败 -->
      <div v-else-if="file.error" class="action-area">
        <el-button type="text" size="mini" @click="retryUpload(file)">
          重试
        </el-button>
        <el-button type="danger" size="mini" @click="handleRemove(file)">
          删除
        </el-button>
      </div>
      <!-- 上传成功 -->
      <div v-else class="action-area">
        <el-button type="success" size="mini" @click="handleDownload(file)">
          下载
        </el-button>
        <el-button type="danger" size="mini" @click="handleRemove(file)">
          删除
        </el-button>
      </div>
    </div>
  </div>
</template>

<script>
import { uploadFile, deleteFile } from "@/api"
import { getFileDownloadUrl } from "@/utils/assert"
import SparkMD5 from "spark-md5"

export default {
  name: "BatchFileUploader",
  props: {
    fileList: {
      type: Array,
      required: true,
      default: () => [],
    },
    businessId: {
      type: Number,
      default: 0
    },
    businessType: {
      type: String,
      default: ""
    },
    usageType: {
      type: String,
      default: ""
    },
    maxFileSize: {
      // 自定义最大文件大小（默认 100MB）
      type: Number,
      default: 100 * 1024 * 1024 // 100MB
    },
    acceptMimeTypes: {
      // 自定义 MIME 类型白名单（可选）
      type: Array,
      default: () => [] // 空数组表示不限制
    }
  },
  data() {
    return {
      file_list: this.fileList,
      uploading_files: {},
      chunk_size: 8 * 1024 * 1024, // 8MB 分片
    }
  },
  computed: {
    displayFileList() {
      const existing = this.file_list.map((f) => ({
        ...f,
        uid: f.id || f.uuid,
        uploading: false,
        error: null,
      }))

      const uploading = Object.values(this.uploading_files).map((f) => ({
        ...f,
        status: f.error ? "fail" : "uploading",
      }))

      return [...existing, ...uploading]
    },
    pendingFileList() {
      return Object.values(this.uploading_files).map((f) => ({
        ...f,
        status: f.error ? "fail" : "uploading",
      }))
    }
  },
  watch: {
    fileList: {
      handler() {
        this.file_list = this.fileList
      },
      deep: true
    }
  },
  methods: {
    formatFileSize(bytes) {
      if (bytes === 0) return "0 Bytes"
      const k = 1024
      const sizes = ["Bytes", "KB", "MB", "GB"]
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i]
    },
    beforeUpload(file) {
      // MIME 类型校验（可选）
      if (this.acceptMimeTypes.length > 0 && !this.acceptMimeTypes.includes(file.type)) {
        this.$message.error(`仅支持以下格式：${this.acceptMimeTypes.join(", ")}`)
        return false
      }

      // 大小校验
      if (file.size > this.maxFileSize) {
        this.$message.error(`文件大小不能超过 ${this.maxFileSize / 1024 / 1024}MB`)
        return false
      }

      return true
    },
    handleChange(file, file_list) {
      if (file.status === "ready") {
        const uid = file.uid
        this.$set(this.uploading_files, uid, {
          ...file,
          uploading: true,
          percentage: 0,
          error: null,
        })
        this.handleRequest({ file, uid })
      }
    },
    async handleRequest({ file, uid }) {
      const file_raw = file.raw
      try {
        if (file_raw.size <= this.chunk_size) {
          await this.uploadSmallFile(file_raw, uid)
        } else {
          await this.uploadBigFile(file_raw, uid)
        }
      } catch (error) {
        this.$set(this.uploading_files, uid, {
          ...this.uploading_files[uid],
          uploading: false,
          error: error.message || "上传失败，请重试",
        })
      }
    },
    async uploadSmallFile(file, uid) {
      try {
        const params = new FormData()
        params.append("file", file)
        params.append("business_id", this.businessId)
        params.append("business_type", this.businessType)
        params.append("usage_type", this.usageType)

        const res = await uploadFile(params)
        if (res.status === 0) {
          this.file_list.push(res.data)
          this.$delete(this.uploading_files, uid)
        }
      } catch (error) {
        console.error("Upload failed:", error)
      }
    },
    async uploadChunkWithRetry(params, max_retries = 3) {
      let last_error
      for (let attempt = 1; attempt <= max_retries; attempt++) {
        try {
          const res = await uploadFile(params)
          if (res.status === 0) {
            return res
          } else {
            last_error = new Error(res.msg || `Chunk upload failed (attempt ${attempt})`)
            this.$message.warning(`分片上传失败，${attempt < max_retries ? "即将重试..." : "重试次数已用完"}`)
          }
        } catch (error) {
          last_error = error
        }
      }
      throw last_error
    },
    async uploadBigFile(file, uid) {
      const { chunk_list, finally_md5 } = await this.getChunkInfo(file)
      const total_chunks = chunk_list.length

      for (let i = 0; i < total_chunks; i++) {
        const params = new FormData()
        params.append("business_id", this.businessId)
        params.append("business_type", this.businessType)
        params.append("usage_type", this.usageType)
        params.append("filename", file.name)
        params.append("slice_total", total_chunks)
        params.append("slice_order", i + 1)
        params.append("file", chunk_list[i].chunk)
        params.append("slice_md5", chunk_list[i].md5)
        params.append("finally_md5", finally_md5)

        try {
          const res = await this.uploadChunkWithRetry(params)
          if (res.status === 0) {
            this.updateProgress(uid, Math.round(((i + 1) / total_chunks) * 100))
            if (res.data?.is_completed) {
              this.file_list.push(res.data)
              this.$delete(this.uploading_files, uid)
            }
          }
        } catch (error) {
          console.error("Upload failed:", error)
          throw new Error("文件上传失败，请检查网络或稍后再试")
        }
      }
    },
    readFileAsArrayBuffer(blob) {
      return new Promise((resolve, reject) => {
        const reader = new FileReader()
        reader.onload = () => resolve(reader.result)
        reader.onerror = () => reject(new Error("Failed to read file"))
        reader.readAsArrayBuffer(blob)
      })
    },
    async getChunkInfo(file) {
      const chunk_list = []
      let current = 0
      const blobSlice = File.prototype.slice ||
                        File.prototype.mozSlice ||
                        File.prototype.webkitSlice
      while (current < file.size) {
        const chunk = blobSlice.call(file, current, current + this.chunk_size)
        chunk_list.push({ chunk, size: chunk.size })
        current += this.chunk_size
      }

      const md5 = new SparkMD5.ArrayBuffer()
      for (let i = 0; i < chunk_list.length; i++) {
        const array_buffer = await this.readFileAsArrayBuffer(chunk_list[i].chunk)
        const chunk_md5 = SparkMD5.ArrayBuffer.hash(array_buffer)
        chunk_list[i].md5 = chunk_md5
        md5.append(array_buffer)
      }

      const finally_md5 = md5.end()
      return { chunk_list, finally_md5 }
    },
    updateProgress(uid, percent) {
      const file = this.uploading_files[uid]
      if (file) {
        this.$set(this.uploading_files, uid, {
          ...file,
          percentage: percent,
        })
      }
    },
    abortUpload(file) {
      this.$delete(this.uploading_files, file.uid)
    },
    retryUpload(file) {
      this.$set(this.uploading_files, file.uid, {
        ...file,
        error: null,
        uploading: true,
        percentage: 0,
      })
      this.handleRequest({ file: file, uid: file.uid })
    },
    async handleRemove(file) {
      try {
        await this.$confirm("确定删除该文件？", "提示", {
          confirmButtonText: "确定",
          cancelButtonText: "取消",
          type: "warning",
        })

        if (file.uploading || file.error) {
          this.$delete(this.uploading_files, file.uid)
        } else {
          const index = this.file_list.findIndex(f => f.uuid === file.uuid || f.id === file.uid)
          if (index !== -1) {
            this.file_list.splice(index, 1)
            await deleteFile(file.uuid)
            this.$message.success("删除成功!")
          }
        }
      } catch {
        this.$message.info("已取消删除")
      }
    },
    handleDownload(file) {
      window.location.href = getFileDownloadUrl(file.uuid)
    }
  },
}
</script>

<style scoped lang="scss">
.upload-files {
  .el-upload--text {
    margin-bottom: 16px;
  }

  .file-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 0;
    border-bottom: 1px solid #eee;

    &:last-child {
      border-bottom: none;
    }
  }

  .file-info {
    display: flex;
    align-items: center;
    gap: 12px;
    min-width: 0;
  }

  .file-icon {
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #f5f7fa;
    border-radius: 4px;
    color: #909399;
  }

  .file-meta {
    .filename {
      font-size: 14px;
      font-weight: 500;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      max-width: 200px;
      color: #303133;   // Element Plus 默认文本色
    }
    .size {
      font-size: 12px;
      color: #909399;
    }
  }

  .action-area {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
  }

  @media (max-width: 480px) {
    .file-info {
      flex-direction: column;
      align-items: flex-start;
      gap: 6px;
    }
    .file-meta {
      width: 100%;
    }
    .action-area {
      width: 100%;
      justify-content: flex-end;
    }
  }
}
</style>