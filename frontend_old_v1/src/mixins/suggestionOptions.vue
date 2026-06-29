
<script>
import { getOptions } from "@/api"

export default {
  name: "SuggestionOptions",
  methods: {
    queryOptions(str, column, table) {
      str = str == null ? "": str
      let promptList = []
      if (column) {
        getOptions(column, { "form_input": str, "db_table": table })
        .then( res => {
          if(res.status == 0 && res.data) {
            res.data.forEach(element => {
              promptList.push({ value: element })
            })
          }
        })
      } 
      return promptList
    }
  }
}
</script>

