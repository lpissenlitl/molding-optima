<template>
  <div class="moreSelete">
    <el-input :placeholder="checkedLists.length?`${this.checkedLists}`:'请输入内容'" v-model="inputVal" @input="filterVal">
      <el-popover slot="append" placement="bottom-end" width="200" trigger="click" v-model="visible">
        <el-checkbox v-model="checkAll" @change="handleCheckAll">全选 (已选{{ checkedLists.length }})</el-checkbox>
        <div style="max-height: 320px;overflow: scroll" class="moreSeletePup">
          <el-checkbox-group v-model="checkedLists" @change="CheckChange">
            <el-checkbox v-for="(item,index) in MoreList" :label="item" :key="index">{{ item }}</el-checkbox>
          </el-checkbox-group>
        </div>
        <el-button slot="reference"><i class="el-icon-arrow-down"></i>请选择</el-button>
      </el-popover>
    </el-input>
  </div>
</template>

<script>
  export default {
    name: 'Moresele',
    data(){
      return {
        inputVal: '',
        visible: false,
        checkAll: false,
        checkedLists: []
      }
    },
    props: {
      dataList: {
        type: Array,
        default: () => []
      }
    },
    computed: {
      MoreList(){
        let List = []
        this.dataList.map(item=>{
          if(item.includes(this.inputVal)){
            List.push(item)
          }
        })
        return List
      }
    },
    methods: {
      handleCheckAll(val){
        // this.checkedLists = val?this.MoreList:[]
        this.checkedLists = val?[...new Set([...this.checkedLists, ...this.MoreList])]:[]
        this.$emit('checked-more', this.checkedLists)
      },
      CheckChange(){
        this.$emit('checked-more', this.checkedLists)
      },
      filterVal(){
        this.visible = true
      }
    },
    watch: {
      visible() {
        if(!this.visible){
          this.inputVal = ''
        }
      }
    }
  }
</script>

<style lang="scss">
  .el-popover{
    .moreSeletePup{
      .el-checkbox-group{
        label.el-checkbox{
          margin-left: 0;
          width: 100%;
          line-height: 24px;
        }
      }
    }
  }
</style>
