<template>
  <div class="upload-images">
    <el-upload
      action="#"
      class="avatar-uploader el-upload--text"
      multiple
      :http-request="uploadVideo"
      :file-list="fileList"
      :on-progress="uploadVideoProcess"
      :before-upload="beforeUploadVideo"
    >
      <el-button size="small" type="primary">点击上传</el-button>
      <!-- <i slot="default" class="el-icon-plus"></i> -->
      <div slot="file" slot-scope="{ file }">
        <div>
          <video
            :src="file.url"
            class="avatar video-avatar"
            controls="controls"
          >您的浏览器不支持视频播放</video>
          <el-progress
            v-if="videoFlag == true"
            type="circle"
            :percentage="videoUploadPercent"
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
import { ProjectsInfoModule } from "@/store/modules/projects";
import SparkMD5 from "spark-md5";
import { getFullImageUrl } from "@/utils/assert";
import { uploadFile } from "@/api";
import { UserModule } from '@/store/modules/user';
export default {
  data() {
    return {
      uploadUrl: "",//你要上传视频到你后台的地址
      videoFlag: false , //是否显示进度条
      videoUploadPercent: "", //进度条的进度
		  isShowUploadVideo: false, //显示上传按钮
      fileList: [],
      disabled: false,
      tempList: this.value,
      partSize: 8 * 1024 * 1024, //文件分片上传，每块8M
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
          var videoUrl = getFullImageUrl(element)
          this.fileList.push({ url: videoUrl })
        })
      },
      deep:true
    }
  },
  methods: {
    //上传前回调
	  beforeUploadVideo (file) {

      if (['video/mp4'].indexOf(file.type) == -1) { //'video/ogg', 'video/flv', 'video/avi', 'video/wmv', 'video/rmvb'
        this.$alert("只能上传 mp4 格式文件！", "提示！", {
          confirmButtonText: '确定'
        })
        return false
      }

      const isLt200M = file.size / 1024 / 1024 < 200;
      if (!isLt200M) {
        this.$alert("上传视频大小不能超过200MB！", "提示！", {
          confirmButtonText: '确定'
        })
        return false
      }

      return true
    },
    // 文件分片
    createChunks(file) {
      let current = 0;
      const partList = [];
      let blobSlice = File.prototype.slice || File.prototype.mozSlice || File.prototype.webkitSlice
      while (current < file.size) {
        // 核心是对文件的 slice
        const chunk = blobSlice.call(file, current, current + this.partSize)
        partList.push({ chunk, size: chunk.size });
        current += this.partSize; // this.partSize 定位每片大小
      }
      return partList;
    },
    getSliceInfo(data, callBack) {
      //如果文件过大，则分段上传；计算每个分片的md5，以及整个文件的md5
      let partList = this.createChunks(data.file)
      const fileReader = new FileReader()
      let index = 0;
      const md5 = new SparkMD5();
      const loadFile = () => {
        const slice = partList[index].chunk
        fileReader.readAsBinaryString(slice)
      }
      loadFile();
      fileReader.onload = e => {
        const sliceHash = SparkMD5.hash(e.target.result)
        partList[index].hash = sliceHash
        md5.appendBinary(e.target.result);
        if (index < partList.length - 1) {
          index += 1;
          loadFile();
        } else {
          const totalHash = md5.end()
          if(callBack) {
            callBack({partList, totalHash})
          }
        }
      }
    },
    //进度条
    uploadVideoProcess (event, file, fileList) {
      this.videoFlag = true;
      file.percentage = event.percentage
      this.videoUploadPercent = event.percentage;
    },
    uploadVideo(data) {
      // 上传视频
      let params = new FormData();
      if(data.file.size < this.partSize) {
        params.append("file", data.file);
        params.append("search_id", this.testing_id)
        params.append("search_type", "media")
        
        uploadFile(params).then(res => {
          if (res.status === 0) {
            //回调上传成功事件
            this.tempList.push(res.data.url)
          } else {
            //回调上传失败事件
            data.onError(res.msg);
          }
        })
        .catch(error => data.onError(error));
      } else {
        //上传大文件
        this.uploadBigVideo(data)
      }
    },
    uploadBigVideo(data) {
      //如果文件过大，则分段上传；计算每个分片的md5，以及整个文件的md5
      data.onProgress({ percentage: 0 })
      this.getSliceInfo(data, (ret) => {
        const uploadSlice = (index) => {
          let params = new FormData();
          params.append("file", ret.partList[index].chunk)
          params.append("search_id", this.testing_id)
          params.append("search_type", "media")
          params.append("slice_total", ret.partList.length)
          params.append("slice_order", index + 1)
          params.append("slice_md5", ret.partList[index].hash)
          params.append("finally_md5", ret.totalHash)
          params.append("origin_filename", data.file.name)

          uploadFile(params).then(res => {
            if (res.status === 0) {
              if(res.data.url) {
                // 修改报告后上传,大于3M,调用切片上传,不需要显示图片
                if(data.file.name.indexOf("xlsx") === -1){
                  // 如果有了url直接就不继续上传了，说明文件已经存在了
                  this.tempList.push(res.data.url)
                }
                data.onProgress({percentage: 100})
                setTimeout(() => {
                  this.videoFlag = false;
                }, 200);
                this.$emit("finish-upload")
                return
              }else if(index < ret.partList.length - 1) {
                data.onProgress({percentage: ~~((index + 1) * 100.0 / ret.partList.length)})
                uploadSlice(index + 1)
              }
            } else {
              this.$message.error('上传失败，请重新上传！');
            }
          })
          .catch(error => data.onError(error));
        }

        uploadSlice(0)
      })
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
