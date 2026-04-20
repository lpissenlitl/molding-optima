<template>
  <div class="upload-images">
    <el-upload
      action="#"
      list-type="picture-card"
      multiple
      :http-request="uploadImage"
      :file-list="fileList"
      :on-success="handleSuccess"
      :before-upload="beforeUpload"
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
            @click="handlePictureCardPreview(file)"
          >
            <i class="el-icon-zoom-in"></i>
          </span>
          <span
            v-if="!disabled"
            class="el-upload-list__item-delete"
            @click="handleRemove(file)"
          >
            <i class="el-icon-delete"></i>
          </span>
        </span>
      </div>
    </el-upload>
    <el-dialog :visible.sync="dialogVisible" modal>
      <img :src="dialogImageUrl" alt="" />
    </el-dialog>
  </div>
</template>
<script>
import { ProjectsInfoModule } from "@/store/modules/projects";
import { getFullImageUrl } from "@/utils/assert";
import { uploadFile } from "@/api";
import { UserModule } from '@/store/modules/user';
var imagesCount = 0;
var alreadyUpdate = 0;
export default {
  data() {
    return {
      dialogImageUrl: "",
      dialogVisible: false,
      disabled: false,
      fileList: [],
      tempList: this.value,
      company_id: UserModule.company_id,
      testing_id: ProjectsInfoModule.selectedTesting.id
    };
  },
  props: {
    value: {
      type: Array,
      default: () => []
    }
  },
  created() {
    imagesCount = 0;
    alreadyUpdate = 0;
  },
  methods: {
    handleRemove(file) {
      this.$confirm('此操作将删除该照片, 是否继续?', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        // 移除图片
        let fileIndex = this.fileList.indexOf(file)
        if (fileIndex != -1) {
          this.fileList.splice(fileIndex, 1)
          this.tempList.splice(fileIndex, 1)
        }
        this.$emit('input', Object.assign([], this.tempList))
        this.$message({
          type: 'success',
          message: '删除成功!'
        });
      }).catch(() => {
        this.$message({
          type: 'info',
          message: '已取消删除'
        });          
      });
    },
    handlePictureCardPreview(file) {
      //点击预览
      window.open(file.url, "_blank")
    },
    handleSuccess(response, file, fileList) {
      // 上传成功
    },
    verifyImage(data) {
      // 上传图片之前,先校验md5,服务器上是否存在该图片,如果存在,直接返回
    },
    beforeUpload(file) {
      let file_type = file.name.substring(file.name.lastIndexOf(".") + 1)
      if (file_type.search(/jpg|png|jpeg/i) != 0) {
        this.$alert("只能上传 jpg/jpeg/png 格式文件！", "提示！", {
          confirmButtonText: '确定'
        })
        return false
      }
      return true
    },  
    uploadImage(data) {
      // 上传图片
      let params = new FormData();
      imagesCount++;
      params.append("file", data.file);
      params.append("search_id", this.testing_id)
      params.append("search_type", "media");

      uploadFile(params).then(res => {
        if (res.status === 0) {
          this.$message({ message: "上传成功！", type: 'success' })
          this.tempList.push(res.data.url)
          alreadyUpdate++;
          this.$notify({
            title: '上传成功',
            message: '已成功上传'+alreadyUpdate+'张图片',
            type: 'success'
          });
        } else {
          //回调上传失败事件
          data.onError(res.msg);
        }
      })
      .catch(error => data.onError(error));
    }
  },
  watch: {
    value: function() { //深度监听，可以监听到对象，数组的变化
      this.tempList = this.value
    },
    'tempList': {
      handler: function(newV, oldV) {
        this.fileList = []
        newV.forEach(element => {
          var imageUrl = getFullImageUrl(element)
          this.fileList.push({ url: imageUrl })
          this.$set(this.fileList)
        })
      },
      deep:true
    }
  },
};
</script>

<style lang="scss">
.upload-images {
  .el-dialog {
    display: flex;
    flex-direction: column;
    margin: 0 !important;
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    /*height:600px;*/
    max-height: calc(100% - 30px);
    max-width: calc(100% - 30px);
  }
  .el-dialog__body {
    flex: 1;
    overflow: auto;
    text-align: center;
  }
  .el-upload-list__item {
    transition: none !important;
  }
}
</style>
