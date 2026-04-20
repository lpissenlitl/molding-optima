<template>
  <div id="helpDoc">
    <svg-icon
      name="documentation"
      @click="click"
    />
  </div>
</template>

<script lang="ts">
import { Component, Vue } from 'vue-property-decorator'

@Component({
  name: 'HelpDoc'
})
export default class extends Vue {

  mounted() {

  }

  beforeDestory() {

  }

  private click() {
    this.$message({
      message: 'there are no docs',
      type: 'warning'
    })
    return false
  }
}
</script>
