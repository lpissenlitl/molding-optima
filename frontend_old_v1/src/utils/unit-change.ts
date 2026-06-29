export function conversion(original_unit: string, converted_unit: string, original_value: number, injector_info: any, convert_type?:string) {
    let VALID_NUMBER = 2
    if (!original_value) {
    } else if (!injector_info) {
    }
    else if (original_unit && converted_unit && original_unit.toLowerCase() == converted_unit.toLowerCase()) {
        return original_value
    } else if (original_value && injector_info) {
            
        if (original_unit == "mm/s" && converted_unit == "inch/s") {
            // 速度转换
            return (original_value / 25.4).toFixed(VALID_NUMBER)
        } else if (original_unit == "inch/s" && converted_unit == "mm/s") {
            return (original_value * 25.4).toFixed(VALID_NUMBER)
        } else if (original_unit == "inch/s" && converted_unit == "cm³/s") {
            return (original_value * 25.4 * getScrewArea(injector_info) / 1000).toFixed(VALID_NUMBER)
        } else if (original_unit == "cm³/s" && converted_unit == "inch/s") {
            return (original_value / 25.4 / getScrewArea(injector_info) * 1000).toFixed(VALID_NUMBER)
        } else if (original_unit == "mm/s" && converted_unit == "inch³/s" && getScrewArea(injector_info)) {
             // 速度和速率之间的转换,需要用到螺杆面积
            return (original_value * getScrewArea(injector_info)/ 25.4/ 25.4/ 25.4).toFixed(VALID_NUMBER)
        } else if (original_unit == "inch³/s" && converted_unit == "mm/s" && getScrewArea(injector_info)) {
            return (original_value / getScrewArea(injector_info)* 25.4* 25.4* 25.4).toFixed(VALID_NUMBER)

        } else if (original_unit == "inch³/s" && converted_unit == "cm³/s" && getScrewArea(injector_info)) {
            return (original_value * 25.4* 25.4* 25.4 / 1000).toFixed(VALID_NUMBER)

        } else if (original_unit == "cm³/s" && converted_unit == "mm/s" && getScrewArea(injector_info)) {
            return (original_value / getScrewArea(injector_info) * 1000).toFixed(VALID_NUMBER)

        } else if (original_unit == "mm/s" && converted_unit == "cm³/s" && getScrewArea(injector_info)) {
            return (original_value * getScrewArea(injector_info) / 1000).toFixed(VALID_NUMBER)

        } else if (original_unit == "cm³/s" && converted_unit == "%") {
            // 在速率转换%时,需要用到最大速率,需要convert_type来区分是保压,注射还是射退, 单位是cm³/s
            if(convert_type == "injection"){
                return caculateRateToPercent(original_value, injector_info.max_injection_rate, injector_info.max_injection_velocity, injector_info, "注射", VALID_NUMBER)
            }
            if(convert_type == "holding"){
                return caculateRateToPercent(original_value, injector_info.max_holding_rate, injector_info.max_holding_velocity, injector_info, "保压", VALID_NUMBER)
            }
            if(convert_type == "decompressure"){
                return caculateRateToPercent(original_value, injector_info.max_decompression_rate, injector_info.max_decompression_velocity, injector_info, "射退", VALID_NUMBER)
            }
        } else if (original_unit == "%" && converted_unit == "mm/s") {
            // 最大开模/合模/顶进/顶退速度 单位是mm/s
            if(convert_type == "opening"){
                return caculatePercentToValue(original_value, injector_info.max_mold_opening_velocity, "开模速度", VALID_NUMBER)
            }
            if(convert_type == "clamping"){
                return caculatePercentToValue(original_value, injector_info.max_mold_clamping_velocity, "合模速度", VALID_NUMBER)
            }
            if(convert_type == "forward"){
                return caculatePercentToValue(original_value, injector_info.max_ejector_forward_velocity, "顶进速度", VALID_NUMBER)
            }
            if(convert_type == "backward"){
                return caculatePercentToValue(original_value, injector_info.max_ejector_backward_velocity, "顶退速度", VALID_NUMBER)
            }
            if(convert_type == "injection"){
                return caculatePercentToValue(original_value, injector_info.max_injection_velocity, "注射速度", VALID_NUMBER)
            }
            if(convert_type == "holding"){
                return caculatePercentToValue(original_value, injector_info.max_holding_velocity, "保压速度", VALID_NUMBER)
            }
            if(convert_type == "decompressure"){
                return caculatePercentToValue(original_value, injector_info.max_decompression_velocity, "射退速度", VALID_NUMBER)
            }
        } else if (original_unit == "mm/s" && converted_unit == "%") {
            if(convert_type == "opening"){
                return caculateValueToPercent(original_value, injector_info.max_mold_opening_velocity, "开模速度", VALID_NUMBER)
            }
            if(convert_type == "clamping"){
                return caculateValueToPercent(original_value, injector_info.max_mold_clamping_velocity, "合模速度", VALID_NUMBER)
            }
            if(convert_type == "forward"){
                return caculateValueToPercent(original_value, injector_info.max_ejector_forward_velocity, "顶进速度", VALID_NUMBER)
            }
            if(convert_type == "backward"){
                return caculateValueToPercent(original_value, injector_info.max_ejector_backward_velocity, "顶退速度", VALID_NUMBER)
            }            
            if(convert_type == "injection"){
                return caculateValueToPercent(original_value, injector_info.max_injection_velocity, "注射速度", VALID_NUMBER)
            }
            if(convert_type == "holding"){
                return caculateValueToPercent(original_value, injector_info.max_holding_velocity, "保压速度", VALID_NUMBER)
            }
            if(convert_type == "decompressure"){
                return caculateValueToPercent(original_value, injector_info.max_decompression_velocity, "射退速度", VALID_NUMBER)
            }
        } else if (original_unit == "%" && converted_unit == "cm³/s") {
            // 最大注射速率 单位是cm³/s
            if(convert_type == "injection"){
                return caculatePercentToRate(original_value, injector_info.max_injection_rate, injector_info.max_injection_velocity, injector_info, "注射", VALID_NUMBER)
            }
            if(convert_type == "holding"){
                return caculatePercentToRate(original_value, injector_info.max_holding_rate, injector_info.max_holding_velocity, injector_info, "保压", VALID_NUMBER)
            }
            if(convert_type == "decompressure"){
                return caculatePercentToRate(original_value, injector_info.max_decompression_rate, injector_info.max_decompression_velocity, injector_info, "射退", VALID_NUMBER)
            }
            // 位置转换
        } else if (original_unit == "mm" && converted_unit == "inch") {
            return (original_value / 25.4).toFixed(VALID_NUMBER)
        } else if (original_unit == "inch" && converted_unit == "mm") {
            return (original_value * 25.4).toFixed(VALID_NUMBER)
            // 位置和体积之间的转换,需要用到螺杆面积 
        } else if (original_unit == "mm" && converted_unit == "inch³" && getScrewArea(injector_info)) {
            return (original_value * getScrewArea(injector_info)/ 25.4/ 25.4/ 25.4).toFixed(VALID_NUMBER)
        } else if (original_unit == "inch³" && converted_unit == "mm" && getScrewArea(injector_info)) {
            return (original_value / getScrewArea(injector_info)* 25.4* 25.4* 25.4).toFixed(VALID_NUMBER)

        } else if (original_unit == "cm³" && converted_unit == "mm" && getScrewArea(injector_info)) {
            return (original_value / getScrewArea(injector_info) * 1000).toFixed(VALID_NUMBER)
        } else if (original_unit == "mm" && converted_unit == "cm³" && getScrewArea(injector_info)) {
            return (original_value * getScrewArea(injector_info) / 1000).toFixed(VALID_NUMBER)

        } else if (original_unit == "cm/s" && converted_unit == "rpm" && getScrewCircumference(injector_info)) {
            // 螺杆转速,需要用到螺杆周长
            return (original_value / getScrewCircumference(injector_info) * 10 * 60).toFixed(VALID_NUMBER)
        } else if (original_unit == "cm/s" && converted_unit == "%") {
            // 最大可设定螺杆转速线速度 单位 是cm/s
            if(injector_info.max_screw_linear_velocity){
                return (original_value / injector_info.max_screw_linear_velocity * 100).toFixed(VALID_NUMBER + 1)
            } else if(injector_info.max_screw_rotation_speed){
                let max_screw_linear_velocity:any = conversion("rpm", "cm/s", injector_info.max_screw_rotation_speed, injector_info)
                return (original_value / max_screw_linear_velocity * 100).toFixed(VALID_NUMBER + 1)
            }
        } else if (original_unit == "%" && converted_unit == "cm/s") {
            // 最大可设定螺杆转速线速度 单位 是cm/s
            if(injector_info.max_screw_linear_velocity){
                return (original_value * injector_info.max_screw_linear_velocity / 100).toFixed(VALID_NUMBER + 1)
            } else if(injector_info.max_screw_rotation_speed){
                let max_screw_linear_velocity:any = conversion("rpm", "cm/s", injector_info.max_screw_rotation_speed, injector_info)
                return (original_value * max_screw_linear_velocity / 100).toFixed(VALID_NUMBER + 1)
            }
        } else if (original_unit == "rpm" && converted_unit == "cm/s" && getScrewCircumference(injector_info)) {
            return (original_value * getScrewCircumference(injector_info) / 10 / 60).toFixed(VALID_NUMBER)
        } else if (original_unit == "rpm" && converted_unit == "mm/s" && getScrewCircumference(injector_info)) {
            return (original_value * getScrewCircumference(injector_info) / 60).toFixed(VALID_NUMBER)
        } else if (original_unit == "rpm" && converted_unit == "m/s" && getScrewCircumference(injector_info)) {
            return (original_value * getScrewCircumference(injector_info) / 60/1000).toFixed(VALID_NUMBER)
        }
        else if (original_unit == "rpm" && converted_unit == "inch/s" && getScrewCircumference(injector_info)) {
            return (original_value * getScrewCircumference(injector_info) / 60/25.4).toFixed(VALID_NUMBER)
        }
        else if (original_unit == "cm/s" && converted_unit == "m/min") {
            return (original_value  * getScrewCircumference(injector_info)).toFixed(VALID_NUMBER)
        }
        else if (original_unit == "rpm" && converted_unit == "m/min") {
            return (original_value / 100 * 60).toFixed(VALID_NUMBER)
            // 时间转换
        } else if (original_unit == "μs" && converted_unit == "s") {
            return (original_value / 1000000.0).toFixed(VALID_NUMBER)
        } else if (original_unit == "s" && converted_unit == "μs") {
            return (original_value * 1000000.0).toFixed(VALID_NUMBER)
        }   // 温度转换 
        else if (original_unit == "℃" && converted_unit == "℉") {
            return (original_value *1.8 +32).toFixed(VALID_NUMBER)
        } else if (original_unit == "℉" && converted_unit == "℃") {
            return ((original_value -32)/1.8).toFixed(VALID_NUMBER)
        } else {
            console.log("没有合适的转换 转之前的单位 "+original_unit+"转之后的单位"+converted_unit+" 转换之前的值"+original_value)
        }
    }
    return null
}

export function getCylinderArea(injector_info: any) {
    let cylinder_area = null
    if (injector_info.cylinder_numer && injector_info.cylinder_diameter) {
        if (injector_info.use_small_size) {
            cylinder_area = Number(injector_info.cylinder_numer) * 3.141592653589793 * Number(injector_info.cylinder_diameter) * Number(injector_info.cylinder_diameter) / 4
        } else {
            cylinder_area = Number(injector_info.cylinder_numer) * (
                3.141592653589793 * Number(injector_info.cylinder_diameter) * Number(injector_info.cylinder_diameter) / 4 - 3.141592653589793 * Number(injector_info.piston_rod_diameter) * Number(injector_info.piston_rod_diameter) / 4)
        }
    }
    return cylinder_area
}

export function getScrewArea(injector_info: any) {
    if (injector_info.screw_diameter) {
        let area = 3.141592653589793 * Number(injector_info.screw_diameter) * Number(injector_info.screw_diameter) / 4
        return area
    } else{
        console.log("注意:返回螺杆面积为1")
        return 1
    }
}

export function getScrewCircumference(injector_info: any) {
    if (injector_info.screw_diameter) {
        return 3.141592653589793 * Number(injector_info.screw_diameter)
    } else {
        console.log("注意:返回螺杆周长为1")
        return 1
    }
}

export function changeVelocityToRate(velocity:number, injector_info:any) {
    let volume:any = conversion("mm/s", "cm³/s", velocity, injector_info)
    return volume
}

export function caculateRateToPercent(original_value:number, rate:number, velocity:number, injector_info:any, convert_type:string, VALID_NUMBER:number){
    // 检查最大(注射/保压/射退)速率是否存在
    if(rate && Number(rate)!==0){
        return (original_value / rate * 100).toFixed(VALID_NUMBER)
    }
    else if(velocity && Number(velocity)!==0){
        return (original_value / changeVelocityToRate(velocity, injector_info) * 100).toFixed(VALID_NUMBER)
    } else{
        console.log("最大"+convert_type+"速度为空或为0 "+ velocity)
        return null
    }
}

export function caculatePercentToRate(original_value:number, rate:number, velocity:number, injector_info:any, convert_type:string, VALID_NUMBER:number){
    // 检查最大(注射/保压/射退)速率是否存在
    if(rate && Number(rate)!==0){
        return (original_value * rate / 100).toFixed(VALID_NUMBER)
    }
    else if(velocity && Number(velocity)!==0){
        console.log("最大"+convert_type+"速率为空或为0 "+ rate)
        console.log("用最大"+convert_type+"速度计算 最大注射速率")
        return (original_value * changeVelocityToRate(velocity, injector_info) / 100).toFixed(VALID_NUMBER)
    } else{
        console.log("最大"+convert_type+"速度为空或为0 "+ velocity)
        return null
    }
}

export function caculateValueToPercent(original_value:number, max:number, convert_type:string, VALID_NUMBER:number){
    // 检查最大(开模/合模/顶进/顶退)速度是否存在
    if(max && Number(max)!==0){
        return (original_value / max * 100).toFixed(VALID_NUMBER)
    } else{
        console.log("最大"+convert_type+"为空或为0 "+ max)
        return null
    }
}

export function caculatePercentToValue(original_value:number, max:number, convert_type:string, VALID_NUMBER:number){
    // 检查最大(开模/合模/顶进/顶退)速度是否存在
    if(max && Number(max)!==0){
        return (original_value * max / 100).toFixed(VALID_NUMBER)
    } else{
        console.log("最大"+convert_type+"为空或为0 "+ max)
        return null
    }
}

export function getPressureCoefficient(injector_info: any, convert_type: string){
    // return 10*getScrewArea(injector_info)/Number(getCylinderArea(injector_info))
    // 注射压力
    if (convert_type =="injection_pressure"){
        return injector_info.max_set_injection_pressure/injector_info.max_injection_pressure
    }
    // 保压压力
    if (convert_type =="holding_pressure"){
        return injector_info.max_set_holding_pressure/injector_info.max_holding_pressure
    }
        // 计量压力
    if (convert_type =="metering_pressure"){
        return injector_info.max_set_metering_pressure/injector_info.max_metering_pressure
    }
        // 松退压力
    if (convert_type =="decompression_pressure"){
        return injector_info.max_set_decompression_pressure/injector_info.max_decompression_pressure

    }
}


export function pressureConversion(original_unit: string, converted_unit: string, original_value: number, injector_info: any, convert_type?:string){
    // 压力转换
    // 1kg/cm2 =14.223psi
    // 1bar=14.5psi
    // 1MPa=145psi
    let VALID_NUMBER = 2
    if (original_unit == "PSI" && converted_unit == "kgf/cm²") {
        return (14.223 * original_value).toFixed(VALID_NUMBER)
    } else if (original_unit   == "kgf/cm²" && converted_unit == "PSI") {
        return (original_value/14.223).toFixed(VALID_NUMBER)
    } else if (original_unit   == "PSI" && converted_unit == "bar") {
        return (14.5 * original_value).toFixed(VALID_NUMBER)
    } else if (original_unit   == "PSI" && converted_unit == "MPa") {
        return (145 * original_value).toFixed(VALID_NUMBER)
    } else if (original_unit == "bar" && converted_unit   == "PSI") {
        return (original_value/14.5).toFixed(VALID_NUMBER)
    } else if (original_unit == "MPa" && converted_unit   == "PSI") {
        return (original_value/145).toFixed(VALID_NUMBER)

    } else if (original_unit == "kgf/cm²" && converted_unit == "bar") {
        return (original_value/0.98).toFixed(VALID_NUMBER)
    } else if (original_unit == "MPa" && converted_unit == "bar") {
        return (original_value * 10).toFixed(VALID_NUMBER)

    } else if (original_unit == "bar" && converted_unit == "kgf/cm²") {
        return (0.98 * original_value).toFixed(VALID_NUMBER)
    }
    else if (original_unit == "MPa" && converted_unit == "kgf/cm²") {
        return (9.8 * original_value).toFixed(VALID_NUMBER)
    }
    else if (original_unit == "bar" && converted_unit == "MPa") {
        return (original_value / 10).toFixed(VALID_NUMBER)
    }
    else if (original_unit == "kgf/cm²" && converted_unit == "MPa") {
        return (original_value/9.8).toFixed(VALID_NUMBER)
    } 
    else if ((original_unit == "MPa"||original_unit == "bar"||original_unit == "kgf/cm²"||original_unit == "PSI" )&& converted_unit == "%") {
        // 在压力转换%时,需要用到最大压力,需要convert_type来区分是保压,注射还是射退, 单位是MPa
        if(original_unit != "MPa"){
            original_value = Number(conversion(original_unit, "MPa", original_value, injector_info))
        }
        if(convert_type == "injection"){
            return caculateValueToPercent(original_value, injector_info.max_injection_pressure, "注射压力", VALID_NUMBER)
        }
        if(convert_type == "holding"){
            return caculateValueToPercent(original_value, injector_info.max_holding_pressure, "保压压力", VALID_NUMBER)
        }
        if(convert_type == "metering"){
            return caculateValueToPercent(original_value, injector_info.max_metering_pressure, "计量压力", VALID_NUMBER)
        }
        if(convert_type == "decompressure"){
            return caculateValueToPercent(original_value, injector_info.max_decompression_pressure, "松退压力", VALID_NUMBER)
        }
        if(convert_type == "backpressure"){
            return caculateValueToPercent(original_value, injector_info.max_metering_back_pressure, "背压", VALID_NUMBER)
        }
    } else if ((converted_unit == "MPa"||converted_unit == "bar"||converted_unit == "kgf/cm²"||converted_unit == "PSI" )&& original_unit == "%") {
        // 在压力转换%时,需要用到最大压力,需要convert_type来区分是保压,注射还是射退, 单位是MPa
        let converted_value = 0
        if(convert_type == "injection" && injector_info.max_injection_pressure){
            converted_value = Number(caculateValueToPercent(original_value, injector_info.max_injection_pressure, "注射压力", VALID_NUMBER))
        }
        if(convert_type == "holding"&& injector_info.max_holding_pressure){
            converted_value = Number(caculateValueToPercent(original_value, injector_info.max_holding_pressure, "保压压力", VALID_NUMBER))
        }
        if(convert_type == "decompressure"&& injector_info.max_decompression_pressure){
            converted_value = Number(caculateValueToPercent(original_value, injector_info.max_decompression_pressure, "松退压力", VALID_NUMBER))
        }
        if(convert_type == "backpressure"&& injector_info.max_metering_back_pressure){
            converted_value = Number(caculateValueToPercent(original_value, injector_info.max_metering_back_pressure, "背压", VALID_NUMBER))
        }
        if(converted_unit != "MPa"){
            converted_value = Number(conversion(original_unit, "MPa", converted_value, injector_info))
        }
        return converted_value
    }
}