<template>
  <div>
    <el-dialog
      title="规则详细"
      width="80%"
      :visible.sync="cardVisible"
      :before-close="handleClose"
    >
      <el-form ref="form" label-width="80px" :inline="true">
        <hr />
        <h3>条件部分</h3>
        <div v-for="(item,i) in conditionList" :key="i">
          <el-form-item label="条件类型" prop="conditiontype">
            <el-select v-model="item.conditiontype">
              <el-option label="普通前置条件" value="普通前置条件"></el-option>
              <el-option label="缺陷前置条件" value="缺陷前置条件"></el-option>
            </el-select>
          </el-form-item>
          <el-form-item label="关键字">
            <el-select v-if="item.conditiontype==='普通前置条件'" v-model="item.keyword" prop="keyword">
              <el-option 
                v-for="keyword, index in normal_conditionKeywordOptions"
                :key="index"
                :label="keyword.label"
                :value="keyword.value"
              >
              </el-option>
            </el-select>
            <el-select v-else-if="item.conditiontype==='缺陷前置条件'" v-model="item.keyword" prop="keyword">
              <el-option 
                v-for="keyword, index in defect_conditionKeywordOptions"
                :key="index"
                :label="keyword.label"
                :value="keyword.value"
              >
              </el-option>
            </el-select>
            <el-select v-else v-model="item.keyword" prop="keyword">
            </el-select>
          </el-form-item>
          <el-form-item label="描述">
            <el-select v-model="item.describe" prop="describe">
              <el-option label="低" value="low"></el-option>
              <el-option label="中" value="mid"></el-option>
              <el-option label="高" value="high"></el-option>
            </el-select>
          </el-form-item>
          <el-button circle icon="el-icon-plus" @click="addList()"></el-button>
          <el-button circle icon="el-icon-minus" @click="subList(i)" v-if="i>0"></el-button>
        </div>
      </el-form>
      <el-form ref="form" label-width="80px" :inline="true">
        <hr />
        <h3>结论部分</h3>
        <div v-for="(conclusion,i) in conclusionList" :key="i">
          <el-form-item label="条件类型">
            <el-select v-model="conclusion.conditiontype" class="epilog" prop="conditiontype">
              <el-option label="结论条件" value="结论条件"></el-option>
            </el-select>
          </el-form-item>
          <el-form-item label="关键字">
            <el-select v-model="conclusion.keyword" class="epilog" prop="keyword">
              <el-option 
                v-for="item, index in concludeKeywordOptions"
                :key="index"
                :label="item.label"
                :value="item.value"
              >
              </el-option>
            </el-select>
          </el-form-item>
          <el-form-item label="描述">
            <el-select v-model="conclusion.describe" class="epilog" prop="describe">
              <el-option label="低" value="low"></el-option>
              <el-option label="中" value="mid"></el-option>
              <el-option label="高" value="high"></el-option>
            </el-select>
          </el-form-item>
          <el-form-item label="动作">
            <el-select v-model="conclusion.action" class="epilog" prop="action">
              <el-option label="降低" value="reduce"></el-option>
              <el-option label="提高" value="add"></el-option>
            </el-select>
          </el-form-item>
          <el-button circle icon="el-icon-plus" @click="addConclusionList()"></el-button>
          <el-button circle icon="el-icon-minus" @click="subConclusionList(i)" v-if="i>0"></el-button>
        </div>
      </el-form>
      <hr />
      <el-button type="primary" @click="generate" style="margin-left: 50px; left: 40%; position: relative">生成规则</el-button>
      <div style="height: 20px" />
      <el-form>
        <el-form-item label="规则浏览">
          <el-input type="textarea" v-model="browse" rows="5" placeholder="请输入内容" class="text"></el-input>
        </el-form-item>
      </el-form>
      <span slot="footer" class="dialog-footer">
        <el-button v-if="!ruleId" type="primary" @click="determine" style="margin-left: 50px">添加</el-button>
        <el-button v-if="ruleId" type="primary" @click="update" style="margin-left: 50px">更新</el-button>
        <el-button @click="cancel">取 消</el-button>
      </span>
    </el-dialog>
  </div>
</template>
<script>
import { ruleDetailMethod, ruleKeywordMethod } from "@/api"
import { UserModule } from "@/store/modules/user"
export default ({
  name: "DetailedRules",
  props: {
    cardVisible:{
        type:Boolean,
        default:false
    },
    ruleData: {
      type: Map,
      default: () => ({
        "precondition": [],
        "solutions": [],
        "rule":""
      })
    },
    ruleId: {
      type: Number,
      default: null
    }
  },
    data() {
      return {
        conditionList:[{
          conditiontype: '缺陷前置条件',
          keyword: '',
          describe: ''
        }],
        conclusionList: [{
          conditiontype: '结论条件',
          keyword: '',
          describe: '',
          action: '',                
        }],
        browse: this.ruleData.get("rule"),
        normal_conditionKeywordOptions: [
          { label: "IP0", value: "IP0" },
          { label: "IP1", value: "IP1" }
        ],
        defect_conditionKeywordOptions: [
          { label: "IP0", value: "IP0" },
          { label: "IP1", value: "IP1" }
        ],
        concludeKeywordOptions: [
          { label: "IP0", value: "IP0" },
          { label: "IP1", value: "IP1" }
        ],
      }
    },
    created() {
      this.initView()
    },
    methods: {
      initView() {
        ruleKeywordMethod.get()
        .then(res => {
          if (res.status === 0) {
            let keywords = res.data.items
            this.concludeKeywordOptions.length = 0
            this.normal_conditionKeywordOptions.length = 0
            this.defect_conditionKeywordOptions.length = 0
            let keyOptions = []
            for (let i = 0; i < keywords.length; ++i) {
              if (keywords[i].key_type === "参数") {
                this.normal_conditionKeywordOptions.push({ label: keywords[i].name, value: keywords[i].name })
                this.concludeKeywordOptions.push({ label: keywords[i].name, value: keywords[i].name })
              } else if (keywords[i].key_type === "缺陷") {
                keyOptions.push({ label: keywords[i].name, value: keywords[i].name })
              }
            }
            // 去重
            keyOptions.forEach(i => {
              if(!this.concludeKeywordOptions[i.label]){
                this.concludeKeywordOptions.push({ label: keywords[i].name, value: keywords[i].name })
              }
            })
          }
        })
      },
      //加号
      addList() {
        this.conditionList.push({conditiontype: '', keyword: '', describe: ''})
      },
      //减号
      subList(index) {
        this.conditionList.splice(index, 1)
      },
      //加号
      addConclusionList() {
        this.conclusionList.push({conditiontype: '', keyword: '', describe: '', action:''})
      },
      //减号
      subConclusionList(index) {
        this.conclusionList.splice(index, 1)
      },
      handleClose(done) {
        this.resetView()
        this.$emit('close-rules',false)
      },
      cancel() {
        this.$emit('close-rules',false)
      },
      determine() {
        if(this.isValid()){
          this.generate()
          // 不带id,就是新增
          ruleDetailMethod.add({"rule":this.browse, "is_auto":0, "company_id":UserModule.company_id}).then(res => {
            })
          this.$emit('close-rules',false)
          this.resetView()
        }
      },
      update() {
        if(this.isValid()){
          this.generate()
          // 带id,就是编辑
          ruleDetailMethod.edit({"rule":this.browse}, this.ruleId).then(res => {
            })
          this.$emit('close-rules',false)
          this.resetView()
        }
      },
      generate(){        
        let if_form = "IF "
        for(let i=0;i<this.conditionList.length;i++){
          let condition = this.conditionList[i]
          if(i!=0){
              if_form += " AND "
          }
          if_form += condition.keyword +"_"+ condition.describe
          // if(condition.conditiontype === "qx"){
          //     if_form += condition.keyword +"_"+ condition.describe
          // } else {
          //     if_form += condition.keyword +"_"+ condition.describe
          // }
        }  
        let then_form = " THEN "
        for(let i=0;i<this.conclusionList.length;i++){
          let conclusion = this.conclusionList[i]
          if(i!=0){
              then_form += " AND "
          }
          then_form += conclusion.keyword + "_" + conclusion.action + "_" + conclusion.describe  
        } 
        this.browse = if_form + then_form
      }, 
      isValid(){
        for(let i=0;i<this.conditionList.length;i++){
          if(this.conditionList[i].conditiontype == ""){
            this.$message({
              type: 'warning',
              message: '条件类型不能为空'
            });  
            return false
          }
          if(this.conditionList[i].keyword == ""){
            this.$message({
              type: 'warning',
              message: '关键字不能为空'
            });  
            return false
          }
          if(this.conditionList[i].describe == ""){
            this.$message({
              type: 'warning',
              message: '描述不能为空'
            });  
            return false
          } 
        }
        for(let i=0;i<this.conclusionList.length;i++){
          if(this.conditionList[i].conditiontype == ""){
            this.$message({
              type: 'warning',
              message: '条件类型不能为空'
            });  
            return false
          }
          if(this.conclusionList[i].keyword == ""){
            this.$message({
              type: 'warning',
              message: '关键字不能为空'
            });  
            return false
          }
          if(this.conclusionList[i].describe == ""){
            this.$message({
              type: 'warning',
              message: '描述不能为空'
            }); 
            return false
          } 
          if(this.conclusionList[i].action == ""){
            this.$message({
              type: 'warning',
              message: '动作不能为空'
            }); 
            return false
          } 
        }
        return true
      },
      resetView(){
        this.conditionList = [{
          conditiontype: '',
          keyword: '',
          describe: ''
        }],
        this.conclusionList = [{
          conditiontype: '',
          keyword: '',
          describe: '',
          action: '',                
        }],
        this.browse = ''
      }
    },
    watch: {
      ruleData: function() {
        this.conditionList = this.ruleData.get("conditionList")
        this.conclusionList = this.ruleData.get("conclusionList")
        this.browse = this.ruleData.get("rule")
      }
    }
})
</script>
<style scoped>
.epilog {
    width: 150px;
}
.text {
    width: 800px;
}
</style>
