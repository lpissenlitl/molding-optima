<template>
  <div class="upload-trial-videos">
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
        选择视频文件
      </el-button>
      <template #tip>
        <div class="el-upload__tip">
          支持 MP4 格式，单个文件 ≤200MB
        </div>
      </template>
    </el-upload>
    <!-- 自定义文件项列表 -->
    <div v-for="file in displayFileList" :key="file.uid" class="video-item">
      <div class="video-info">
        <!-- 已上传视频：可播放 -->
        <video
          v-if="file.url && !file.uploading && !file.error"
          :src="file.url"
          class="video-preview"
          controls
          preload="metadata"
        />
        <!-- 上传中/失败/未加载：占位图 -->
        <div v-else class="placeholder">
          <i class="el-icon-video-camera"></i>
          <span class="filename">{{ file.name }}</span>
        </div>
        <div class="video-meta">
          <span class="size">{{ formatFileSize(file.size) }}</span>
        </div>
      </div>
      <!-- 上传中状态 -->
      <div v-if="file.uploading" class="action-area">
        <el-progress
          :percentage="file.percentage || 0"
          :stroke-width="12"
          style="width: 120px; margin-right: 8px"
        />
        <el-button
          type="text"
          size="mini"
          @click="abortUpload(file)"
        >
          取消
        </el-button>
      </div>
      <!-- 上传失败状态 -->
      <div v-else-if="file.error" class="action-area">
        <el-button
          type="text"
          size="mini"
          @click="retryUpload(file)"
        >
          重试
        </el-button>
        <el-button
          type="danger"
          size="mini"
          @click="handleRemove(file)"
        >
          删除
        </el-button>
      </div>
      <!-- 已上传成功状态 -->
      <div v-else class="action-area">
        <el-button
          type="danger"
          size="mini"
          @click="handleRemove(file)"
        >
          删除
        </el-button>
      </div>
    </div>
  </div>
</template>

<script>
import { uploadFile, deleteFile } from "@/api"
import { getFilePreviewUrl } from "@/utils/assert"
import SparkMD5 from "spark-md5"

export default {
  name: "UploadTrialVideos",
  props: {
    // ⚠️ 必须传入一个可变的响应式数组（如父组件 data 中的数组）
    fileList: {
      type: Array,
      required: true,
      default: () => [],
    },
    businessId: {
      type: Number,
      default: -1,
    },
    businessType: {
      type: String,
      default: "trial_session",
    },
    usageType: {
      type: String,
      default: "trial_record",
    },
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
      // 1. 已上传的文件（来自 prop）
      const existing = this.file_list.map((f) => ({
        ...f,
        uid: f.id || f.uuid, // 统一 uid
        uploading: false,
        error: null,
        url: getFilePreviewUrl(f.uuid),
      }))

      // 2. 正在上传或失败的文件（本地状态）
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
      if (!["video/mp4"].includes(file.type)) {
        this.$message.error("仅支持 MP4 格式视频")
        return false
      }
      if (file.size > 200 * 1024 * 1024) {
        this.$message.error("视频大小不能超过 200MB")
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
          this.file_list.push({
            ...res.data,
            "url": getFilePreviewUrl(res.data.uuid),
          })
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
            this.$message.warning(`分片上传失败，${attempt < max_retries ? "即将重试..." : "重试次数已用完，请检查网络或稍后再试"}`)
          }
        } catch (error) {
          last_error = error
        }
      }
      throw last_error // 所有重试均失败，抛出最后一次错误
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
            console.log("res data", res.data)
            if (res.data?.is_completed) {
              this.file_list.push({
                ...res.data,
                "url": getFilePreviewUrl(res.data.uuid),
              })
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
      // 获取分片信息
      const chunk_list = []
      let current = 0
      let blobSlice = File.prototype.slice || File.prototype.mozSlice || File.prototype.webkitSlice
      while (current < file.size) {
        const chunk = blobSlice.call(file, current, current + this.chunk_size)
        chunk_list.push({ chunk, size: chunk.size })
        current += this.chunk_size
      }

      // 串行计算每个分片的MD5 和 文件MD5
      const md5 = new SparkMD5.ArrayBuffer()
      for (let i = 0; i < chunk_list.length; i++) {
        try {
          const array_buffer = await this.readFileAsArrayBuffer(chunk_list[i].chunk)
          const chunk_md5 = SparkMD5.ArrayBuffer.hash(array_buffer)
          chunk_list[i].md5 = chunk_md5
          md5.append(array_buffer)
        } catch (error) {
          console.error("MD5 calculation failed:", error)
          throw new Error("MD5计算失败，请检查网络或稍后再试")
        }
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
        await this.$confirm("确定删除该视频？", "提示", {
          confirmButtonText: "确定",
          cancelButtonText: "取消",
          type: "warning",
        })

        if (file.uploading || file.error) {
          // 本地任务：直接删除
          this.$delete(this.uploading_files, file.uid)
        } else {
          // 已上传：服务器删除
          const index = this.file_list.findIndex(f => f.uuid === f.uuid || f.id === f.uid)
          if (index !== -1) {
            this.file_list.splice(index, 1)
            const res = await deleteFile(file.uuid)
            if (res.status === 0) {
              this.$message({ type: "success", message: "删除成功!" })
            }
          }
        }
      } catch (error) {
        this.$message({ type: "info", message: "已取消删除" })   
      }
    },
  },
}
</script>

<style scoped lang="scss">.upload-trial-videos {
  .el-upload--text {
    margin-bottom: 16px;
  }

  .video-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 0;
    border-bottom: 1px solid #eee;

    &:last-child {
      border-bottom: none;
    }
  }

  .video-info {
    display: flex;
    align-items: center;
    gap: 12px;
    min-width: 0;
    // 默认：横向排列（桌面/平板）
  }

  // 视频预览容器：统一用 aspect-ratio 保持比例
  .video-preview,
  .placeholder {
    width: 100%;
    max-width: 120px;
    aspect-ratio: 16 / 9; // 16:9 横屏比例（主流视频）
    border-radius: 4px;
    flex-shrink: 0;
  }

  .video-preview {
    object-fit: cover;
    background: #000;
  }

  .placeholder {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    background: #f5f7fa;
    color: #909399;
    font-size: 12px;
    text-align: center;

    .filename {
      max-width: 90%;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      margin-top: 4px;
      font-size: 11px;
    }
  }

  .video-meta {
    display: flex;
    flex-direction: column;
    gap: 4px;
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

  /* 响应式：小屏设备（手机） */
  @media (max-width: 480px) {
    .video-info {
      flex-direction: column;
      align-items: flex-start;
      gap: 8px;
      width: 100%;
    }

    .video-meta {
      width: 100%;
      flex-direction: row;
      justify-content: space-between;
    }

    .action-area {
      width: 100%;
      justify-content: flex-end;
    }

    // 可选：进一步缩小视频最大宽度
    .video-preview,
    .placeholder {
      max-width: 100px;
    }
  }
}
</style>