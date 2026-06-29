<template>
  <div>
    <el-collapse v-model="active_collapse" class="collapseItemTitle">
      <el-collapse-item title="缺陷参数" name="1">
        <el-form ref="methodForm" label-width="2.5rem" size="small" :inline="true">
          <div
            class="box"
            v-for="(item, idx) in rule_method.preconditions"
            :key="idx"
          >
            <div class="left">
              <span>
                <el-form-item label="工况">
                  <el-select 
                    size="mini"
                    v-model="item.keyword" 
                    prop="keyword"
                    @change="normalKeywordChange"
                   >
                    <el-option-group
                      v-for="group in normalKeywordOptions"
                      :key="group.label"
                      :label="group.label">
                      <el-option
                        v-for="(item, index) in group.options"
                        :key="index"
                        :label="item.label"
                        :value="item.value">
                      </el-option>
                    </el-option-group>
                  </el-select>
                </el-form-item>

                <el-form-item label="状态">
                  <el-select
                    size="mini"
                    v-model="item.status"
                    prop="status"
                  >
                    <template>
                      <el-option
                        v-for="(key, value) in paraLevelMap"
                        :key="value"
                        :label="key.label"
                        :value="key.value"
                      ></el-option>
                    </template>
                  </el-select>
                </el-form-item>

                <el-button
                  v-if="idx > 0 || rule_method.preconditions.length > 1"
                  type="danger"
                  circle
                  icon="el-icon-minus"
                  size="small"
                  @click="subPrecondition(idx)"
                ></el-button>

                <el-button
                  v-if="idx === rule_method.preconditions.length - 1"
                  circle
                  type="success"
                  icon="el-icon-plus"
                  size="small"
                  @click="addPrecondition()"
                ></el-button>
                <br />
              </span>
            </div>

            <div class="right">
              <span
                v-for="(item, index) in rule_method.preconditions[idx].solutions"
                :key="index"
              >
                <el-form-item label="调整">
                  <el-select size="mini" v-model="item.action" prop="action">
                    <template>
                      <el-option
                        v-for="(key, value) in actionMap"
                        :key="value"
                        :label="key.label"
                        :value="key.value"
                      ></el-option>
                    </template>
                  </el-select>
                </el-form-item>
                <el-form-item label="参数">
                  <el-select size="mini" v-model="item.keyword" prop="keyword">
                    <el-option-group
                      v-for="group in concludeKeywordOptions"
                      :key="group.label"
                      :label="group.label">
                      <el-option
                        v-for="(item, index) in group.options"
                        :key="index"
                        :label="item.label"
                        :value="item.value">
                      </el-option>
                    </el-option-group>
                  </el-select>
                </el-form-item>

                <el-button
                  v-if="
                    idx > 0 || rule_method.preconditions[idx].solutions.length > 1
                  "
                  circle
                  type="danger"
                  icon="el-icon-minus"
                  size="small"
                  @click="subSolution(idx, index)"
                ></el-button>

                <el-button
                  circle
                  type="success"
                  icon="el-icon-plus"
                  size="small"
                  @click="addSolution(idx)"
                ></el-button>
                <br />
              </span>
            </div>
          </div>
        </el-form>
        <div style="text-align: center" v-if="is_show">
          <el-button
            type="primary"
            size="mini"
            @click="generateGraphData"
            style="width: 8rem"
            :disabled="!is_defect"
          >
            生成流程图
          </el-button>
        </div>
      </el-collapse-item>
    </el-collapse>
  </div>
</template>

<script>
import { getParaLevel, normalKeyword, concludeKeyword} from "@/utils/rule_to_key";

export default {
  name: "RuleMethodDetail",
  props: {
    ruleFlow: {
      type: Object,
      default: () => ({}),
    },
    currentDefect: {
      type: Number,
      default: 0,
    },
    isShow: null,
    isDefect: null,
    activeCollapse: {
      type: Array,
      default: () => ([]),
    },
  },
  data() {
    return {
      is_show: this.isShow,
      is_defect: this.isDefect,
      rule_flow: this.ruleFlow,
      current_defect: this.currentDefect,
      rule_method: this.ruleFlow.defect_data[this.currentDefect].rule_method,
      normalKeywordOptions: normalKeyword,
      paraLevelMap: [
        {label: "偏低",value: "偏低",desc: "low"},
        {label: "偏高",value: "偏高",desc: "high"},
        {label: "不合理",value: "不合理",desc: "worse"},
      ],
      actionMap: [
        {label: "增加",value: "增加",desc: "add"},
        {label: "减小",value: "减小",desc: "reduce"},
        {label: "调整",value: "调整",desc: "adjust"},
        {label: "弹窗",value: "弹窗",desc: "adjust"},
      ],
      concludeKeywordOptions: concludeKeyword,
      right_sum: 1,
      active_collapse:this.activeCollapse
    };
  },
  created() {},
  methods: {
    generateGraphData() {
      // 需要验证是否为空
      let sub_solution_num_list = [];
      let total_solution_num = 0;
      for (let i = 0; i < this.rule_method.preconditions.length; i++) {
        let precondition = this.rule_method.preconditions[i];
        let current_solution_num = precondition.solutions.length;
        total_solution_num += current_solution_num;
        sub_solution_num_list.push(current_solution_num);
      }
      let methodFormData = {
        total_pre_num: this.rule_method.preconditions.length,
        preconditions: this.rule_method.preconditions,
        total_solution_num: total_solution_num,
        sub_solution_num_list: sub_solution_num_list,
        solution_ways: [],
      };
      let nodes = [
        {
          id: "1",
          type: "diamond",
          x: 100,
          y: 100,
          text: this.ruleFlow.defect_data[this.current_defect].defect_name,
          properties: {
            rule_name: this.ruleFlow.defect_data[this.current_defect].defect_desc,
          },
        },
      ];
      let edges = [];

      let current_pre_no = 1;
      let current_row = 1;
      let current_source_node_id = "1";
      let current_node_row = 1;
      for (let i = 1; i <= methodFormData.total_pre_num; i++) {
        let pre_node = {
          id: "2" + String(i),
          type: "diamond",
          x: 300,
          y: 100 * current_row,
          text: "检查\n" + methodFormData.preconditions[i - 1].keyword,
          properties: {
            rule_name: this.getValueForOption(methodFormData.preconditions[i - 1].keyword,this.normalKeywordOptions, 1),
            action:this.getValueForOption(methodFormData.preconditions[i - 1].status, this.paraLevelMap, 0)
          },
        };
        nodes.push(pre_node);

        let edge = {
          sourceNodeId: current_source_node_id,
          targetNodeId: "2" + String(i),
          type: "polyline",
        };
        edges.push(edge);

        let current_solution_no = methodFormData.sub_solution_num_list[i - 1];
        let s = 1;
        current_node_row = current_row
        for (s = 1; s <= current_solution_no; s++) {
          let solution_node = {
            id: "2" + String(i) + String(s),
            type: "rect",
            x: 500,
            y: 100 * current_row,
            text:
              methodFormData.preconditions[i - 1].solutions[s - 1].action +
              methodFormData.preconditions[i - 1].solutions[s - 1].keyword,
            properties: {
              rule_name:
                this.getValueForOption(methodFormData.preconditions[i - 1].solutions[s - 1].keyword,this.concludeKeywordOptions, 1),
              action:
                this.getValueForOption(methodFormData.preconditions[i - 1].solutions[s - 1].action, this.actionMap, 0),
            },
          };
          nodes.push(solution_node);

          // 只在第一条边增加text
          if(s == 1){
            let pointsList = [ { x: 330, y: 100 * current_node_row }, { x: 420, y: 100* current_node_row }, { x: 420, y: 100* current_row }, { x: 450, y: 100* current_row } ]
            edge = {
              sourceNodeId: "2" + String(i),
              targetNodeId: "2" + String(i) + String(s),
              type: "polyline",
              text:
                methodFormData.preconditions[i - 1].keyword +
                methodFormData.preconditions[i - 1].status,
              pointsList: pointsList,
            };
          }else if(s == 2){
            edge = {
              sourceNodeId: "2" + String(i),
              targetNodeId: "2" + String(i) + String(s),
              type: "polyline"
            };
          } else {
            let pointsList = [ { x: 330, y: 100 * current_node_row }, { x: 420, y: 100* current_node_row }, { x: 420, y: 100* current_row }, { x: 450, y: 100* current_row } ]
            edge = {
              sourceNodeId: "2" + String(i),
              targetNodeId: "2" + String(i) + String(s),
              type: "polyline",
              pointsList: pointsList,
            };         
          }
          edges.push(edge);

          let solution_way = [0, current_pre_no, current_pre_no + s];
          methodFormData.solution_ways.push(solution_way);
          current_row = current_row + 1;
        }
        if (current_solution_no == 1) {
          current_row = current_row + 1;
        }
        current_source_node_id = "2" + String(i);
        current_pre_no = current_pre_no + s;
      }
      let graph_data = {
        nodes: nodes,
        edges: edges,
      };
      this.ruleFlow.defect_data[this.current_defect].graph_data = graph_data
      this.ruleFlow.defect_data[this.current_defect].rule_method = methodFormData
      this.$emit("change-rule-flow", this.ruleFlow);
    },
    getValueForOption(value, options, group){
      if(value == "不良"||value == "不足"|| value=="过低"||value=="过短"||value=="过小"){
        return "low"
      }
      if(value == "过高"|| value=="过长"||value=="过大"){
        return "high"
      }
      if(value == "不合理"){
        return "worse"
      }
      for(let i=0;i<options.length;i++){
        if(group == 1){
          let inner_options = options[i]["options"]
          for(let j=0;j<inner_options.length;j++){
            if(value == inner_options[j].value){
              return inner_options[j].desc
            }    
          }
        } else {
          if(value == options[i].value){
            return options[i].desc
          }
        }
      }
    },
    resetRowValue(precondition, type) {
      if (type === "precondition") {
        precondition.keyword = null;
        precondition.describe = null;
      }
    },
    addPrecondition() {
      this.rule_method.preconditions.push({
        conditiontype: "普通前置条件",
        keyword: null,
        describe: null,
        solutions: [
          {
            conditiontype: "结论条件",
            keyword: null,
            describe: null,
            action: null,
          },
        ],
      });
    },
    subPrecondition(index) {
      this.rule_method.preconditions.splice(index, 1);
    },
    addSolution(idx) {
      this.rule_method.preconditions[idx].solutions.push({
        conditiontype: "结论条件",
        keyword: null,
        describe: null,
        action: null,
      });
      this.right_sum++;
    },
    subSolution(idx, index) {
      this.rule_method.preconditions[idx].solutions.splice(index, 1);
      this.right_sum--;
    },
    validateForm() {
      for (let i = 0; i < this.rule_method.preconditions.length; i++) {
        if (!this.rule_method.preconditions[i].conditiontype) {
          this.$message({
            type: "warning",
            message: "条件部分条件类型不能为空",
          });
          return false;
        }
        if (!this.rule_method.preconditions[i].keyword) {
          this.$message({
            type: "warning",
            message: "条件部分关键字不能为空",
          });
          return false;
        }
        if (!this.rule_method.preconditions[i].describe) {
          this.$message({
            type: "warning",
            message: "条件部分描述不能为空",
          });
          return false;
        }
      }
      return true;
    },
    cancel() {
      this.resetView();
    },
    resetView() {
      this.rule_method.polymer_abbreviation = null;
      this.rule_method.product_small_type = null;
      this.rule_method.preconditions = [
        {
          conditiontype: "普通前置条件",
          keyword: null,
          describe: null,
          solutions: [
            {
              conditiontype: "结论条件",
              keyword: null,
              describe: null,
              action: null,
            },
          ],
        },
      ];
      this.rule_method.rule_description = null;
      this.rule_method.rule_explanation = null;
      this.$emit("close-dialog");
    },
    normalKeywordChange(item){
      this.paraLevelMap = getParaLevel(item)
    }
  },
  computed: {},
  watch: {
    currentDefect: {
      handler(newVal) {
        this.current_defect = this.currentDefect;
        if(this.currentDefect < this.ruleFlow.defect_data.length){
          this.rule_method = this.ruleFlow.defect_data[this.currentDefect].rule_method;
        }
      },
      deep: true,
      // immediate: true,
    },
    ruleFlow: {
      handler() {
        this.rule_flow = this.ruleFlow;
        if(this.currentDefect < this.ruleFlow.defect_data.length){
          this.rule_method = this.ruleFlow.defect_data[this.currentDefect].rule_method;
        }
        this.$emit("change-flow",this.rule_flow)
      },
      deep: true,
      // immediate: true,
    },
    activeCollapse() {
      this.active_collapse = this.activeCollapse
    },
    isDefect() {
      this.is_defect = this.isDefect
    }
  },
};
</script>

<style scoped lang="scss">
.box {
  display: flex;
  justify-content: center;
  width: 100%;
}
.left {
  width: 50%;
}
.right {
  width: 50%;
}
.el-select {
  width: 7.5rem
}
</style>
