<template>
  <el-card>
    <!-- <h3>填充+保压+翘曲</h3> -->
    <div>
      <fill-and-holding :technology-data="technology" :process-data="process"> </fill-and-holding>
    </div>
    <div style="height:20px"></div>
    <div>
      <el-form-item label="翘曲分析类型" prop="warping_analysis_type">
        <el-select v-model="technology.warping_analysis_type">
          <el-option label="小变形" value="1"></el-option>
          <el-option label="大变形" value="2"></el-option>
          <el-option label="挫曲" value="3"></el-option>
        </el-select>
      </el-form-item>

      <el-form-item label="并行的线程数" prop="parallel_thread">
        <el-select v-model="technology.parallel_thread">
          <el-option label="自动" value="1"></el-option>
          <el-option
            label="单一线程(无并行)"
            value="4"
          ></el-option>
          <el-option label="最大值" value="2"></el-option>
          <el-option label="指定线程数" value="3"></el-option>
        </el-select>
      </el-form-item>

      <el-form-item
        label="AMG矩阵求解器选择"
        prop="amg_select"
        v-if="isShowAmg"
      >
        <el-select v-model="technology.amg_select">
          <el-option label="开" value="1"></el-option>
          <el-option label="关" value="0"></el-option>
        </el-select>
      </el-form-item>

      <el-form-item label="线程数" prop="thread_count" v-if="isShowThread">
        <el-input v-model="technology.thread_count"></el-input>
      </el-form-item>
    </div>
    <!-- <el-button size="mini" type="primary" class="but" @click="next" v-if="!isShowTwo">下一步</el-button>
    <el-button size="mini" type="primary" class="but" @click="last" v-if="!isShowOne">上一步</el-button> -->
  </el-card>
</template>

<script>
import FillAndHolding from "./fillAndHolding.vue";

export default {
  name: "FillAndHoldingAndWarping",
  components: { FillAndHolding },
  props: {
    technologyData: {
      type: Object,
      default: () => ({}),
    },
    processData: {
      type: Object,
      default: () => ({})
    }
  },
  data() {
    return {
      technology: this.technologyData,
      process: this.processData,
      // isShowOne: true,
      // isShowTwo: false,
      isShowAmg: false,
      isShowThread: false,
    };
  },
  methods: {
    // next() {
    //   this.isShowOne = false;
    //   this.isShowTwo = true;
    // },
    // last() {
    //   this.isShowOne = true;
    //   this.isShowTwo = false;
    // },
  },
  watch: {
    technologyData: {
      handler() {
        this.technology = this.technologyData;
      },
      immediate: true,
      deep: true,
    },
    processData: {
      handler() {
        this.process = this.processData
      },
      immediate: true,
      deep: true,
    },
    "technology.parallel_thread"(val) {
      if (val == "1" || val == "2" || !val) {
        this.isShowAmg = false;
        this.isShowThread = false;
      } else if (val == "4") {
        this.isShowAmg = true;
        this.isShowThread = false;
      } else if (val == "3") {
        this.isShowAmg = false;
        this.isShowThread = true;
      }
    },
  },
};
</script>

<style lang="scss" scoped>
.but {
  float: right;
  margin: 10px 20px 10px 0;
}
</style>