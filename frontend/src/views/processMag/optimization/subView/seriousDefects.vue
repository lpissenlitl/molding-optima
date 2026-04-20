<template>
  <div>
    <el-table
      :data="table_data"
      size="mini"
      border
      fit
      highlight-current-row
    >
      <el-table-column prop="desc" label="" align="center"> </el-table-column>
      <el-table-column prop="original_value" label="原始值" align="center">
      </el-table-column>
      <el-table-column prop="suggest_value" label="推荐值" align="center">
      </el-table-column>
    </el-table>
    <div class="buttonGroup">
      <el-button-group>
        <el-button type="success" size="small" @click="execute">
          执行推荐值
        </el-button>
        <el-button type="warning" size="small" @click="inexecution">
          不执行
        </el-button>
      </el-button-group>
    </div>
  </div>
</template>

<script>
export default {
  name: "SeriousDefects",
  props: {
    tabData: {
      type: Array,
      default: [],
    },
  },
  data() {
    return {
      table_data: this.tabData,
      tableHeaderStyle: {
        "background-color": "lightblue",
        color: "#000",
        "font-size": "12px",
        padding: "8px 0px",
      },
    };
  },
  methods: {
    execute() {
      this.$emit('execute')
    },
    inexecution() {
      this.$emit('close-dialog')
    },
  },
  watch: {
    tabData: {
      handler: function (newVal) {
        this.table_data = this.tabData;
      },
      deep: true,
      immediate:true
    },
  },
};
</script>

<style lang="scss" scoped>
.buttonGroup {
  z-index: 999;
  position: relative;
  right: -187px;
  bottom: -20px;
  text-align: center;
  width: 100%;
  font-size: 11px;
  line-height: 32px;
  height: 40px;
  .el-button {
    width: 8rem;
  }
}
</style>