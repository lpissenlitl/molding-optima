<template>
  <el-form
    ref="detail_info"
    :inline="true"
    :model="detail_info"
    size="mini"
    label-width="10rem"
  >
    <el-divider class="precondition-divider" content-position="center">
      <span>模具</span>
    </el-divider>
    <el-form-item 
      label="模具编号" 
      prop="mold_no" 
    >
      <el-autocomplete 
        v-model="detail_info.mold_no"
        clearable
        :fetch-suggestions="((str, cb) => {querySuggestionOptions(str, cb, 'mold_no')})"
        placeholder="请输入内容"
        :debounce="0"
        @select="onMoldSelected"
      >
      </el-autocomplete>
    </el-form-item>
    <el-form-item 
      label="模具类别" 
      prop="mold_type"
    >
      <el-input
        v-model="detail_info.mold_type"
        readonly
      ></el-input>
    </el-form-item>
    <el-form-item 
      label="模具名称"
      prop="mold_name"
    >
      <el-input
        v-model="detail_info.mold_type"
        readonly
      ></el-input>
    </el-form-item>
    <el-form-item 
      label="型腔数量"
      prop="cavity_num"
    >
      <el-input 
        v-model="detail_info.cavity_num"
        readonly
      >
        <span slot="suffix">腔</span>
      </el-input>
    </el-form-item>
    <el-form-item 
      label="注塑周期"
      prop="inject_cycle_require"
    >
      <el-input 
        type="number"
        v-model="detail_info.inject_cycle_require"
        readonly
      >
        <span slot="suffix">s</span>
      </el-input>
    </el-form-item>
    <el-divider content-position="center">
      <span>制品</span>
    </el-divider>
    <el-form-item
      label="制品大类(行业)"
      prop="product_industry"
    >
      <el-input
        v-model="detail_info.product_industry"
        readonly
      >
      </el-input>
    </el-form-item>
    <el-form-item
      label="制品中类(商品)"
      prop="product_category"
    >
      <el-input
        v-model="detail_info.product_category"
        readonly
      >
      </el-input>
    </el-form-item>
    <el-form-item
      label="制品小类(品类)"
      prop="product_type"
    >
      <el-input
        v-model="detail_info.product_type"
        readonly
      >
      </el-input>
    </el-form-item>
    <el-form-item
      label="制品名称"
      prop="product_name"
    >
      <el-input 
        v-model.trim="detail_info.product_name"
        readonly
      ></el-input>
    </el-form-item>
    <el-form-item
      label="总注射重量"
      prop="product_total_weight"
    >
      <el-input 
        v-model.trim="detail_info.product_total_weight"
        readonly
      >
        <span slot="suffix">g</span>
      </el-input>
    </el-form-item>
  </el-form>
</template>

<script>
import SuggestionOptions from "@/mixins/suggestionOptions.vue";

export default {
  name: "BasicMoldInfo",
  mixins: [ SuggestionOptions ],
  props: {
    basicMoldInfo: {
      type: Object,
      default: () => {}
    },
  },
  data() {
    return {
      detail_info: this.basicMoldInfo,
    }
  },
  methods: {
    async querySuggestionOptions(input_str, cb, db_column) {
      let selections = [];
      if (["mold_no"].includes(db_column)) {
        selections = await this.queryOptions(input_str, "project", db_column);
      }
      cb(selections);
    },
    onMoldSelected(item) {
      this.detail_info.id = item.id;
    },
  },
  watch: {
    basicMoldInfo: {
      handler: function() {
        this.detail_info = this.basicMoldInfo;
      },
      deep: true
    }
  }
}
</script>

<style lang="scss" scoped>
  .el-input,
  .el-select,
  .el-autocomplete {
    width: 10rem;
  }
</style>