<template>
  <div class="upload-images">
    <el-upload
      action="#"
      class="avatar-uploader el-upload--text"
      multiple
      :file-list="file_list"
      :http-request="uploadFile"
      :on-progress="uploadVideoProcess"
      :before-upload="beforeUpload"
    >
      <el-button size="small" type="primary">
        点击上传
      </el-button>
      <div slot="file" slot-scope="{ file }">
        <div>
          <video
            :src="file.url"
            class="avatar video-avatar"
            controls="controls"
          >您的浏览器不支持视频播放</video>
          <el-progress
            v-if="upload_progress == true"
            type="circle"
            :percentage="upload_percent"
            style="margin-top:30px;"
          ></el-progress>
        </div>
        <div style="height:4px" />
        <div>
          <el-button
            class="video-btn"
            @click="handleRemove(file)"
            size="small"
            type="danger"
          >
            移除视频文件
          </el-button>
        </div>
      </div>
    </el-upload>
  </div>
</template>

<script>
import { uploadFile } from "@/api"
import { getFullFileUrl } from "@/utils/assert"
import SparkMD5 from "spark-md5"

export default {
  name: "UploadTrialVideos",
  props: {
    searchId: {
      type: Number,
      default: -1
    },
    searchType: {
      type: String,
      default: "media"
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
      store_type: "problem/videos",
      chunk_size: 8 * 1024 * 1024, //文件分片上传，每块8M
      upload_progress: false , //是否显示进度条
      upload_percent: "", //进度条的进度
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
  methods: {
    //上传前回调
    beforeUpload (file) {
      //'video/ogg', 'video/flv', 'video/avi', 'video/wmv', 'video/rmvb'
      if (["video/mp4"].indexOf(file.type) == -1) { 
        this.$alert("只能上传 mp4 格式文件！", "提示！", {
          confirmButtonText: "确定"
        })
        return false
      }
      const isLt200M = file.size / 1024 / 1024 < 200
      if (!isLt200M) {
        this.$alert("上传视频大小不能超过200MB！", "提示！", {
          confirmButtonText: "确定"
        })
        return false
      }
      return true
    },
    //进度条
    uploadVideoProcess (event, file, file_list) {
      this.upload_progress = true
      file.percentage = event.percentage
      this.upload_percent = event.percentage
    },
    uploadFile(data) {
      // 上传视频
      let params = new FormData()

      // 考虑大文件的情况
      if (data.file.size < this.chunk_size) {
        // 直接上传
        params.append("file", data.file)
        params.append("search_id", this.search_id)
        params.append("search_type", this.search_type)
        params.append("store_type", this.store_type)
        uploadFile(params).then( res => {
          if (res.status === 0) {
            this.$message({ message: "上传成功！", type: "success" })

            this.file_list.push({
              "id": res.data.id,
              "search_id": res.data.search_id,
              "search_type": res.data.search_type,
              "name": res.data.filename,
              "url": getFullFileUrl(res.data.file_url),
            })
          } else {
            //回调上传失败事件
            data.onError(res.msg)
          }
        }).catch(error => data.onError(error))
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
                  data.onProgress({ percentage: 100 })
                  this.upload_progress = false

                  this.file_list.push({
                    "id": res.data.id,
                    "search_id": res.data.search_id,
                    "search_type": res.data.search_type,
                    "name": res.data.filename,
                    "url": getFullFileUrl(res.data.file_url),
                  })
                } else if (index < chunk_list.length - 1) {
                  uploadChunk(index + 1)
                  data.onProgress({ percentage: ~~((index + 1) * 100.0 / chunk_list.length) })
                }
              } else {
                data.onError(res.msg)
              }
            }).catch(error => data.onError(error))
          }
  
          uploadChunk(0)
          data.onProgress({ percentage: 0 }) // 显示进度条
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
    handleRemove(file) {
      this.$confirm("此操作将删除该视频, 是否继续?", "提示", {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        type: "warning"
      }).then(() => {
        // 移除视频
        let file_index = this.file_list.indexOf(file)
        if (file_index != -1) {
          this.file_list.splice(file_index, 1)
        }
        this.$message({ type: "success", message: "删除成功！" })
      }).catch(() => {
        this.$message({ type: "info", message: "已取消删除" })
      })
    },
  },
}
</script>

<style lang="scss" scoped>
.avatar-uploader .el-upload {
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
}
.avatar-uploader .el-upload:hover {
  border-color: #409eff;
}
.avatar-uploader-icon {
  font-size: 28px;
  color: #8c939d;
  width: 178px;
  height: 178px;
  line-height: 178px;
  text-align: center;
}
.video-avatar {
  width: 100%;
  height: 100%;
}
</style>
