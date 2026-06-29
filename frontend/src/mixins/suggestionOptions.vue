
<script>
import { getSelectionOptions } from "@/api"
import { UserModule } from "@/store/modules/user"

export default {
  name: "SuggestionOptions",
  methods: {
    async queryOptions(input_str, db_table, db_column, filter_cols = null) {
      input_str = input_str == null ? "" : input_str
      let selection_list = []
      if (!db_column) return selection_list
      // console.log(db_column)
      let condition = { 
        "company_id": UserModule.company_id,
        "organization_id": UserModule.organization_id,
        "db_table": db_table,
        "db_column": db_column,
        "input_str": input_str,
      }
      if (filter_cols != null) {
        condition = Object.assign({}, condition, filter_cols)
      }
      // console.log(condition)
      await getSelectionOptions(condition)
        .then( res => {
        // console.log(res)
          if (res.status == 0 && res.data) {
            selection_list = res.data
          }
        })
      return selection_list
    }
  }
}
</script>