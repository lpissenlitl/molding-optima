<template>
  <el-card>
    <!-- <h3>冷却fem</h3> -->
    <el-form-item label="熔体温度" prop="melt_temperature">
      <el-input
        type="number"
        min="0"
        v-model="technology.melt_temperature"
        @input="
          technology.melt_temperature = checkNumberFormat(
            technology.melt_temperature
          )
        "
      >
        <span slot="suffix">℃</span>
      </el-input>
    </el-form-item>

    <el-form-item label="开模时间" prop="mold_open_time">
      <el-input
        type="number"
        min="0"
        v-model="technology.mold_open_time"
        @input="
          technology.mold_open_time = checkNumberFormat(
            technology.mold_open_time
          )
        "
      >
        <span slot="suffix">s</span>
      </el-input>
    </el-form-item>
    <el-form-item label="注射前闭模时间" prop="mold_close_time">
      <el-input
        type="number"
        min="0"
        v-model="technology.mold_close_time"
        @input="
          technology.mold_close_time = checkNumberFormat(
            technology.mold_close_time
          )
        "
      >
        <span slot="suffix">s</span>
      </el-input>
    </el-form-item>
    <br>

    <el-form-item label="注射+保压+冷却时间" prop="injection_holding_cooling_time">
      <el-select v-model="technology.injection_holding_cooling_time">
        <el-option label="指定" value="1"></el-option>
        <el-option label="自动" value="2"></el-option>
      </el-select>
    </el-form-item>

    <el-form-item label="注射+保压+冷却时间" v-if="isShowCoolingTime">
      <el-input
        type="number"
        min="0"
        v-model="technology.injection_holding_cool_time"
        @input="technology.injection_holding_cool_time = checkNumberFormat(technology.injection_holding_cool_time)"
      >
        <span slot="suffix">s</span>
      </el-input>
    </el-form-item>

    <el-form-item label="模具温度选项" prop="mold_temperature">
      <el-select v-model="technology.mold_temperature">
        <el-option label="周期内平均" value="1"></el-option>
        <el-option label="周期内瞬态" value="2"></el-option>
        <el-option label="生产开始后瞬态" value="3"></el-option>
      </el-select>
    </el-form-item>
    <br />
  </el-card>
</template>

<script>
export default {
  name: "CoolingFem",
  props: {
    technologyData: {
      type: Object,
      default: () => ({}),
    },
  },
  data() {
    return {
      technology: this.technologyData,
      isShowCoolingTime: false,
    };
  },
  watch: {
    technologyData: {
        handler() {
            this.technology = this.technologyData;
        },
        immediate: true,
        deep: true,
    },
    "technology.injection_holding_cooling_time"(val) {
      if (val == "1") {
        this.isShowCoolingTime = true;
      } else {
        this.isShowCoolingTime = false;
      }
    },
  },
};
</script>

<style>
</style>