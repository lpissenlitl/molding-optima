<template>
  <el-dialog 
    v-el-drag-dialog
    width="80%"
    center
    :visible.sync="showDialog" 
    :show-update="showUpdate"
    :modal="true"
    :append-to-body="true"
    :close-on-click-modal="false"
    :lock-scroll="true"
    @close="closeDialog"
  >
    <div slot="title" class="header-title">
      <div style="font-size:25px; font-weight:bold">{{ title }}</div>
    </div>
    <template v-if="trialType == 'load_sensitivity'">
      <load-sensitivity
        ref="loadSensitivity"
        :id="id"
        @close="closeDialog"
      >
      </load-sensitivity>
    </template>
    <template v-else-if="trialType == 'check_ring_dynamic'">
      <check-ring-dynamic
        ref="checkRingDynamic"
        :id="id"
        @close="closeDialog"
      >
      </check-ring-dynamic>
    </template>
    <template v-else-if="trialType == 'check_ring_static'">
      <check-ring-static
        ref="checkRingStatic"
        :id="id"
        @close="closeDialog"
      >
      </check-ring-static>
    </template>
    <template v-else-if="trialType == 'inject_velocity_linearity'">
      <inject-velocity-linearity
        ref="injectVelocityLinearity"
        :id="id"
        @close="closeDialog"
      >
      </inject-velocity-linearity>
    </template>
    <template v-else-if="trialType == 'stability_assessment'">
      <stability-assessment
        ref="stabilityAssessment"
        :id="id"
        @close="closeDialog"
      >
      </stability-assessment>
    </template>
    <template v-else-if="trialType == 'mould_board_deflection'">
      <mould-board-deflection
        ref="mouldBoardDeflection"
        :id="id"
        @close="closeDialog"
      >
      </mould-board-deflection>
    </template>
    <template v-else-if="trialType == 'screw_wear'">
      <screw-wear
        ref="screwWear"
        :id="id"
        @close="closeDialog"
      >
      </screw-wear>
    </template>
  </el-dialog>
</template>

<script>
import LoadSensitivity from "./loadSensitivity.vue"
import CheckRingDynamic from "./checkRingDynamic.vue"
import CheckRingStatic from "./checkRingStatic.vue"
import InjectVelocityLinearity from "./injectVelocityLinearity.vue"
import StabilityAssessment from "./stabilityAssessment.vue"
import MouldBoardDeflection from "./mouldBoardDeflection.vue"
import ScrewWear from "./screwWear.vue"

export default {
  name: "MachineTrialDetail",
  components: { 
    LoadSensitivity, 
    CheckRingDynamic, 
    CheckRingStatic, 
    InjectVelocityLinearity, 
    StabilityAssessment, 
    MouldBoardDeflection,
    ScrewWear
  },
  props: {
    showUpdate: {
      type: Boolean,
      default: false
    },
    id: {
      type: Number,
      default: null
    },
    viewType: {
      type: String,
      default: null
    },
    trialType: {
      type: String,
      default: null
    }
  },
  data() {
    return {
      title: "",
      showDialog: this.showUpdate,
    }
  },
  methods: {
    closeDialog() {
      if (this.trialType == "load_sensitivity") {
        this.$refs["loadSensitivity"].resetView()
      } else if (this.trialType == "check_ring_dynamic") {
        this.$refs["checkRingDynamic"].resetView()
      } else if (this.trialType == "check_ring_static") {
        this.$refs["checkRingStatic"].resetView()
      } else if (this.trialType == "inject_velocity_linearity") {
        this.$refs["injectVelocityLinearity"].resetView()
      } else if (this.trialType == "stability_assessment") {
        this.$refs["stabilityAssessment"].resetView()
      } else if (this.trialType == "mould_board_deflection") {
        this.$refs["mouldBoardDeflection"].resetView()
      }else if (this.trialType == "screw_wear") {
        this.$refs["screwWear"].resetView()
      }
      this.$emit('close')
    }
  },
  watch: {
    showUpdate() {
      this.showDialog = this.showUpdate
    },
  }
}
</script>

<style lang="scss" scoped>

</style>
