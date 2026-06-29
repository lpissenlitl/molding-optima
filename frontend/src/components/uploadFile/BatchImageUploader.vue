<template>
  <div class="upload-images">
    <el-upload
      action="#"
      list-type="picture-card"
      :multiple="true"
      :file-list="file_list"
      :before-upload="beforeUpload"
      :http-request="handleRequest"
      :on-remove="handleRemove"
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
import { uploadFile, deleteFile } from "@/api"
import { getFilePreviewUrl } from "@/utils/assert"

export default {
  name: "BatchImageUploader",
  props: {
    fileList: {
      type: Array,
      default: () => []
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
    maxCount: {
      type: Number,
      default: 0,
    }
  },
  data() {
    return {
      file_list: this.fileList,
      total_images: 0,
      already_update: 0
    }
  },
  watch: {
    fileList: {
      handler: function() {
        this.file_list = this.fileList
        this.file_list.forEach(file => {
          file.url = getFilePreviewUrl(file.uuid)
        })
      },
      deep: true,
      immediate: true
    }
  },
  methods: {
    beforeUpload(file) {
      const isImage = file.type.startsWith("image/")
      const isValidExt = /\.(jpg|jpeg|png|gif|webp)$/i.test(file.name)
      if (!isImage || !isValidExt) {
        this.$message.error("仅支持 JPG/PNG/GIF/WEBP 格式的图片")
        return false
      }

      if (this.maxCount > 0 && this.file_list.length >= this.maxCount) {
        this.$message.warning(`最多上传 ${this.maxCount} 张图片`)
        return false
      }
      return true
    },  
    async handleRequest({ file, onSuccess, onError }) {
      // 上传图片
      this.total_images++
      try {
        const params = new FormData()
        params.append("file", file)
        params.append("business_id", this.businessId)
        params.append("business_type", this.businessType)
        params.append("usage_type", this.usageType)

        const res = await uploadFile(params)
        if (res.status === 0) {
          this.already_update++
          this.$notify({
            title: "上传成功",
            message: "总图片" + this.total_images + "张，已成功上传" + this.already_update + "张图片。",
            type: "success"
          })
          console.log(getFilePreviewUrl(res.data.uuid))
          this.file_list.push({
            ...res.data,
            "name": res.data.filename,
            "url": getFilePreviewUrl(res.data.uuid),
          })
        }
      } catch (error) {
        onError(error)
      }
    },
    async handleRemove(file) {
      try {
        await this.$confirm("此操作将删除该照片, 是否继续?", "提示", {
          confirmButtonText: "确定",
          cancelButtonText: "取消",
          type: "warning"
        })
        const index = this.file_list.findIndex(f => f.uuid === file.uuid || f.id === file.uid)
        if (index !== -1) {
          this.file_list.splice(index, 1)
          const res = await deleteFile(file.uuid)
          if (res.status === 0) {
            this.$message({ type: "success", message: "删除成功!" })
          }
        }
      } catch (error) {
        this.$message({ type: "info", message: "已取消删除" })          
      }
    },
    handlePreview(file) {
      window.open(file.url, "_blank")
    },
  },
}
</script>

<style lang="scss">

</style>
