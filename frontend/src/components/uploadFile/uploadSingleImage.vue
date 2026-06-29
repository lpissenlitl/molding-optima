<template>
  <el-upload
    class="avatar-uploader"
    action="#"
    :show-file-list="false"
    :before-upload="beforeUpload"
    :http-request="uploadImage"
    :on-success="handleSuccess"
  >
    <img 
      v-if="file_url" 
      class="avatar"
      :src="file_url" 
    >
    <i 
      v-else 
      class="el-icon-plus avatar-uploader-icon"
    ></i>
  </el-upload>
</template>

<script>
import { uploadFile } from "@/api"
import { getFullFileUrl } from "@/utils/assert"

export default {
  props: {
    searchId: {
      type: Number,
      default: -1
    },
    searchType: {
      type: String,
      default: "media"
    },
    fileUrl: {
      type: String,
      default: ""
    },
  },
  data() {
    return {
      file_info: this.fileInfo,
      search_id: this.searchId,
      search_type: this.searchType,
      store_type: "mold_trial",
      file_url: ""
    }
  },
  watch: {
    fileUrl: function() {
      this.updateImageUrl()
    }
  },
  mounted() {
    this.updateImageUrl()
  },
  methods: {
    beforeUpload(file) {
      // const isJPG = file.type === 'image/jpeg';
      // const isLt2M = file.size / 1024 / 1024 < 2;

      // if (!isJPG) {
      //   this.$message.error('上传头像图片只能是 JPG 格式!');
      // }
      // if (!isLt2M) {
      //   this.$message.error('上传头像图片大小不能超过 2MB!');
      // }
      // return isJPG && isLt2M;
      return true
    },
    uploadImage(data) {
      console.log(data)
      let params = new FormData()
      params.append("file", data.file)
      params.append("search_id", this.search_id)
      params.append("search_type", this.search_type)
      params.append("store_type", this.store_type)

      uploadFile(params).then(res => {
        if (res.status === 0) {
          this.$notify({
            title: "上传成功",
            message: "图片上传成功！",
            type: "success"
          })

          this.file_url = getFullFileUrl(res.data.file_url)
          this.$emit("file-upload", res.data.file_url)
        }
      })
    },
    handleSuccess(res, file) {
      // this.imageUrl = URL.createObjectURL(file.raw);
    },
    updateImageUrl() {
      if (this.fileUrl == "@/image/mold_core.png") {
        this.file_url = require("@/image/mold_core.png")
      } else if (this.fileUrl == "@/image/mold_cavity.png") {
        this.file_url = require("@/image/mold_cavity.png")
      } else {
        this.file_url = getFullFileUrl(this.fileUrl)
      }
    }
  }
}
</script>

<style lang="css" scope>
.avatar-uploader .el-upload {
border: 1px dashed #d9d9d9;
border-radius: 6px;
cursor: pointer;
position: relative;
overflow: hidden;
}
.avatar-uploader .el-upload:hover {
border-color: #409EFF;
}
.avatar-uploader-icon {
font-size: 28px;
color: #8c939d;
width: 18rem;
height: 18rem;
line-height: 18rem;
text-align: center;
}
.avatar-uploader-icon-large {
font-size: 28px;
color: #8c939d;
width: 24rem;
height: 24rem;
line-height: 24rem;
text-align: center;
}
.avatar {
width: 18rem;
height: 18rem;
display: block;
}
.avatar-large {
width: 24rem;
height: 24rem;
display: block;
}
</style>