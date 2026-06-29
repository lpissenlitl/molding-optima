<template>
  <div class="upload-images">
    <el-upload
      action="#"
      list-type="picture-card"
      multiple
      :file-list="file_list"
      :before-upload="beforeUpload"
      :http-request="uploadImage"
      :on-success="handleSuccess"
    >
      <i slot="default" class="el-icon-plus"></i>
      <div slot="file" slot-scope="{ file }">
        <img
          class="el-upload-list__item-thumbnail"
          v-if="file.url"
          :src="file.url"
          alt=""
          style="height:146px"
        />
        <span class="el-upload-list__item-actions">
          <span
            class="el-upload-list__item-preview"
            @click="handlePreview(file)"
          >
            <i class="el-icon-zoom-in"></i>
          </span>
          <span
            class="el-upload-list__item-delete"
            @click="handleRemove(file)"
          >
            <i class="el-icon-delete"></i>
          </span>
        </span>
      </div>
    </el-upload>
  </div>
</template>

<script>
import { uploadFile } from "@/api"
import { getFullFileUrl } from "@/utils/assert"

export default {
  name: "UploadTrialImages",
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
      store_type: "problem/images",
      total_images: 0,
      already_update: 0
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
  created() {

  },
  methods: {
    beforeUpload(file) {
      let file_type = file.name.substring(file.name.lastIndexOf(".") + 1)
      if (file_type.search(/jpg|png|jpeg/i) != 0) {
        this.$alert("只能上传 jpg/jpeg/png 格式文件！", "提示！", {
          confirmButtonText: "确定"
        })
        return false
      }
      return true
    },  
    uploadImage(data) {
      // 上传图片
      this.total_images++

      let params = new FormData()
      params.append("file", data.file)
      params.append("search_id", this.search_id)
      params.append("search_type", this.search_type)
      params.append("store_type", this.store_type)
      
      uploadFile(params).then(res => {
        if (res.status === 0) {
          this.already_update++
          this.$notify({
            title: "上传成功",
            message: "总图片" + this.total_images + "张，已成功上传" + this.already_update + "张图片。",
            type: "success"
          })
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
      })
        .catch(error => data.onError(error))
    },
    handleSuccess(response, file, file_list) {
      // 上传成功
    },
    handlePreview(file) {
      window.open(file.url, "_blank")
    },
    handleRemove(file) {
      this.$confirm("此操作将删除该照片, 是否继续?", "提示", {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        type: "warning"
      }).then(() => {
        // 移除图片
        let fileIndex = this.file_list.indexOf(file)
        if (fileIndex != -1) {
          this.file_list.splice(fileIndex, 1)
          this.total_images++
          this.already_update++
        }
        this.$message({
          type: "success",
          message: "删除成功!"
        })
      }).catch(() => {
        this.$message({
          type: "info",
          message: "已取消删除"
        })          
      })
    }
  },
}
</script>

<style lang="scss">

</style>
