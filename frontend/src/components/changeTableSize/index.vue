<template>
  <el-button-group>
    <el-button
      size="mini"
      :type="currentSize === 'small' ? 'primary' : ''"
      @click="$emit('update', 'small')"
    >
      小
    </el-button>
    <el-button
      size="mini"
      :type="currentSize === 'normal' ? 'primary' : ''"
      @click="$emit('update', 'normal')"
    >
      中
    </el-button>
    <el-button
      size="mini"
      :type="currentSize === 'large' ? 'primary' : ''"
      @click="$emit('update', 'large')"
    >
      大
    </el-button>
  </el-button-group>
</template>

<script>
export default {
  name: "ChangeTableSize",
  props: {
    size: {
      type: String,
      default: "normal"
    }
  },
  computed: {
    currentSize() {
      return this.size
    }
  },
}
</script>

<style>

</style>