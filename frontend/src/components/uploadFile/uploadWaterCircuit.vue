<template>
  <el-upload
    action="#"
    :multiple="false"
    :limit="2"
    :file-list="file_list"
    :before-upload="beforeUpload"
    :http-request="uploadFile"
    :on-preview="handlePreview"
    :on-exceed="handleExceed"
  >
    <el-button 
      size="mini" 
      type="primary"
      style="width:10rem"
      :loading="upload_loading"
    >
      点击上传
    </el-button>
    <div slot="tip" class="el-upload__tip">
      上传文件，可支持png/jpg/pdf等格式
    </div>
  </el-upload>
</template>
  
<script>
import { uploadFile, deleteFile } from "@/api"
import { getFullFileUrl } from "@/utils/assert"
import SparkMD5 from "spark-md5"
  
export default {
  name: "UploadWaterCircuit",
  props: {
    searchId: {
      type: Number,
      default: -1
    },
    searchType: {
      type: String,
      default: "mold"
    },
    fileList: {
      type: Array,
      default: () => {
        return []
      }
    }
  },
  data() {
    return {
      file_list: this.fileList,
      search_id: this.searchId,
      search_type: this.searchType,
      store_type: "water_flow",
      upload_loading: false,
      chunk_size: 4 * 1024 * 1024,
      boundary_size: 10 * 1024 * 1024
    }
  },
  watch: {
    fileList: {
      handler: function() {
        this.file_list = this.fileList
      },
      deep: true
    }
  },
  mounted() {

  },
  methods: {
    beforeUpload (file) {
      const isLt20M = file.size / 1024 / 1024 < 200
      const fileType = file.name.substring(file.name.lastIndexOf(".") + 1).toLowerCase()
      const isJpg = fileType == "jpg"
      const isPng = fileType == "png"
      const isJpeg = fileType == "jpeg"
      const isPdf = fileType == "pdf"
      const isPpt = fileType == "ppt" || fileType == "pptx"
      if (!isJpg && !isPng && !isJpeg && !isPdf) { 
        this.$message.error("只能上传png或jpg格式或pdf格式的文件!")
        return false
      }
      if (!isLt20M) {
        this.$message.error("上传文件大小不能超过20MB哦!")
        return false
      }
      return true
    },
    uploadFile(data) {
      this.upload_loading = true
      let params = new FormData()
  
      // 考虑大文件的情况
      if (data.file.size < this.boundary_size) {
        // 直接上传
        params.append("file", data.file)
        params.append("search_id", this.search_id)
        params.append("search_type", this.search_type)
        params.append("store_type", this.store_type)
        uploadFile(params).then( res => {
          if (res.status === 0) {
            this.upload_loading = false
            this.$message({ message: "上传成功！", type: "success" })

            this.file_list.push({
              "id": res.data.id,
              "search_id": res.data.search_id,
              "search_type": res.data.search_type,
              "name": res.data.filename,
              "url": res.data.file_url,
            })
          } 
        })
      } else {
        // 分片上传
        const uploadBigFile = (chunk_list, total_hash) => {
          const uploadChunk = (index) => {
            params.append("search_id", this.search_id)
            params.append("search_type", this.search_type)
            params.append("store_type", this.store_type)
            params.append("filename", data.file.name)
            params.append("slice_total", chunk_list.length)
            params.append("slice_order", index + 1)
            params.append("file", chunk_list[index].chunk)
            params.append("slice_md5", chunk_list[index].hash),
            params.append("finally_md5", total_hash)
  
            uploadFile(params).then(res => {
              if (res.status === 0) {
                if (res.data.file_url) {
                  this.upload_loading = false
                  this.$message({ message: "上传成功！", type: "success" })

                  this.file_list.push({
                    "id": res.data.id,
                    "search_id": res.data.search_id,
                    "search_type": res.data.search_type,
                    "name": res.data.filename,
                    "url": res.data.file_url,
                  })
                } else if (index < chunk_list.length - 1) {
                  uploadChunk(index + 1)
                }
              } else {
                data.onError(res.msg)
              }
            }).catch(error => data.onError(error))
          }
  
          uploadChunk(0)
        }
  
        const getChunkInfo = (data, callBack) => {
          // 分割文件
          const chunk_list = []
          let current = 0
          let blobSlice = File.prototype.slice || File.prototype.mozSlice || File.prototype.webkitSlice
          while (current < data.file.size) {
            const chunk = blobSlice.call(data.file, current, current + this.chunk_size)
            chunk_list.push({ chunk, size: chunk.size })
            current += chunk.size
          }
            
          // 计算分割文件 md5
          const fileReader  = new FileReader()
          const md5 = new SparkMD5.ArrayBuffer()
          let index = 0
          const loadFile = () => {
            const chunk = chunk_list[index].chunk
            fileReader.readAsArrayBuffer(chunk)
          }
          loadFile()
          fileReader.onload = (e) => {
            const array_buffer = e.target.result
            const chunk_hash = SparkMD5.ArrayBuffer.hash(array_buffer)
            chunk_list[index].hash = chunk_hash
            md5.append(array_buffer)
            if (index < chunk_list.length - 1) {
              index += 1
              loadFile()
            } else {
              const total_hash = md5.end()
              if (callBack) {
                callBack(chunk_list, total_hash)
              }
            }
          }
        }
  
        getChunkInfo(data, uploadBigFile)
      }
    },
    handlePreview(file) {
      window.open(getFullFileUrl(file.url))
    },
    async beforeRemove(file, file_list) {
      let allow_delete = false
      await this.$confirm("此操作将删除该文件, 是否继续?", "提示", {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        type: "warning"
      }).then(() => {
        allow_delete =  true
      })
      return allow_delete
    },
    handleRemove(file, file_list) {
      this.$message({ message: "删除成功！", type: "success" })
      this.$emit("file-update", file_list)
    },
    handleExceed(file, file_list) {
      this.$message.warning("超过上传文件数量！")
    },
  }
}
</script>
  
  <style>
  
  </style>