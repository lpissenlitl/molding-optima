<template>
  <el-button-group>
    <el-button
      size="small"
      :type="currentSize === 'small' ? 'primary' : ''"
      @click="$emit('update', 'small')"
    >
      小
    </el-button>
    <el-button
      size="small"
      :type="currentSize === 'default' ? 'primary' : ''"
      @click="$emit('update', 'default')"
    >
      中
    </el-button>
    <el-button
      size="small"
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
      default: "default"
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