<script>
    export default {
        name: "ExtendObject",
      methods:{
          extendObject(objectlist){
            let data = {};
            let length = objectlist.length;
            for(let i = 0; i < length; ++ i){
              let objectitem = objectlist[i];
              if(typeof(objectitem) === "object"){
                for(let key in objectitem){
                  data[key] = objectitem[key];
                }
              }
            }
            return data;
          }
      }
    }
</script>

<style scoped>

</style>
