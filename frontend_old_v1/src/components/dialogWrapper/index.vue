<template>
  <div class="from-wrapper" :style="{maxWidth: maxWidth+'px'}">
    <slot></slot>
  </div>
</template>

<script>
  export default {
    props: {
      maxWidth: {
        type: Number,
        default: 500
      }
    }
  }
</script>

<style lang="scss" scoped>
  .from-wrapper{
    margin: auto;
  }
</style>
