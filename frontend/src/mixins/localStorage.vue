
<script>
    export default {
      name: "LocalStorage",
      methods:{
        setStorageData(dataname, data){
          this.$saveLocalStorageObject(dataname, data);
        },
        loadStorageData(dataname, data){
          let storagedata = this.$getLocalStorageObject(dataname);
          for(let item in storagedata) {
            data[item] = storagedata[item];
          }
        },
        removeStorageData(dataname){
          this.$removeLocalStorage(dataname);
        }
      }
    }
</script>


