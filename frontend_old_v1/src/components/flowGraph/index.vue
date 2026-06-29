<template>
  <el-container>
    <div ref="container"></div>
  </el-container>
</template>

<script>
import LogicFlow from "@logicflow/core";
import "@logicflow/core/dist/style/index.css";

export default {
  props: {
    graphDataParent: {
      type: Object,
      default: null,
    },  
  },
  data() {
    return {
      lf: null,
      graphData: this.graphDataParent,
    };
  },
  created() {
  },
  mounted() {
    setTimeout(() => {
      this.huatu()
    },700)
  },
  methods: {
    huatu() {
      this.lf = new LogicFlow({
        container: this.$refs.container,
        grid: true,
        stopScrollGraph: true, // 禁止鼠标滚动移动画布
        stopZoomGraph: true, // 禁止缩放
        width: 810,
        height: 3500,
      });
      this.lf.render(this.graphData);
    }
  },
  watch: {
    graphDataParent: {
      handler: function (newVal) {
        this.graphData = this.graphDataParent;
        this.huatu()
      },
      deep: true,
    },
  },
};
</script>

<style>
</style>