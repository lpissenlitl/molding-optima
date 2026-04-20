<template>
  <div class="upload-images">
    <el-upload
      action="#"
      class="avatar-uploader el-upload--text"
      multiple
      :http-request="uploadFile"
      :before-upload="beforeUploadFile"
      :file-list="fileList"
    >
      <el-button size="small" type="primary">点击上传</el-button>
    </el-upload>
  </div>
</template>
<script>
import { ProjectsInfoModule } from "@/store/modules/projects";
import SparkMD5 from "spark-md5";
import { getFullImageUrl } from "@/utils/assert";
import { uploadFile } from "@/api";
import { UserModule } from '@/store/modules/user';
export default {
  data() {
    return {
      uploadUrl:"",//你要上传视频到你后台的地址
      videoFlag:false , //是否显示进度条
      videoUploadPercent:"", //进度条的进度
		  isShowUploadVideo:false, //显示上传按钮
      fileList: [],
      tempList: this.value,
      disabled: false,
      chunkSize: 10 * 1024 * 1024, //文件分片上传，每块10MB
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
  watch: {
    value: { //深度监听，可以监听到对象，数组的变化
      handler(newV, oldV) {
        this.tempList = this.value
        this.fileList = []
        newV.forEach(element => {
          // 借用获取图片url函数
          var videoUrl = getFullImageUrl(this.company_id +"/"+ element)

          this.fileList.push({ url: videoUrl })
        })
      },
      deep:true
    }
  },
  methods: {
    //上传前回调
	  beforeUploadFile (file) {
      // const isLt20M = file.size / 1024 / 1024 < 200;
      // if (['video/mp4'].indexOf(file.type) == -1) { //'video/ogg', 'video/flv', 'video/avi', 'video/wmv', 'video/rmvb'
      //     this.$message.error('请上传正确的视频格式');
      //     return false;
      // }
      // if (!isLt20M) {
      //     this.$message.error('上传视频大小不能超过20MB哦!');
      //     return false;
      // }
      // this.isShowUploadVideo = false;
    },
    // 文件分片
    uploadFile(data) {
      if (data.file.size < this.chunkSize) {
        // 直接上传
      } else {
        this.uploadBigFile(data)
      }
    },
    uploadBigFile(data) {
      const createChunks = (file) => {
        let blobSlice = File.prototype.mozSlice || File.prototype.webkitSlice || File.prototype.slice
        let totalSize = 0
        let chunkList = []
        while (totalSize < file.size) {
          const chunk = blobSlice.call(file, totalSize, totalSize + this.chunkSize)
          totalSize += this.chunkSize
          chunkList.push({ chunk, size: chunk.size })
        }
        return chunkList
      }

      const chunkList = createChunks(data.file)

      const uploadChunk = (index, final_hash) => {
        let params = new FormData()
        params.append("file", chunkList[index].chunk)
        params.append("search_id", this.testing_id)
        params.append("search_type", "media")
        params.append("file", chunkList[index].chunk)
        params.append("slice_total", chunkList.length)
        params.append("slice_order", index + 1)
        params.append("slice_md5", chunkList[index].hash)
        params.append("finally_md5", final_hash)
        params.append("origin_filename", data.file.name)

        uploadFile(params).then(res => {
          if (res.status === 0) {
            if (res.data.url) {

            } else if (index < chunkList.length - 1) {
              uploadChunk(index + 1, final_hash)
            }
          }
        })
      }

      let index = 0
      let fileReader = new FileReader()
      let md5 = new SparkMD5()
      fileReader.onload = function(e) {
        const chunkHash = SparkMD5.hash(e.target.result)
        chunkList[index].hash = chunkHash
        md5.appendBinary(e.target.result)

        if (index < chunkList.length - 1) {
          index += 1
          loadFile()
        } else {
          const totalHash = md5.end()
          uploadChunk(0, totalHash)
        }
      }

      const loadFile = () => {
        fileReader.readAsBinaryString(chunkList[index].chunk)
      }
      loadFile()
    },
    handleRemove(file) {
      this.$confirm('此操作将删除该视频, 是否继续?', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
      // 移除视频
      let fileIndex = this.fileList.indexOf(file)
      if (fileIndex != -1) {
        this.fileList.splice(fileIndex, 1)
        this.tempList.splice(fileIndex, 1)
      }
      // this.$emit('input', Object.assign([], this.tempList))
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
    }
  }
};
</script>

<style lang="scss">
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
  .avatar {
    width: 178px;
    height: 178px;
    display: block;
  }
  .video-avatar {
    width: 400px;
    height: 200px;
  }
</style>
