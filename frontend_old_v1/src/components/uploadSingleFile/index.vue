<template>
  <el-upload
    action="#"
    :multiple="false"
    :limit="1"
    :file-list="fileList"
    :before-upload="beforeUpload"
    :http-request="uploadFile"
    :on-preview="handlePreview"
    :on-remove="handleRemove"
  >
    <el-button 
      size="mini" 
      type="primary"
      style="width:10rem"
      :loading="loading"
    >
      点击上传
    </el-button>
    <div slot="tip" class="el-upload__tip" v-if="searchType != 'mold_flow_ppt'">
      上传文件，可支持png/jpg/pdf等格式
    </div>
  </el-upload>
</template>

<script>
import { uploadFile, deleteFile } from "@/api"
import { getFullImageUrl } from '@/utils/assert'

export default {
  name: "UploadSingleFile",
  props: {
    value: {
      type: Object,
      default: () => {}
    },
    searchType: {
      type: String,
      default: ""
    },
    allowDelete: {
      type: Boolean,
      default: true
    }
  },
  data() {
    return {
      fileList: [],
      loading: false,
    }
  },
  mounted() {

  },
  methods: {
	  beforeUpload (file) {
      const isLt20M = file.size / 1024 / 1024 < 200;
      const fileType = file.name.substring(file.name.lastIndexOf('.') + 1).toLowerCase()
      const isJpg = fileType == 'jpg'
      const isPng = fileType == 'png'
      const isJpeg = fileType == 'jpeg'
      const isPdf = fileType == 'pdf'
      const isPpt = fileType == 'ppt' || fileType == 'pptx'
      if (this.searchType == "mold_flow_ppt") {
        if (!isPpt) {
          this.$message.error('只能上传ppt格式的文件!');
            return false;
        }
      } else if (!isJpg && !isPng && !isJpeg && !isPdf) { 
          this.$message.error('只能上传png或jpg格式或pdf格式的文件!');
          return false;
      }
      if (!isLt20M) {
          this.$message.error('上传文件大小不能超过20MB哦!');
          return false;
      }
    },
    uploadFile(data) {
      this.loading = true
      let params = new FormData()
      params.append("file", data.file)
      params.append("search_type", this.searchType)
      // 上传模流ppt时，带着project_id
      if (this.searchType == "mold_flow_ppt") {
        params.append("search_id", this.value.id)
        params.append("mold_flow_no", this.value.mold_flow_no)
      }
      uploadFile(params).then( res => {
        if (res.status === 0) {
          this.loading = false
          this.$message({ message: "上传成功！", type: 'success' })
          if (this.searchType == "mold_flow_ppt") {
            let file_info = []
            file_info = res.data
            this.$emit("upload-file-info", file_info)
          } else {
            let file_info = {
              id: res.data.id,
              name: res.data.name,
              url: res.data.url
            }
            this.fileList.push({
              id: file_info.id,
              name: file_info.name,
              url: getFullImageUrl(file_info.url)
            })
            this.$emit("upload-file-info", file_info)
          }
        } 
      })
    },
    handlePreview(file) {
      window.open(file.url)
    },
    handleRemove(file, fileList) {
      if (file.id && this.allowDelete) {
        deleteFile(file.id)
        .then( res => {
          if (res.status === 0) {
            this.$message({ message: "删除成功！", type: "success" })
            this.fileList = fileList
            this.$emit("upload-file-info", null)
          }
        })
      } else {
        this.fileList = fileList
        this.$emit("upload-file-info", null)
      }
    },
  },
  watch: {
    value: {
      handler(newV, oldV) {
        this.fileList = []
        if (newV.url) {
          this.fileList.push({
            id: newV.id,
            name: newV.name,
            url: getFullImageUrl(newV.url)
          })
        }
      },
      deep: true
    }
  }
}
</script>

<style>

</style>