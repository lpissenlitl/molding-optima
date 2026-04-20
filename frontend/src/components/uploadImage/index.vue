<template>
  <el-upload
    class="avatar-uploader"
    action="#"
    :show-file-list="false"
    :http-request="uploadImage"
    :on-success="handleAvatarSuccess"
    :before-upload="beforeAvatarUpload"
  >
    <img 
      v-if="imageUrl" 
      :class="[image_size == 'normal' ? 'avatar' : 'avatar-large']"
      :src="imageUrl" 
    >
    <i 
      v-else 
      class="el-icon-plus" 
      :class="[image_size == 'normal' ? 'avatar-uploader-icon' : 'avatar-uploader-icon-large']"
    ></i>
  </el-upload>
</template>

<script>
import { ProjectsInfoModule } from "@/store/modules/projects";
import { getFullImageUrl } from "@/utils/assert";
import { uploadFile } from "@/api"

export default {
  data() {
    return {
      imageUrl: this.value,
      image_size: this.imageSize,
      testing_id: ProjectsInfoModule.selectedTesting.id
    };
  },
  props: {
    value: {
      type: String,
      default: ""
    },
    imageSize: {
      type: String,
      default: "normal"
    }
  },
  mounted() {
    this.checkImageUrl()
  },
  methods: {
    handleAvatarSuccess(res, file) {
      this.imageUrl = URL.createObjectURL(file.raw);
    },
    beforeAvatarUpload(file) {
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
      let params = new FormData()
      params.append("file", data.file)
      params.append("search_id", this.testing_id)
      params.append("search_type", "media")

      uploadFile(params).then(res => {
        if (res.status === 0) {
          this.imageUrl = getFullImageUrl(res.data.url)
          this.$emit("updated", res.data.url)
        }
      })
    },
    checkImageUrl() {
      if (this.value.indexOf('@/image/mold_core.png') === 0) {
        this.imageUrl = require('@/image/mold_core.png')
      } else if (this.value.indexOf('@/image/mold_cavity.png') === 0) {
        this.imageUrl = require('@/image/mold_cavity.png')
      } else {
        this.imageUrl = getFullImageUrl(this.value)
      }
    }
  },
  watch: {
    value: function() {
      this.checkImageUrl()
    },
    imageUrl: function() {

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