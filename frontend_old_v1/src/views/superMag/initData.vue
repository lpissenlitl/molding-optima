<template>
  <div>
    <div class="toolbar">
      <el-form 
        :inline="true" 
        :model="query" 
        size="mini"
        label-width="6rem"
      >
        <el-form-item label="操作对象">
          <el-autocomplete
            v-model="query.interface_view"
            placeholder="操作对象"
            clearable
            style="width:14rem"
            :fetch-suggestions="queryInterfaceView"
          >
            <template slot-scope="{ item }">
              <span class="label">{{ item.label }}</span>
            </template>
          </el-autocomplete>
        </el-form-item>
        <el-form-item label="下拉框">
          <el-autocomplete
            v-model="query.interface_select"
            placeholder="下拉框"
            clearable
            style="width:16rem"
            :fetch-suggestions="queryInterfaceSelect"
            @select="queryListData"
          >
            <template slot-scope="{ item }">
              <span class="label">{{ item.label }}</span>
            </template>
          </el-autocomplete>
        </el-form-item>
        <el-form-item style="float:right">
          <el-button type="primary" @click="queryListData(true)" style="width:6rem">搜索</el-button>
        </el-form-item>
      </el-form>
    </div>
    <div style="text-align: left">
      <el-transfer
        v-model="selectd_choice"
        style="text-align: left; display: inline-block"
        :data="listData"
        :titles="['修改前', '修改后']"
      >
        <el-input v-model="item_to_add" class="transfer-footer" slot="left-footer" style="width:10rem"></el-input>
        <el-button class="transfer-footer" slot="left-footer" size="small" type="primary" @click="addItem">新增</el-button>
        <el-button class="transfer-footer" slot="right-footer" size="small" type="primary" style="float:right" @click="saveDetail">提交修改</el-button>
      </el-transfer>
    </div>
    <div class="nextButton">
      <el-tooltip 
        content="第一次进入页面时,一键初始化下拉框数据" 
        v-if="!inited"
      >
        <el-button type="primary" @click="initData" style="width:6rem">一键初始化</el-button>
      </el-tooltip>
    </div>
  </div>
</template>
<script>
import { getOptions, optionMethod } from '@/api'
import { UserModule } from '@/store/modules/user'

export default {
  data() {
    return {
      query: {
        company_id: UserModule.company_id,
        interface_view: null,
        interface_select: null,
        view_desc:null,
        select_desc:null
      },
      listData: [],
      selectd_choice:[],
      loading: false,
      item_to_add: "",
      list_length: 0,
      inited: 0
    }
  },
  methods: {
    queryInterfaceView(queryString, cb) {
      let interface_view_list = []
      getOptions("interface_view")
      .then(res => {
        if (res.status === 0 && Array.isArray(res.data) && res.data.length > 0) {
          this.inited = 1
          for (let i = 0; i < res.data.length; ++i) {
            interface_view_list.push({ "value": res.data[i].value, "label": res.data[i].label})
          }
        }
      })
      var results = queryString ? interface_view_list.filter(this.createStateFilter(queryString)) : interface_view_list;
      cb(results);
    },
    queryInterfaceSelect(queryString, cb) {
      let interface_select_list = []
      getOptions("interface_select",{
        "interface_view": this.query.interface_view,
        "company_id": UserModule.company_id,
      }).then(res => {
        if (res.status === 0 && Array.isArray(res.data)) {
          for (let i = 0; i < res.data.length; ++i) {
            interface_select_list.push({ "value": res.data[i].value, "label": res.data[i].label})
          }
        }
      })
      var results = queryString ? interface_select_list.filter(this.createStateFilter(queryString)) : interface_select_list;
      cb(results);
    },
    createStateFilter(queryString) {
      return (state) => {
        return (state.value.toLowerCase().indexOf(queryString.toLowerCase()) === 0);
      };
    },
    queryListData(reset=false) {
      if(reset){
        this.query.page_no = 1
      }
      getOptions("custom_option", {
      interface_view: this.query.interface_view,
      interface_select: this.query.interface_select,
      company_id:UserModule.company_id
      }).then(res => {
      // 如果数据库有值,则读取,如果没有,则读取页面const
      if (res.status === 0 && res.data.length != 0) {
        this.listData = res.data
        this.list_length = this.listData.length
      }
      })
      this.selectd_choice = []
    },
    addItem(){
      this.listData.push({
        'interface_view': this.query.interface_view, 
        'interface_select': this.query.interface_select, 
        'key': this.list_length, 
        'value': this.item_to_add, 
        'label': this.item_to_add, 
        'company_id': this.query.company_id,
        'view_desc':this.listData[0].view_desc,
        'select_desc':this.listData[0].select_desc
        })
      this.item_to_add = ""
      this.list_length = this.list_length + 1
    },
    deleteItem(item){
    },
    initData(){
      this.$confirm('第一次进入该界面时,一键初始化,会使所有下拉框恢复原始数据.之前的更改将被丢弃,且不可找回.确认要初始化么?', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        getOptions("init", {
        interface_view: this.query.interface_view,
        interface_select: this.query.interface_select,
        company_id:UserModule.company_id
        }).then(res => {          
          this.$message({
            type: 'success',
          message: '初始化成功!'
          });
        })
      }).catch(() => {
        this.$message({
          type: 'info',
          message: '已取消初始化数据'
        });          
      });
    },
    saveDetail(){
      if(this.selectd_choice.length === 0){
        this.$message({
          type: 'warning',
          message: '请把选项添加到修改后!'
        });
      } else {
        let choose_data = []
        let choose_length = 0 
        for(let i=0;i<this.listData.length;i++){
          if(this.selectd_choice.indexOf(i) > -1){
            choose_data.push(this.listData[i])
            choose_data[choose_length]["key"] =  choose_length
            choose_length = choose_length + 1
          }
        }
        optionMethod.add({options:choose_data}).then(res => {
        // 如果数据库有值,则读取,如果没有,则读取页面const
        if (res.status === 0 && res.data.length != 0) {
          this.listData = []
          this.selectd_choice = []
          this.$message({
            type: 'success',
            message: '修改成功!'
          });
        }
        })
      }
    }
  }
}
</script>

<style lang="scss" scoped>
  .el-transfer-panel{
    width:400px !important;
    height:500px !important;
  }
  .el-transfer-panel__list{
    width:400px !important;
    height:500px !important;
  }
</style>