<template>
  <div style="display: inline-block">
    <!-- 隐藏的文件输入框 -->
    <input
      ref="fileInput"
      type="file"
      :accept="accept"
      style="display: none"
      @change="handleFileChange"
    />
    <!-- 透传所有 attrs 和 listeners 给 el-button -->
    <el-button
      v-bind="$attrs"
      :loading="uploading"
      @click="triggerUpload"
      v-on="$listeners"
    >
      <slot>{{ uploading ? '上传中...' : '上传文件' }}</slot>
    </el-button>
  </div>
</template>

<script>
import { uploadFile } from "@/api"
import SparkMD5 from "spark-md5"

export default {
  name: "FileUploadButton",
  inheritAttrs: false, // 防止 accept 等属性落到 el-button 上
  props: {
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
    accept: {
      type: String,
      default: "*"
    },
    maxSize: {
      type: Number,
      default: 200 * 1024 * 1024 // 10MB
    },
    allowedTypes: {
      type: Array,
      default: () => ["txt", "ppt", "pptx"] // 如 ['application/pdf']
    }
  },
  data() {
    return {
      uploading: false,
      chunk_size: 8 * 1024 * 1024, // 8MB 分片
    }
  },
  methods: {
    triggerUpload() {
      if (this.uploading) return
      this.$refs.fileInput.click()
    },
    async handleFileChange(e) {
      const file = e.target.files[0]
      if (!file) return
      // 校验文件类型（如果提供了 allowedTypes）
      const file_type = file.name.split(".").at(-1)
      if (this.allowedTypes.length && !this.allowedTypes.includes(file_type)) {
        this.$message.error(`仅支持以下格式：${this.allowedTypes.join(", ")}`)
        this.resetInput()
        return
      }

      // 校验大小
      if (file.size > this.maxSize) {
        this.$message.error(`文件不能超过 ${(this.maxSize / 1024 / 1024).toFixed(1)}MB`)
        this.resetInput()
        return
      }

      await this.uploadFile(file)
    },
    async uploadFile(file) {
      this.uploading = true
      try {
        if (file.size <= this.chunk_size) {
          await this.uploadSmallFile(file)
        } else {
          await this.uploadBigFile(file)
        }
      } catch (error) {
        console.error("Upload error:", error)
        this.$message.error("上传失败：" + (error.message || "请重试"))
      } finally {
        this.uploading = false
        this.resetInput()
      }
    },
    async uploadSmallFile(file) {
      try {
        const params = new FormData()
        params.append("file", file)
        params.append("business_id", this.businessId)
        params.append("business_type", this.businessType)
        params.append("usage_type", this.usageType)

        const res = await uploadFile(params)
        if (res.status === 0) {
          this.$message({ message: "上传成功", type: "success" })
          this.$emit("upload-success", res.data)
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
    async uploadBigFile(file) {
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
          console.log("Chunk upload response:", res.data)
          if (res.status === 0 && res.data?.is_completed) {
            this.$message({ message: "上传成功", type: "success" })
            this.$emit("upload-success", res.data)
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
    resetInput() {
      this.$refs.fileInput.value = ""
    }
  }
}
</script>