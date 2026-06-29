<template>
  <el-upload
    action="#"
    :multiple="false"
    :limit="2"
    :file-list="file_list"
    :show-file-list="false"
    :http-request="uploadFile"
    :on-preview="handlePreview"
    :before-remove="beforeRemove"
    :on-remove="handleRemove"
    :on-exceed="handleExceed"
  >
    <el-link 
      size="mini" 
      type="primary"
      :loading="upload_loading"
    >
      上传
    </el-link>
  </el-upload>
</template>

<script>
import { uploadMoldflowFile } from "@/api"
import { getFileDownloadUrl,getFilePreviewUrl } from "@/utils/assert"
import SparkMD5 from "spark-md5"

export default {
  name: "UploadPolymerFile",
  props: {
    moldflowId: {
      type: Number,
      default: -1
    },
    searchType: {
      type: String,
      default: "moldflow_file"
    },
    storeType: {
      type: String,
      default: "moldflow/file"
    },
  },
  data() {
    return {
      file_list: [],
      moldflow_id: this.moldflowId,
      search_type: this.searchType,
      store_type: this.storeType,
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
  methods: {
    uploadFile(data) {
      // 校验文件格式
      let file_type = data.file.name.split(".").at(-1)
      if (this.search_type == "moldflow_txt") {
        if (file_type != "txt") {
          return this.$message({
            type: "warning",
            message: "文件上传格式不对！"
          })
        }
      } else if (this.search_type == "moldflow_ppt") {
        if (!(["ppt", "pptx"].includes(file_type))) {
          return this.$message({
            type: "warning",
            message: "文件上传格式不对！"
          })
        }
      } else {
        return this.$message({
          type: "warning",
          message: "请上传正确格式的文件！"
        })
      }

      this.upload_loading = true
      let params = new FormData()
      if (data.file.size < this.boundary_size) {
        // 直接上传
        params.append("file", data.file)
        params.append("business_id", this.moldflow_id)
        params.append("business_type", "moldflow")
        params.append("usage_type", "moldflow")
        // params.append("search_type", this.search_type);
        // params.append("store_type", this.store_type);
        uploadMoldflowFile(params).then( res => {
          if (res.status === 0) {
            this.upload_loading = false
            let file_info =  {
              "id": res.data.id,
              // "search_id": res.data.search_id,
              "type": res.data.type,
              "name": res.data.filename,
              "uuid": res.data.uuid,
            }
            console.log(file_info)
            this.file_list.push(file_info)
            this.$emit("file-upload", file_info)
          } 
        })
      } else {
        const uploadBigFile = (chunk_list, total_hash) => {
          const uploadChunk = (index) => {
            let single_chunk_params = new FormData()
            single_chunk_params.append("business_id", this.moldflow_id)
            single_chunk_params.append("business_type", "moldflow")
            single_chunk_params.append("usage_type", "moldflow")
            single_chunk_params.append("filename", data.file.name)
            single_chunk_params.append("slice_total", chunk_list.length)
            single_chunk_params.append("slice_order", index + 1)
            single_chunk_params.append("file", chunk_list[index].chunk)
            single_chunk_params.append("slice_md5", chunk_list[index].hash)
            single_chunk_params.append("finally_md5", total_hash)

            uploadMoldflowFile(single_chunk_params).then(res => {
              if (res.status === 0) {
                this.upload_loading = false
                if (res.data.is_completed) {   
                  let file_info =  {
                    "id": res.data.id,
                    "type": res.data.type,
                    "name": res.data.filename,
                    // "search_id": res.data.search_id,
                    // "search_type": res.data.search_type,
                    // "name": res.data.filename,
                    "uuid": res.data.uuid,
                  }
                  this.file_list.push(file_info)
                  this.$emit("file-upload", file_info)
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
          const chunk_list = []
          let current = 0
          let blobSlice = File.prototype.slice || File.prototype.mozSlice || File.prototype.webkitSlice
          while (current < data.file.size) {
            const chunk = blobSlice.call(data.file, current, current + this.chunk_size)
            chunk_list.push({ chunk, size: chunk.size })
            current += chunk.size
          }
          
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
      window.open(getFileDownloadUrl(file.url))
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
