export function ruleToKey(rule: string) {
    let rule_result = new Map()
    let conditionList:any = []
    let conclusionList:any = []
    let words_list = rule.replace(/[\r\n]/g,"").split(" ")
    console.log(words_list)
    let is_pre = false
    for(let i=0; i<words_list.length; i++) {
        if(words_list[i] === 'IF') {
            is_pre = true
        }
        else if(words_list[i] === 'Then' || words_list[i] ===  'THEN') {
            is_pre = false
        }
        else if(words_list[i] == 'AND') {
            continue
        }
        else{
            let words:Array<string> = words_list[i].split('_')
            console.log(words)
            if(is_pre) {
                let condition = { "conditiontype": "普通前置条件", "keyword": words[0], "describe": words[1] }

                if(["SHORTSHOT", "FLASH", "SHRINKAGE", "WELDLINE", "ABERRATION", "AIRTRAP"].indexOf(words[0]) === -1 ) {
                    // 工艺参数条件,键为参数名,值为参数模糊级别、条件类型
                    condition.conditiontype = "普通前置条件"
                }
                else{
                    // 缺陷类型条件,键为缺陷类型,值为缺陷严重程度、缺陷位置、条件类型
                    condition.conditiontype = "缺陷前置条件"
                }
                conditionList.push(condition)
                }                      
            else{
                // 工艺参数修正,键为参数名,值为参数调整方向、调整模糊级别、条件类型
                if(words.length === 3) {
                    let solution = { "conditiontype": "结论条件","keyword": words[0], "describe": words[2], "action": words[1] }
                    conclusionList.push(solution)   
                }
                if(words.length === 2) {
                    let solution = { "conditiontype": "结论条件","keyword": words[0], "describe": words[1] }
                    conclusionList.push(solution)    
                    }
                }
            }
    }
    console.log(conditionList)
    console.log(conclusionList)
    rule_result.set("conditionList", conditionList)
    rule_result.set("conclusionList", conclusionList)
    rule_result.set("rule", rule)
    return rule_result
  }
