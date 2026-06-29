import { getSelectionOptions } from "@/api"


// 回调函数格式
type callback = (suggestions: ({ value: string } & Record<string, any>)[]) => void

interface SelectOption {
  value: string|number;
  label: string|number;
}

type DataItem = {
  value: string; 
} & Record<any, any>;

// 查询建议
export function querySuggestions(params: object, options: Array<SelectOption>|null) {
  return (input: string, cb: callback) => {
    input = input ? input.trim() : ""
    getSelectionOptions({
      ...params,
      input: input
    }).then(res => {
      let suggestions = []
      if (res.status === 0) {
        if (options) {
          //先将options转化为map，使optionsMap[value]能获取到对应的label
          const optionsMap:Record<string|number, string|number> = {}
          options.forEach((option)=>{
            optionsMap[option.value] = option.label
          })
          const result:Array<DataItem> = res.data
          result.forEach(element => {
            suggestions.push({ value:optionsMap[element.value] || element.value })
          })
        } else {
          suggestions = res.data
        }
      }
      cb(suggestions)
    })
  }
}
                