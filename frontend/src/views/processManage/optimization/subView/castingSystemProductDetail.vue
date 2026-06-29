<template>
  <el-form
    size="mini"
    label-width="8rem"
    :model="detail_info"
    :inline="true"
  >
    <el-form-item
      label="制品数量"
      prop="product_number"
    >
      <el-input 
        v-model.trim="detail_info.product_number"
        type="number" 
        @input="detail_info.product_number=$formatNumber(detail_info.product_number, 0)"
      >
      </el-input>
    </el-form-item>
    <el-form-item
      label="制品流长"
      prop="product_flow_length"
    >
      <el-input 
        v-model.trim="detail_info.product_flow_length"
        type="number" 
        @input="detail_info.product_flow_length=$formatNumber(detail_info.product_flow_length)"
      >
        <span slot="suffix">mm</span>
      </el-input>
    </el-form-item>
    <el-form-item
      label="最大壁厚"
      prop="product_max_thickness"
    >
      <el-input 
        v-model.trim="detail_info.product_max_thickness"
        type="number" 
        @input="detail_info.product_max_thickness=$formatNumber(detail_info.product_max_thickness)"
      >
        <span slot="suffix">mm</span>
      </el-input>
    </el-form-item>
    <el-form-item
      label="平均壁厚"
      prop="product_ave_thickness"
    >
      <el-input 
        v-model.trim="detail_info.product_ave_thickness"
        type="number" 
        @input="detail_info.product_ave_thickness=$formatNumber(detail_info.product_ave_thickness)"
      >
        <span slot="suffix">mm</span>
      </el-input>
    </el-form-item>
    <el-form-item
      label="单件重量"
      prop="product_single_weight"
    >
      <el-input 
        v-model.trim="detail_info.product_single_weight"
        type="number" 
        @input="detail_info.product_single_weight=$formatNumber(detail_info.product_single_weight)"
      >
        <span slot="suffix">g</span>
      </el-input>
    </el-form-item>
  </el-form>
</template>

<script>
export default {
  name: "CastingSystemProductDetail",
  props: {
    productDetail: {
      type: Object,
      default: () => {}
    }
  },
  data() {
    return {
      detail_info: this.productDetail
    }
  },
  watch: {
    productDetail() {
      this.detail_info = this.productDetail;
    }
  }
}
</script>

<style lang="scss" scoped>
.el-input {
  width: 10rem;
}
</style>