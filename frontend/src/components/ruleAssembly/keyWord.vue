<template>
  <div>
    <el-dialog 
      :visible.sync="dialogVisible"
      width="50%"
      :before-close="handleClose"
    >
      <el-form ref="form" :model="rule_keywords" label-width="90px" :inline="true">
        <el-form-item label="关键词" prop="name">
          <el-input v-model="rule_keywords.name" class="iput" placeholder="IV0"></el-input>
        </el-form-item>
        <el-form-item label="类型" prop="key_type">
          <el-radio-group v-model="rule_keywords.key_type" @change="setValue">
            <el-radio label="参数"></el-radio>
            <el-radio label="缺陷"></el-radio>
            <el-radio label="其他"></el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="注释" prop="comment">
          <el-input type="textarea" v-model="rule_keywords.comment" class="input" placeholder="一级注射压力"></el-input>
        </el-form-item>
        <el-form-item label="模糊级别" prop="level">
          <el-select v-model="rule_keywords.level" placeholder="请选择" style="width: 50%">
            <el-option label="3" value="3"></el-option>
            <el-option label="5" value="5"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="最小取值" prop="all_range_min">
          <el-input v-model="rule_keywords.all_range_min" style="width: 50%" type="number"></el-input>
        </el-form-item>
        <el-form-item label="最大取值" prop="all_range_max">
          <el-input v-model="rule_keywords.all_range_max" style="width: 50%" type="number"></el-input>
        </el-form-item>
        <el-form-item label="调整最小值" prop="action_range_min">
          <el-input v-model="rule_keywords.action_range_min" style="width: 50%" type="number" :disabled="rule_keywords.key_type=='缺陷'"></el-input>
        </el-form-item>
        <el-form-item label="调整最大值" prop="action_range_max">
          <el-input v-model="rule_keywords.action_range_max" style="width: 50%" type="number" :disabled="rule_keywords.key_type=='缺陷'"></el-input>
        </el-form-item><br />
        <el-form-item label="调整幅度限定值" prop="action_max_val">
          <el-input v-model="rule_keywords.action_max_val" class="iput" type="number" :disabled="rule_keywords.key_type=='缺陷'"></el-input>
        </el-form-item>
      </el-form>
      <span slot="footer" class="dialog-footer">
        <el-button type="primary" @click="determine" style="margin-left: 50px">保存</el-button>
        <el-button @click="cancel">取 消</el-button>
      </span>
    </el-dialog>
  </div>
</template>
<script>
import { ruleKeywordMethod } from "@/api";
import { UserModule } from "@/store/modules/user";
export default ({
    name: "KeyWord",
    props: {
      dialogVisible:{
        type:Boolean,
        default:false
      },
      // FormData就是这个form表单的数据，如果父组件没有传，那就初始化都为空，点击编辑的时候需要传入这一行的数据，点击新建的时候需要全部置为空
      formData:{
        type:Object,
        default:() => ({
          company_id: UserModule.company_id,
          name: '',
          key_type: null,
          comment: '',
          level: null,
          all_range_min: null,
          all_range_max:null,
          action_range_min: null,
          action_range_max: null,
          action_max_val: null
        })
      },
      ruleKeyId:{
        type:Number,
        default:null
      }
    },
    data() {
      return {
        rule_keywords:this.formData
      }
    },
    mounted() {
  
    },
    methods: {
      handleClose(done) {
        this.$emit('closeDialog',false)
      },
      //取消按钮
      cancel() {
        this.$emit('closeDialog',false)
      },
      //保存按钮
      determine() {
        if(!this.ruleKeyId){
          ruleKeywordMethod.add(this.rule_keywords)
          .then(res => {
            if (res.status === 0) {
              this.rule_keywords = {
                company_id: UserModule.company_id,
                name: '',
                key_type: null,
                comment: '',
                level: null,
                all_range_min: null,
                all_range_max:null,
                action_range_min: null,
                action_range_max: null,
                action_max_val: null
              }
            }
            this.$message({
              type:res.status === 0?'success':'error',
              message:res.status === 0?'保存成功！':'保存失败！'
            })
          }).finally(()=> {
            this.$emit('closeDialog',false)
          })
        } else {
          ruleKeywordMethod.edit(this.rule_keywords,this.ruleKeyId)
          .then(res => {
            if (res.status === 0) {
            }
            this.$message({
              type:res.status === 0?'success':'error',
              message:res.status === 0?'保存成功！':'保存失败！'
            })
          }).finally(()=> {
            this.$emit('closeDialog',false)
          })
        }
       },
      setValue(val) {
        if (val === "缺陷") {
          this.rule_keywords.action_range_min = -1
          this.rule_keywords.action_range_max = -1
          this.rule_keywords.action_max_val = -1
        }
      }
    },
    watch:{
      "formData":function(){
        this.rule_keywords =this.formData
      }
    }
})
</script>
<style scoped>
.iput {
    width: 350px;
}
</style>
