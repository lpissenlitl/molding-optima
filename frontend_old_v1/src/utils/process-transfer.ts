import { conversion, getScrewArea, getScrewCircumference, changeVelocityToRate } from '@/utils/unit-change'

let current_VP_switch_position: any = null

// 工艺参数转换
export function processTransfer(
    origin_machine: any,
    origin_process: any,
    transplant_machine: any,
    transplant_process: any,
    VP_switch_position: any,
) {
    current_VP_switch_position = VP_switch_position
    // 转换之前,先检查参数是否齐全
    // checkValid(origin_machine)
    // checkValid(transplant_machine)
    // 注射参数
    transplant_process.inject_para.injection_stage = origin_process.inject_para.injection_stage
    for (let row = 0; row < 3; ++row)
        for (let col = 0; col < transplant_process.inject_para.injection_stage; ++col) {
            if (row == 0)
                transplant_process.inject_para.table_data[row].sections[col] = transferInjectionPressure(origin_process.inject_para.table_data[row].sections[col], 
                origin_machine.max_set_injection_pressure, origin_machine.max_injection_pressure, 
                transplant_machine.max_set_injection_pressure, transplant_machine.max_injection_pressure)
            else if (row == 1)
                transplant_process.inject_para.table_data[row].sections[col] = transferVelocity(origin_machine.velocity_unit, transplant_machine.velocity_unit, origin_process.inject_para.table_data[row].sections[col], origin_machine, transplant_machine, "injection")
            // transferInjectionVelocity(origin_process.inject_para.table_data[row].sections[col], 
            //     origin_machine.max_set_injection_velocity, origin_machine.max_injection_velocity, 
            //     transplant_machine.max_set_injection_velocity, transplant_machine.max_injection_velocity, 
            //     origin_machine.screw_diameter, transplant_machine.screw_diameter,
            //     origin_machine, transplant_machine)
            else if (row == 2)
                transplant_process.inject_para.table_data[row].sections[col] = transferPosition(origin_process, origin_machine.position_unit, transplant_machine.position_unit, origin_process.inject_para.table_data[row].sections[col], origin_machine, transplant_machine)
            // transferInjectionPosition(origin_process.inject_para.table_data[row].sections[col], 
            //     origin_machine.screw_diameter, transplant_machine.screw_diameter)

        }
    transplant_process.inject_para.injection_time = origin_process.inject_para.injection_time
    transplant_process.inject_para.injection_delay_time = origin_process.inject_para.injection_delay_time
    transplant_process.inject_para.cooling_time = origin_process.inject_para.cooling_time

    // 保压参数
    transplant_process.holding_para.holding_stage = origin_process.holding_para.holding_stage
    for (let row = 0; row < 3; ++row)
        for (let col = 0; col < transplant_process.holding_para.holding_stage; ++col) {
            if (row == 0)
                transplant_process.holding_para.table_data[row].sections[col] = transferHoldingPressure(origin_process.holding_para.table_data[row].sections[col], 
                origin_machine.max_set_holding_pressure, origin_machine.max_holding_pressure, 
                transplant_machine.max_set_holding_pressure, transplant_machine.max_holding_pressure)
            else if (row == 1)
            // 保压速度设定为注塑机最大可设定的30%
                transplant_process.holding_para.table_data[row].sections[col] = (transplant_machine.max_set_holding_velocity *0.3).toFixed(1)
                //transferVelocity(origin_machine.velocity_unit, transplant_machine.velocity_unit, origin_process.holding_para.table_data[row].sections[col], origin_machine, transplant_machine, "holding")
            // transferHoldingVelocity(origin_process.holding_para.table_data[row].sections[col], 
            //     origin_machine.max_set_holding_velocity, origin_machine.max_holding_velocity, 
            //     transplant_machine.max_set_holding_velocity, transplant_machine.max_holding_velocity, 
            //     origin_machine.screw_diameter, transplant_machine.screw_diameter,
            //     origin_machine, transplant_machine)
            else if (row == 2)
                transplant_process.holding_para.table_data[row].sections[col] = origin_process.holding_para.table_data[row].sections[col]

        }
    // vp切换
    transplant_process.VP_switch.VP_switch_mode = origin_process.VP_switch.VP_switch_mode
    // V/P切换位置设定为最大螺杆行程的20%,或者是由工程师自主设定
    transplant_process.VP_switch.VP_switch_position = VP_switch_position
    // (transplant_machine.max_injection_stroke * 0.2).toFixed(2)
    // transferPosition(origin_process, origin_machine.position_unit, transplant_machine.position_unit, origin_process.VP_switch.VP_switch_position, origin_machine, transplant_machine)
    // transferInjectionPosition(origin_process.VP_switch.VP_switch_position, 
    //     origin_machine.screw_diameter, transplant_machine.screw_diameter)
    transplant_process.VP_switch.VP_switch_time = origin_process.VP_switch.VP_switch_time
    transplant_process.VP_switch.VP_switch_pressure = origin_process.VP_switch.VP_switch_pressure
    transplant_process.VP_switch.VP_switch_velocity = transferVelocity(origin_machine.velocity_unit, transplant_machine.velocity_unit, origin_process.VP_switch.VP_switch_velocity, origin_machine, transplant_machine, "injection")
    // transferInjectionVelocity(origin_process.VP_switch.VP_switch_velocity, 
    //     origin_machine.max_set_injection_velocity, origin_machine.max_injection_velocity, 
    //     transplant_machine.max_set_injection_velocity, transplant_machine.max_injection_velocity, 
    //     origin_machine.screw_diameter, transplant_machine.screw_diameter,
    //     origin_machine, transplant_machine)

    // 计量参数
    transplant_process.metering_para.metering_stage = origin_process.metering_para.metering_stage
    for (let row = 0; row < 4; ++row)
        for (let col = 0; col < transplant_process.metering_para.metering_stage; ++col) {
            if (row == 0){
                // 全电转液压时,需要增加计量压力,75%*最大计量压力
                // 全电转全电,不计算计量压力
                // 如果转换之前的计量压力为空,转换之后的机台动力方式为液压,油压,油电混等
                if(origin_machine.power_method == "电动机" && (transplant_machine.power_method.indexOf("液压机") != -1 || transplant_machine.power_method.indexOf("油压") != -1|| transplant_machine.power_method.indexOf("油电混") != -1|| transplant_machine.power_method.indexOf("电动/油压") != -1)){
                    if(!origin_process.metering_para.table_data[row].sections[col]){
                        let original_value = 0.75*transplant_machine.max_metering_pressure
                        transplant_process.metering_para.table_data[row].sections[col] = conversion("MPa", transplant_machine.pressure_unit, original_value, transplant_machine, "metering")
                    }

                }else if(origin_machine.power_method == "液压机"&&transplant_machine.power_method== "液压机"){
                    // 液压转液压,正常用公式计算
                    transplant_process.metering_para.table_data[row].sections[col] = transferMeteringPressure(origin_process.metering_para.table_data[row].sections[col], 
                        origin_machine.max_set_metering_pressure, origin_machine.max_metering_pressure, 
                        transplant_machine.max_set_metering_pressure, transplant_machine.max_metering_pressure)
                }
            }
            else if (row == 1)
                transplant_process.metering_para.table_data[row].sections[col] = transferRotation(origin_machine.screw_rotation_unit, transplant_machine.screw_rotation_unit, origin_process.metering_para.table_data[row].sections[col], origin_machine, transplant_machine)
            else if (row == 2)
                transplant_process.metering_para.table_data[row].sections[col] = transferMeteringBackPressure(origin_process.metering_para.table_data[row].sections[col], 
                origin_machine.max_set_metering_back_pressure, origin_machine.max_metering_back_pressure, 
                transplant_machine.max_set_metering_back_pressure, transplant_machine.max_metering_back_pressure)
            else if (row == 3)
                transplant_process.metering_para.table_data[row].sections[col] = transferPosition(origin_process, origin_machine.position_unit, transplant_machine.position_unit, origin_process.metering_para.table_data[row].sections[col], origin_machine, transplant_machine)
        }

    transplant_process.metering_para.decompressure_mode_before_metering = origin_process.metering_para.decompressure_mode_before_metering
    transplant_process.metering_para.decompressure_mode_after_metering = origin_process.metering_para.decompressure_mode_after_metering

    for (let row = 0; row < 2; ++row) {
        console.log(origin_machine.max_set_decompression_pressure, origin_machine.max_decompression_pressure, 
            transplant_machine.max_set_decompression_pressure, transplant_machine.max_decompression_pressure)
        transplant_process.metering_para.decompressure_paras[row].pressure = transferDecompressionPressure(origin_process.metering_para.decompressure_paras[row].pressure, 
            origin_machine.max_set_decompression_pressure, origin_machine.max_decompression_pressure, 
            transplant_machine.max_set_decompression_pressure, transplant_machine.max_decompression_pressure)

        transplant_process.metering_para.decompressure_paras[row].velocity = transferVelocity(origin_machine.velocity_unit, transplant_machine.velocity_unit, origin_process.metering_para.decompressure_paras[row].velocity, origin_machine, transplant_machine, "decompressure")

        transplant_process.metering_para.decompressure_paras[row].distance = transferDecompressurePosition(origin_machine.position_unit, transplant_machine.position_unit, origin_process.metering_para.decompressure_paras[row].distance, origin_machine, transplant_machine)

        transplant_process.metering_para.decompressure_paras[row].time = origin_process.metering_para.decompressure_paras[row].time
    }

    transplant_process.metering_para.metering_delay_time = origin_process.metering_para.metering_delay_time
    transplant_process.metering_para.metering_ending_position = transferPosition(origin_process, origin_machine.position_unit, transplant_machine.position_unit, origin_process.metering_para.metering_ending_position, origin_machine, transplant_machine)

    // 料筒温度
    if(transplant_machine.max_temperature_stage && transplant_machine.max_temperature_stage >= origin_process.temp_para.barrel_temperature_stage||!transplant_machine.max_temperature_stage){
        transplant_process.temp_para.barrel_temperature_stage = origin_process.temp_para.barrel_temperature_stage
        for (let col = 0; col < origin_process.temp_para.barrel_temperature_stage; ++col) {
            transplant_process.temp_para.table_data[0].sections[col] = origin_process.temp_para.table_data[0].sections[col]       
        }
    }else{
        transplant_process.temp_para.barrel_temperature_stage = transplant_machine.max_temperature_stage
        let difference = origin_process.temp_para.table_data[0].sections[0] - origin_process.temp_para.table_data[0].sections[origin_process.temp_para.barrel_temperature_stage-1]
        let step = difference / (transplant_process.temp_para.barrel_temperature_stage - 1)
        for (let col = 0; col < transplant_machine.max_temperature_stage; ++col) {
            transplant_process.temp_para.table_data[0].sections[col] = (origin_process.temp_para.table_data[0].sections[0] - col*step).toFixed(0)
        }
    }

    //顶针
    transplant_process.ejector_setting.ejector_backward.ejector_backward_stage = origin_process.ejector_setting.ejector_backward.ejector_backward_stage
    transplant_process.ejector_setting.ejector_forward.ejector_forward_stage = origin_process.ejector_setting.ejector_forward.ejector_forward_stage
    for (let row = 0; row < 3; ++row)
        for (let col = 0; col < 8; ++col) {
            if (row == 0)
                transplant_process.ejector_setting.ejector_backward.table_data[row].sections[col] = origin_process.ejector_setting.ejector_backward.table_data[row].sections[col]
            else if (row == 1)
                transplant_process.ejector_setting.ejector_backward.table_data[row].sections[col] = transferOCVelocity(origin_machine.oc_velocity_unit, transplant_machine.oc_velocity_unit, origin_process.ejector_setting.ejector_backward.table_data[row].sections[col], origin_machine, transplant_machine, "backward")
            else if (row == 2)
                transplant_process.ejector_setting.ejector_backward.table_data[row].sections[col] = origin_process.ejector_setting.ejector_backward.table_data[row].sections[col]

        }
    for (let row = 0; row < 3; ++row)
        for (let col = 0; col < 8; ++col) {
            if (row == 0)
                transplant_process.ejector_setting.ejector_forward.table_data[row].sections[col] = origin_process.ejector_setting.ejector_forward.table_data[row].sections[col]
            else if (row == 1)
                transplant_process.ejector_setting.ejector_forward.table_data[row].sections[col] = transferOCVelocity(origin_machine.oc_velocity_unit, transplant_machine.oc_velocity_unit, origin_process.ejector_setting.ejector_forward.table_data[row].sections[col], origin_machine, transplant_machine, "forward")

            else if (row == 2)
                transplant_process.ejector_setting.ejector_forward.table_data[row].sections[col] = origin_process.ejector_setting.ejector_forward.table_data[row].sections[col]

        }
    transplant_process.ejector_setting.ejector_start_point = origin_process.ejector_setting.ejector_start_point
    transplant_process.ejector_setting.ejector_delay = origin_process.ejector_setting.ejector_delay
    transplant_process.ejector_setting.ejector_keep = origin_process.ejector_setting.ejector_keep
    transplant_process.ejector_setting.ejector_pause = origin_process.ejector_setting.ejector_pause
    transplant_process.ejector_setting.ejector_blow_time = origin_process.ejector_setting.ejector_blow_time
    transplant_process.ejector_setting.ejector_mode = origin_process.ejector_setting.ejector_mode
    transplant_process.ejector_setting.ejector_times = origin_process.ejector_setting.ejector_times
    transplant_process.ejector_setting.ejector_on_opening = origin_process.ejector_setting.ejector_on_opening
    transplant_process.ejector_setting.ejector_stroke = origin_process.ejector_setting.ejector_stroke
    transplant_process.ejector_setting.ejector_force = origin_process.ejector_setting.ejector_force
    transplant_process.ejector_setting.set_torque = origin_process.ejector_setting.set_torque

    //开合模
    transplant_process.opening_and_clamping_mold_setting.mold_opening.mold_opening_stage = origin_process.opening_and_clamping_mold_setting.mold_opening.mold_opening_stage
    transplant_process.opening_and_clamping_mold_setting.mold_clamping.mold_clamping_stage = origin_process.opening_and_clamping_mold_setting.mold_clamping.mold_clamping_stage
    for (let row = 0; row < 3; ++row)
        for (let col = 0; col < 8; ++col) {
            if (row == 0)
                transplant_process.opening_and_clamping_mold_setting.mold_opening.table_data[row].sections[col] = origin_process.opening_and_clamping_mold_setting.mold_opening.table_data[row].sections[col]
            else if (row == 1)
                transplant_process.opening_and_clamping_mold_setting.mold_opening.table_data[row].sections[col] = transferOCVelocity(origin_machine.oc_velocity_unit, transplant_machine.oc_velocity_unit, origin_process.opening_and_clamping_mold_setting.mold_opening.table_data[row].sections[col], origin_machine, transplant_machine, "opening")

            else if (row == 2)
                transplant_process.opening_and_clamping_mold_setting.mold_opening.table_data[row].sections[col] = origin_process.opening_and_clamping_mold_setting.mold_opening.table_data[row].sections[col]

        }
    for (let row = 0; row < 3; ++row)
        for (let col = 0; col < 8; ++col) {
            if (row == 0)
                transplant_process.opening_and_clamping_mold_setting.mold_clamping.table_data[row].sections[col] = origin_process.opening_and_clamping_mold_setting.mold_clamping.table_data[row].sections[col]
            else if (row == 1)
                transplant_process.opening_and_clamping_mold_setting.mold_clamping.table_data[row].sections[col] = transferOCVelocity(origin_machine.oc_velocity_unit, transplant_machine.oc_velocity_unit, origin_process.opening_and_clamping_mold_setting.mold_clamping.table_data[row].sections[col], origin_machine, transplant_machine, "clamping")

            else if (row == 2)
                transplant_process.opening_and_clamping_mold_setting.mold_clamping.table_data[row].sections[col] = origin_process.opening_and_clamping_mold_setting.mold_clamping.table_data[row].sections[col]

        }
    transplant_process.opening_and_clamping_mold_setting.set_mold_clamping_force = origin_process.opening_and_clamping_mold_setting.set_mold_clamping_force
    transplant_process.opening_and_clamping_mold_setting.using_robot = origin_process.opening_and_clamping_mold_setting.using_robot
    transplant_process.opening_and_clamping_mold_setting.using_tool = origin_process.opening_and_clamping_mold_setting.using_tool
    transplant_process.opening_and_clamping_mold_setting.reset_method = origin_process.opening_and_clamping_mold_setting.reset_method
    transplant_process.opening_and_clamping_mold_setting.set_mold_protect_time = origin_process.opening_and_clamping_mold_setting.set_mold_protect_time
    transplant_process.opening_and_clamping_mold_setting.set_mold_protect_velocity = origin_process.opening_and_clamping_mold_setting.set_mold_protect_velocity
    transplant_process.opening_and_clamping_mold_setting.set_mold_protect_pressure = origin_process.opening_and_clamping_mold_setting.set_mold_protect_pressure
    transplant_process.opening_and_clamping_mold_setting.set_mold_protect_distance = origin_process.opening_and_clamping_mold_setting.set_mold_protect_distance
    transplant_process.opening_and_clamping_mold_setting.opening_position_deviation = origin_process.opening_and_clamping_mold_setting.opening_position_deviation
    transplant_process.opening_and_clamping_mold_setting.turnable_method = origin_process.opening_and_clamping_mold_setting.turnable_method
    transplant_process.opening_and_clamping_mold_setting.turnable_velocity = origin_process.opening_and_clamping_mold_setting.turnable_velocity

}

// 计算中需要用到注塑机的参数:
function transferPressure(original_unit: string, converted_unit: string, original_value: number, origin_injector_info: any, converted_injector_info: any, convert_type: string) {
    if (original_value) {
        let standard_value = conversion(original_unit, "MPa", original_value, origin_injector_info, convert_type)
        let converted_value = conversion("MPa", converted_unit, Number(standard_value), converted_injector_info, convert_type)
        return converted_value
    }
}

// 注射速度,保压速度, 松退速度中的%
function transferVelocity(original_unit: string, converted_unit: string, original_value: number, origin_injector_info: any, converted_injector_info: any, convert_type: string) {
    if (original_value) {
        let standard_value = conversion(original_unit, "cm³/s", original_value, origin_injector_info, convert_type)
        let converted_value = conversion("cm³/s", converted_unit, Number(standard_value), converted_injector_info, convert_type)
        
        return converted_value
    }
}

function transferPosition(origin_process:any, original_unit: string, converted_unit: string, original_value: number, origin_injector_info: any, converted_injector_info: any) {
    // 对于注射来说,通过螺杆位置计算每一段的注射体积:[熔胶终止位置,注射一段位置,注射二段位置...,V/P切换位置]
    // 螺杆位置包括前面V/P切换位置, V/P切换位置为最大螺杆行程的20%，或者是由工程师自主设定

    let origin_VP_position = origin_process.VP_switch.VP_switch_position
    let translant_VP_position = current_VP_switch_position
    // (converted_injector_info.max_injection_stroke*0.2).toFixed(2)

    let standard_value:any = conversion(original_unit, "cm³", (original_value-origin_VP_position), origin_injector_info)

    if(origin_injector_info.screw_wear && origin_injector_info.slope && origin_injector_info.intercept){
        standard_value = ((original_value-origin_VP_position)*origin_injector_info.slope + origin_injector_info.intercept).toFixed(2)
    }
    let converted_value:any = conversion("cm³", converted_unit, Number(standard_value), converted_injector_info)
    // 考虑到移植机台的螺杆磨损,实际上的行程,需要除以系数
    if(converted_injector_info.screw_wear && converted_injector_info.slope && converted_injector_info.intercept){
        converted_value = ((converted_value-converted_injector_info.intercept)/converted_injector_info.slope).toFixed(2)
    }
    // 最后停留位置需要加上V/P切换位置
    return (Number(converted_value) + Number(translant_VP_position)).toFixed(2)
}

// 松退距离
function transferDecompressurePosition(original_unit: string, converted_unit: string, original_value: number, origin_injector_info: any, converted_injector_info: any) {

    let standard_value = conversion(original_unit, "cm³", (original_value), origin_injector_info)
    let converted_value = conversion("cm³", converted_unit, Number(standard_value), converted_injector_info)

    return converted_value
}

// 螺杆转速中的%
function transferRotation(original_unit: string, converted_unit: string, original_value: number, origin_injector_info: any, converted_injector_info: any) {
    let standard_value = conversion(original_unit, "cm/s", original_value, origin_injector_info)
    let converted_value = conversion("cm/s", converted_unit, Number(standard_value), converted_injector_info)
    return converted_value
}

// 开合模,顶进顶退 速度中的%
function transferOCVelocity(original_unit: string, converted_unit: string, original_value: number, origin_injector_info: any, converted_injector_info: any, convert_type: string) {
    let standard_value = conversion(original_unit, "mm/s", original_value, origin_injector_info, convert_type)
    let converted_value = conversion("mm/s", converted_unit, Number(standard_value), converted_injector_info, convert_type)
    return converted_value
}

export function checkValidTransfer(injector_info: any, error: any) {
    // 以下参数和工艺有关
    if (!injector_info.screw_diameter) {
        error.push("螺杆直径为空")
    } else if (injector_info.screw_diameter == 0) {
        error.push("螺杆直径为零")
    }

    if (!injector_info.max_injection_pressure) {
        error.push("最大注射压力为空")
    } else if (injector_info.max_injection_pressure == 0) {
        error.push("最大注射压力为零")
    }

    if (!injector_info.max_injection_velocity) {
        error.push("最大注射速度为空")
    } else if (injector_info.max_injection_velocity == 0) {
        error.push("最大注射速度为零")
    }

    if (!injector_info.max_holding_pressure) {
        error.push("最大保压压力为空")
    } else if (injector_info.max_holding_pressure == 0) {
        error.push("最大保压压力为零")
    }

    if (!injector_info.max_holding_velocity) {
        error.push("最大保压速度为空")
    } else if (injector_info.max_holding_velocity == 0) {
        error.push("最大保压速度为零")
    }

    if (!injector_info.max_metering_pressure) {
        error.push("最大计量压力为空")
    } else if (injector_info.max_metering_pressure == 0) {
        error.push("最大计量压力为零")
    }

    if (!injector_info.max_screw_rotation_speed) {
        error.push("最大螺杆转速为空")
    } else if (injector_info.max_screw_rotation_speed == 0) {
        error.push("最大螺杆转速为零")
    }

    if (!injector_info.max_metering_back_pressure) {
        error.push("最大计量背压为空")
    } else if (injector_info.max_metering_back_pressure == 0) {
        error.push("最大计量背压为零")
    }

    if (!injector_info.max_decompression_pressure) {
        error.push("最大松退压力为空")
    } else if (injector_info.max_decompression_pressure == 0) {
        error.push("最大松退压力为零")
    }

    if (!injector_info.max_decompression_velocity) {
        error.push("最大松退速度为空")
    } else if (injector_info.max_decompression_velocity == 0) {
        error.push("最大松退速度为零")
    }

    if (!injector_info.max_ejector_forward_velocity) {
        error.push("最大顶进速度为空")
    } else if (injector_info.max_ejector_forward_velocity == 0) {
        error.push("最大顶进速度为零")
    }

    if (!injector_info.max_ejector_backward_velocity) {
        error.push("最大顶退速度为空")
    } else if (injector_info.max_ejector_backward_velocity == 0) {
        error.push("最大顶退速度为零")
    }

    if (!injector_info.max_mold_opening_velocity) {
        error.push("最大开模速度为空")
    } else if (injector_info.max_mold_opening_velocity == 0) {
        error.push("最大开模速度为零")
    }

    if (!injector_info.max_mold_clamping_velocity) {
        error.push("最大合模速度为空")
    } else if (injector_info.max_mold_clamping_velocity == 0) {
        error.push("最大合模速度为零")
    }

    if (!injector_info.max_set_injection_pressure) {
        error.push("最大可设定注射压力为空")
    } else if (injector_info.max_set_injection_pressure == 0) {
        error.push("最大可设定注射压力为零")
    }

    if (!injector_info.max_set_injection_velocity) {
        error.push("最大可设定注射速度为空")
    } else if (injector_info.max_set_injection_velocity == 0) {
        error.push("最大可设定注射速度为零")
    }

    if (!injector_info.max_set_holding_pressure) {
        error.push("最大可设定保压压力为空")
    } else if (injector_info.max_set_holding_pressure == 0) {
        error.push("最大可设定保压压力为零")
    }

    if (!injector_info.max_set_holding_velocity) {
        error.push("最大可设定保压速度为空")
    } else if (injector_info.max_set_holding_velocity == 0) {
        error.push("最大可设定保压速度为零")
    }

    if (!injector_info.max_set_metering_pressure) {
        error.push("最大可设定计量压力为空")
    } else if (injector_info.max_set_metering_pressure == 0) {
        error.push("最大可设定计量压力为零")
    }

    if (!injector_info.max_set_screw_rotation_speed) {
        error.push("最大可设定螺杆转速为空")
    } else if (injector_info.max_set_screw_rotation_speed == 0) {
        error.push("最大可设定螺杆转速为零")
    }

    if (!injector_info.max_set_metering_back_pressure) {
        error.push("最大可设定计量背压为空")
    } else if (injector_info.max_set_metering_back_pressure == 0) {
        error.push("最大可设定计量背压为零")
    }

    if (!injector_info.max_set_decompression_pressure) {
        error.push("最大可设定松退压力为空")
    } else if (injector_info.max_set_decompression_pressure == 0) {
        error.push("最大可设定松退压力为零")
    }

    if (!injector_info.max_set_decompression_velocity) {
        error.push("最大可设定松退速度为空")
    } else if (injector_info.max_set_decompression_velocity == 0) {
        error.push("最大可设定松退速度为零")
    }

    if (!injector_info.max_set_ejector_forward_velocity) {
        error.push("最大可设定顶进速度为空")
    } else if (injector_info.max_set_ejector_forward_velocity == 0) {
        error.push("最大可设定顶进速度为零")
    }

    if (!injector_info.max_set_ejector_backward_velocity) {
        error.push("最大可设定顶退速度为空")
    } else if (injector_info.max_set_ejector_backward_velocity == 0) {
        error.push("最大可设定顶退速度为零")
    }

    if (!injector_info.max_set_mold_opening_velocity) {
        error.push("最大可设定开模速度为空")
    } else if (injector_info.max_set_mold_opening_velocity == 0) {
        error.push("最大可设定开模速度为零")
    }

    if (!injector_info.max_set_mold_clamping_velocity) {
        error.push("最大可设定合模速度为空")
    } else if (injector_info.max_set_mold_clamping_velocity == 0) {
        error.push("最大可设定合模速度为零")
    }

    if (!injector_info.max_injection_stroke) {
        error.push("最大注射行程为空")
    } else if (injector_info.max_injection_stroke == 0) {
        error.push("最大注射行程为零")
    }

    if (!injector_info.power_method) {
        error.push("动力方式为空")
    }
}

let not_enough = 0
let machine_not_enough = 0
export function checkValidMold(mold_info:any, error:any){
    not_enough = 0
    if(mold_info){
        if (!mold_info.mold_type) {
            error.push("模具类型为空")
            not_enough = 1
        } 
        if (!mold_info.min_clamping_force) {
            error.push("模具锁模力为空")
            not_enough = 1
        } 
        if (!mold_info.product_total_weight) {
            error.push("模具总重量为空")
            not_enough = 1
        } 
        if (!mold_info.size_horizon) {
            error.push("模具尺寸(横)为空")
            not_enough = 1
        }
        if (!mold_info.size_vertical) {
            error.push("模具尺寸(竖)为空")
            not_enough = 1
        } 
        if (!mold_info.size_thickness) {
            error.push("模具厚度为空")
            not_enough = 1
        } 
        if (!mold_info.locate_ring_diameter) {
            error.push("模具定位圈直径为空")
            not_enough = 1
        } 
        if (!mold_info.ejector_force) {
            error.push("模具顶出力空")
            not_enough = 1
        } 
        if (!mold_info.ejector_stroke) {
            error.push("模具顶出行程为空")
            not_enough = 1
        } 
        if (!mold_info.mold_opening_stroke) {
            error.push("模具开模行程为空")
            not_enough = 1
        } 
        if (!mold_info.product_infos[0].sprue_sphere_radius) {
            error.push("模具喷嘴球径为空")
            not_enough = 1
        } 
        if (!mold_info.product_infos[0].sprue_hole_diameter) {
            error.push("模具喷嘴孔径为空")
            not_enough = 1
        }
        if (mold_info.mold_type&&mold_info.mold_type.indexOf("三板模")!= -1 &&!mold_info.drain_distance) {
            error.push("三模板，取流道距离为空")
            not_enough = 1
        }

    }
}

export function checkValidTransferMachine(injector_info: any, error: any){
    machine_not_enough = 0
    if (!injector_info.screw_diameter) {
        error.push("注塑机类型(射台数)为空")
        machine_not_enough = 1
    }

    if (!injector_info.max_injection_pressure) {
        error.push("注塑机最大锁模力为空")
        machine_not_enough = 1
    } else if (injector_info.max_injection_pressure == 0) {
        error.push("注塑机最大锁模力为零")
        machine_not_enough = 1
    }

    if (!injector_info.max_injection_velocity) {
        error.push("注塑机最大注射量为空")
        machine_not_enough = 1
    } else if (injector_info.max_injection_velocity == 0) {
        error.push("注塑机最大注射量为零")
        machine_not_enough = 1
    }

    if (!injector_info.max_mold_size_horizon) {
        error.push("注塑机最大容模尺寸（横）为空")
        machine_not_enough = 1
    } else if (injector_info.max_mold_size_horizon == 0) {
        error.push("注塑机最大容模尺寸（横）为零")
        machine_not_enough = 1
    }

    if (!injector_info.max_mold_size_vertical) {
        error.push("注塑机最大容模尺寸（竖）为空")
        machine_not_enough = 1
    } else if (injector_info.max_mold_size_vertical == 0) {
        error.push("注塑机最大容模尺寸（竖）为零")
        machine_not_enough = 1
    }

    if (!injector_info.max_mold_thickness) {
        error.push("注塑机最大容模厚度为空")
        machine_not_enough = 1
    } else if (injector_info.max_mold_thickness == 0) {
        error.push("注塑机最大容模厚度为零")
        machine_not_enough = 1
    }
    if (!injector_info.min_mold_size_horizon) {
        error.push("注塑机最小容模尺寸（横）为空")
        machine_not_enough = 1
    } else if (injector_info.min_mold_size_horizon == 0) {
        error.push("注塑机最小容模尺寸（横）为零")
        machine_not_enough = 1
    }

    if (!injector_info.min_mold_size_vertical) {
        error.push("注塑机最小容模尺寸（竖）为空")
        machine_not_enough = 1
    } else if (injector_info.min_mold_size_vertical == 0) {
        error.push("注塑机最小容模尺寸（竖）为零")
        machine_not_enough = 1
    }

    if (!injector_info.min_mold_thickness) {
        error.push("注塑机最小容模厚度为空")
        machine_not_enough = 1
    } else if (injector_info.min_mold_thickness == 0) {
        error.push("注塑机最小容模厚度为零")
        machine_not_enough = 1
    }

    if (!injector_info.locate_ring_diameter) {
        error.push("注塑机定位圈直径为空")
        machine_not_enough = 1
    } else if (injector_info.locate_ring_diameter == 0) {
        error.push("注塑机定位圈直径为零")
        machine_not_enough = 1
    }

    if (!injector_info.max_ejection_force) {
        error.push("注塑机最大顶出力为空")
        machine_not_enough = 1
    } else if (injector_info.max_ejection_force == 0) {
        error.push("注塑机最大顶出力为零")
        machine_not_enough = 1
    }

    if (!injector_info.max_mold_open_stroke) {
        error.push("注塑机最大顶出行程为空")
        machine_not_enough = 1
    } else if (injector_info.max_mold_open_stroke == 0) {
        error.push("注塑机最大顶出行程为零")
        machine_not_enough = 1
    }

    if (!injector_info.nozzle_sphere_diameter) {
        error.push("注塑机最大开模行程为空")
        machine_not_enough = 1
    } else if (injector_info.max_decompression_velocity == 0) {
        error.push("注塑机最大开模行程为零")
        machine_not_enough = 1
    }

    if (!injector_info.nozzle_sphere_diameter) {
        error.push("注塑机喷嘴球径为空")
        machine_not_enough = 1
    } else if (injector_info.nozzle_sphere_diameter == 0) {
        error.push("注塑机喷嘴球径为零")
        machine_not_enough = 1
    }

    if (!injector_info.nozzle_hole_diameter) {
        error.push("注塑机喷嘴孔径为空")
        machine_not_enough = 1
    } else if (injector_info.nozzle_hole_diameter == 0) {
        error.push("注塑机喷嘴孔径为零")
        machine_not_enough = 1
    }
}

export function checkValidAdaption(injector_info: any, error: any, mold_info:any){
    let yellow = 0
    if(mold_info){
        const MachineTypeOptions:any = {
            "单色注塑机": 1,
            "双色注塑机": 2,
            "三色注塑机": 3,
            "四色注塑机": 4,
            "五色注塑机": 5,
            "六色注塑机": 6,
            "七色注塑机": 7,
          }
        const MoldTypeOptions:any = {
            "单色模": 1,
            "双色模": 2,
            "三色模": 3,
            "四色模": 4,
            "五色模": 5,
            "六色模": 6,
            "七色模": 7,
          }
        if (mold_info.mold_type && injector_info.machine_type && MoldTypeOptions[mold_info.mold_type.slice(4,6)] > MachineTypeOptions[injector_info.machine_type]) {
            error.push("模具为"+mold_info.mold_type+",注塑机为"+injector_info.machine_type+",注塑机射台数不足")
        } 
        if (mold_info.min_clamping_force && injector_info.max_clamping_force && Number(mold_info.min_clamping_force) > Number(injector_info.max_clamping_force)) {
            error.push("模具锁模力为"+mold_info.min_clamping_force+"Ton,注塑机锁模力为"+injector_info.max_clamping_force+"Ton")
        } 
        if (mold_info.min_clamping_force && injector_info.max_clamping_force && Number(mold_info.min_clamping_force) > Number(injector_info.max_clamping_force)*0.85) {
            error.push("注意：模具锁模力为"+mold_info.min_clamping_force+"Ton,注塑机锁模力为"+injector_info.max_clamping_force+"Ton,大于注塑机锁模力的85%")
        } 
        if (mold_info.product_total_weight && injector_info.max_injection_weight && Number(mold_info.min_clamping_force) > Number(injector_info.max_injection_weight)) {
            error.push("模具注射量为"+mold_info.product_total_weight+"g,注塑机注射量为"+injector_info.max_injection_weight+"g")
        }
        if (mold_info.product_total_weight && injector_info.max_injection_weight && Number(mold_info.min_clamping_force) < Number(injector_info.max_injection_weight)*0.25) {
            error.push("注意：模具注射量为"+mold_info.product_total_weight+"g,注塑机注射量为"+injector_info.max_injection_weight+"g,小于注塑机最大注射量的25%")
        } 
        if (mold_info.product_total_weight && injector_info.max_injection_weight && Number(mold_info.min_clamping_force) > Number(injector_info.max_injection_weight)*0.75) {
            error.push("注意：模具注射量为"+mold_info.product_total_weight+"g,注塑机注射量为"+injector_info.max_injection_weight+"g,大于注塑机最大注射量的75%")
        } 
        if (mold_info.size_horizon && injector_info.max_mold_size_horizon && Number(mold_info.size_horizon) > Number(injector_info.max_mold_size_horizon)) {
            error.push("模具尺寸（横）为"+mold_info.size_horizon+"mm,注塑机最大容模尺寸（横）为"+injector_info.max_mold_size_horizon+"mm")
        } 
        if (mold_info.size_vertical && injector_info.max_mold_size_vertical && Number(mold_info.size_vertical) > Number(injector_info.max_mold_size_vertical)) {
            error.push("模具尺寸（竖）为"+mold_info.size_vertical+"mm,注塑机最大容模尺寸（竖）为"+injector_info.max_mold_size_vertical+"mm")
        } 
        if (mold_info.size_thickness && injector_info.max_mold_thickness && Number(mold_info.size_thickness) > Number(injector_info.max_mold_thickness)) {
            error.push("模具厚度为"+mold_info.size_thickness+"mm,注塑机最大容模厚度为"+injector_info.max_mold_thickness+"mm")
        } 
        if (mold_info.size_horizon && injector_info.min_mold_size_horizon && Number(mold_info.size_horizon) < Number(injector_info.min_mold_size_horizon)) {
            error.push("模具尺寸（横）为"+mold_info.size_horizon+"mm,注塑机最小容模尺寸（横）为"+injector_info.min_mold_size_horizon+"mm")
        } 
        if (mold_info.size_vertical && injector_info.min_mold_size_vertical && Number(mold_info.size_vertical) < Number(injector_info.min_mold_size_vertical)) {
            error.push("模具尺寸（竖）为"+mold_info.size_vertical+"mm,注塑机最小容模尺寸（竖）为"+injector_info.min_mold_size_vertical+"mm")
        } 
        if (mold_info.size_thickness && injector_info.min_mold_thickness && Number(mold_info.size_thickness) < Number(injector_info.min_mold_thickness)) {
            error.push("模具厚度为"+mold_info.size_thickness+"mm,注塑机最小容模厚度为"+injector_info.min_mold_thickness+"mm")
        } 
        if (mold_info.locate_ring_diameter && injector_info.locate_ring_diameter && Number(mold_info.locate_ring_diameter) != Number(injector_info.locate_ring_diameter)) {
            error.push("模具定位圈直径为"+mold_info.locate_ring_diameter+"mm,注塑机定位圈直径为"+injector_info.locate_ring_diameter+"mm")
        } 
        if (mold_info.ejector_force && injector_info.max_ejection_force && Number(mold_info.ejector_force) > Number(injector_info.max_ejection_force)) {
            error.push("模具顶出力为"+mold_info.ejector_force+"KN,注塑机顶出力为"+injector_info.max_ejection_force+"KN")
        } 
        if (mold_info.ejector_stroke && injector_info.max_ejection_stroke && Number(mold_info.ejector_stroke) > Number(injector_info.max_ejection_stroke)) {
            error.push("模具顶出行程为"+mold_info.ejector_stroke+"mm,注塑机顶出行程为"+injector_info.max_ejection_stroke+"mm")
        } 

        if (mold_info.mold_opening_stroke && injector_info.max_mold_open_stroke){
            if(mold_info.mold_type.indexOf("两板模") != -1){
                if(Number(mold_info.mold_opening_stroke)+Number(mold_info.size_thickness) > Number(injector_info.max_mold_open_stroke)-10) {
                error.push("模具开模行程为"+mold_info.mold_opening_stroke+"mm,厚度为"+mold_info.size_thickness+"mm,注塑机开模行程为"+injector_info.max_mold_open_stroke+"mm")
                } 
            }
            if(mold_info.mold_type.indexOf("三板模") != -1 && mold_info.drain_distance){
                if(Number(mold_info.mold_opening_stroke)+Number(mold_info.size_thickness)+Number(mold_info.drain_distance) > Number(injector_info.max_mold_open_stroke)-10) {
                error.push("模具开模行程为"+mold_info.mold_opening_stroke+"mm,厚度为"+mold_info.size_thickness+"mm,取流道距离为"+mold_info.drain_distance+"mm,注塑机开模行程为"+injector_info.max_mold_open_stroke+"mm")
                } 
            }
        }
        if (mold_info.product_infos[0].sprue_sphere_radius && injector_info.nozzle_sphere_diameter && Number(mold_info.product_infos[0].sprue_sphere_radius) > Number(injector_info.nozzle_sphere_diameter)) {
            error.push("模具喷嘴球径为"+mold_info.product_infos[0].sprue_sphere_radius+"mm,注塑机喷嘴球径为"+injector_info.nozzle_sphere_diameter+"mm,")
        } 
        if (mold_info.product_infos[0].sprue_hole_diameter && injector_info.nozzle_hole_diameter && Number(mold_info.product_infos[0].sprue_hole_diameter) > Number(injector_info.nozzle_hole_diameter)) {
            error.push("模具喷嘴孔径为"+mold_info.product_infos[0].sprue_hole_diameter+"mm,注塑机喷嘴孔径为"+injector_info.nozzle_hole_diameter+"mm")
        } 
        if(error == "模具和转换机台适配的"){
            if (not_enough === 1){
                error.push("模具参数不全")
            }
            if (machine_not_enough === 1){
                error.push("转换机台参数不全")
            }
        }
    }
    return yellow
}

function transferInjectionPressure(origin: number, ori_max_set_inj_pres: number, ori_max_act_inj_pres: number, trans_max_set_inj_pres: number, trans_max_act_inj_pres: number) {
    if (origin && ori_max_set_inj_pres > 0 && ori_max_act_inj_pres && trans_max_set_inj_pres && trans_max_act_inj_pres > 0) {
        return (origin * (trans_max_set_inj_pres / ori_max_set_inj_pres) * (ori_max_act_inj_pres / trans_max_act_inj_pres)).toFixed(2)
    } else {
        if (origin == 0)
            return origin
        else
            return null
    }
}

// function transferInjectionVelocity(origin: number, ori_max_set_inj_velo: number, ori_max_act_inj_velo: number, trans_max_set_inj_velo: number, trans_max_act_inj_velo: number, ori_sd: number, tra_sd: number, origin_machine: any, transplant_machine: any) {
//     if (origin_machine.velocity_unit == "%"){
//         ori_max_set_inj_velo = 1
//     }
//     if (transplant_machine.velocity_unit == "%"){
//         trans_max_set_inj_velo = 1
//     }
//     if (origin && ori_max_set_inj_velo > 0 && trans_max_set_inj_velo && ori_max_act_inj_velo && trans_max_act_inj_velo > 0 && ori_sd && tra_sd > 0) {
//         return (origin * (trans_max_set_inj_velo / ori_max_set_inj_velo) * (ori_max_act_inj_velo / trans_max_act_inj_velo) * (ori_sd**2 / tra_sd**2)).toFixed(2)
//     } else {
//         return null
//     }
// }

// function transferInjectionPosition(origin: number, ori_sd: number, tra_sd: number) {
//     if (origin && ori_sd && tra_sd > 0) {
//         return (origin * (ori_sd**2 / tra_sd**2)).toFixed(2)
//     } else {
//         if (origin == 0)
//             return origin
//         else
//             return null
//     }
// }

function transferHoldingPressure(origin: number, ori_max_set_hld_pres: number, ori_max_act_hld_pres: number, trans_max_set_hld_pres: number, trans_max_act_hld_pres: number) {
    if (origin && ori_max_set_hld_pres > 0 && trans_max_set_hld_pres && ori_max_act_hld_pres && trans_max_act_hld_pres > 0) {
        return (origin * (trans_max_set_hld_pres / ori_max_set_hld_pres) * (ori_max_act_hld_pres / trans_max_act_hld_pres)).toFixed(2)
    } else {
        if (origin == 0)
            return origin
        else
            return null
    }
}

// function transferHoldingVelocity(origin: number, ori_max_set_hld_velo: number, ori_max_act_hld_velo: number, trans_max_set_hld_velo: number, trans_max_act_hld_velo: number, ori_sd: number, tra_sd: number, origin_machine: any, transplant_machine: any) {
//     if (origin_machine.velocity_unit == "%"){
//         ori_max_set_hld_velo = 1
//     }
//     if (transplant_machine.velocity_unit == "%"){
//         trans_max_set_hld_velo = 1
//     }
//     if (origin && ori_max_set_hld_velo > 0 && ori_max_act_hld_velo && trans_max_set_hld_velo && trans_max_act_hld_velo > 0 && ori_sd && tra_sd > 0) {
//         return (origin * (trans_max_set_hld_velo / ori_max_set_hld_velo) * (ori_max_act_hld_velo / trans_max_act_hld_velo) * (ori_sd**2 / tra_sd**2)).toFixed(2)
//     } else {
//         if (origin == 0)
//             return origin
//         else
//             return null
//     }
// }

function transferMeteringPressure(origin: number, ori_max_set_mtr_pres: number, ori_max_act_mtr_pres: number, trans_max_set_mtr_pres: number, trans_max_act_mtr_pres: number) {
    if (origin && ori_max_set_mtr_pres && ori_max_act_mtr_pres && trans_max_set_mtr_pres > 0 && trans_max_act_mtr_pres > 0) {
        return (origin * (ori_max_set_mtr_pres / trans_max_set_mtr_pres) * (ori_max_act_mtr_pres / trans_max_act_mtr_pres)).toFixed(2)
    } else {
        if (origin == 0)
            return origin
        else
            return null
    }
}

// function transferScrewRotaionSpeed(origin: number, ori_max_set_srw_rot_spd: number, ori_max_act_srw_rot_spd: number, trans_max_set_srw_rot_spd: number, trans_max_act_srw_rot_spd: number, ori_sd: number, tra_sd: number) {
//     if (origin && ori_max_set_srw_rot_spd > 0 && ori_max_act_srw_rot_spd && trans_max_set_srw_rot_spd && trans_max_act_srw_rot_spd > 0 && ori_sd && tra_sd > 0) {
//         return (origin * (trans_max_set_srw_rot_spd / ori_max_set_srw_rot_spd) * (ori_max_act_srw_rot_spd / trans_max_act_srw_rot_spd) * (ori_sd / tra_sd)).toFixed(2)
//     } else {
//         if (origin == 0)
//             return origin
//         else
//             return null
//     }
// }

function transferMeteringBackPressure(origin: number, ori_max_set_mtr_bak_pres: number, ori_max_act_mtr_bak_pres: number, trans_max_set_mtr_bak_pres: number, trans_max_act_mtr_bak_pres: number) {
    if (origin && ori_max_set_mtr_bak_pres > 0 && ori_max_act_mtr_bak_pres && trans_max_set_mtr_bak_pres && trans_max_act_mtr_bak_pres > 0) {
        return (origin * (trans_max_set_mtr_bak_pres / ori_max_set_mtr_bak_pres) * (ori_max_act_mtr_bak_pres / trans_max_act_mtr_bak_pres)).toFixed(2)
    } else {
        if (origin == 0)
            return origin
        else
            return null
    }
}

// function transferMeteringPosition(origin: number, ori_sd: number, tra_sd: number) {
//     if (origin && ori_sd && tra_sd > 0) {
//         return (origin * (ori_sd**2 / tra_sd**2)).toFixed(2)
//     } else {
//         if (origin == 0)
//             return origin
//         else
//             return null
//     }
// }

function transferDecompressionPressure(origin: number, ori_max_set_dec_pres: number, ori_max_act_dec_pres: number, trans_max_set_dec_pres: number, trans_max_act_dec_pres: number) {
    if (origin && ori_max_set_dec_pres > 0 && ori_max_act_dec_pres && trans_max_set_dec_pres && trans_max_act_dec_pres > 0) {
        return (origin * (trans_max_set_dec_pres / ori_max_set_dec_pres) * (ori_max_act_dec_pres / trans_max_act_dec_pres)).toFixed(2)
    } else {
        if (origin == 0)
            return origin
        else
            return null
    }
}

// function transferDecompressionVecolity(origin: number, ori_max_set_dec_velo: number, ori_max_act_dec_velo: number, trans_max_set_dec_velo: number, trans_max_act_dec_velo: number, ori_sd: number, tra_sd: number) {
//     if (origin && ori_max_set_dec_velo > 0 && ori_max_act_dec_velo && trans_max_set_dec_velo && trans_max_act_dec_velo > 0 && ori_sd && tra_sd > 0) {
//         return (origin * (trans_max_set_dec_velo / ori_max_set_dec_velo) * (ori_max_act_dec_velo / trans_max_act_dec_velo) * (ori_sd**2 / tra_sd**2)).toFixed(2)
//     } else {
//         if (origin == 0)
//             return origin
//         else
//             return null
//     }
// }

// function transferDecompressionPosition(origin: number, ori_sd: number, tra_sd: number) {
//     if (origin && ori_sd && tra_sd > 0) {
//         return (origin * (ori_sd**2 / tra_sd**2)).toFixed(2)
//     } else {
//         if (origin == 0)
//             return origin
//         else
//             return null
//     }
// }

// function transferOpenVelocity(origin: number, ori_max_set_open_velo: number, ori_max_act_open_velo: number, trans_max_set_open_velo: number, trans_max_act_open_velo: number, origin_machine: any, transplant_machine: any) {
//     if (origin_machine.oc_velocity_unit == "%"){
//         ori_max_set_open_velo = 1
//     }
//     if (transplant_machine.oc_velocity_unit == "%"){
//         trans_max_set_open_velo = 1
//     }
//     if (origin && ori_max_set_open_velo > 0 && trans_max_set_open_velo && ori_max_act_open_velo && trans_max_act_open_velo > 0) {
//         return (origin * (trans_max_set_open_velo / ori_max_set_open_velo) * (ori_max_act_open_velo / trans_max_act_open_velo)).toFixed(2)
//     } else {
//         return null
//     }
// }

// function transferClampingVelocity(origin: number, ori_max_set_clamping_velo: number, ori_max_act_clamping_velo: number, trans_max_set_clamping_velo: number, trans_max_act_clamping_velo: number,origin_machine: any, transplant_machine: any) {
//     if (origin_machine.oc_velocity_unit == "%"){
//         ori_max_set_clamping_velo = 1
//     }
//     if (transplant_machine.oc_velocity_unit == "%"){
//         trans_max_set_clamping_velo = 1
//     }
//     if (origin && ori_max_set_clamping_velo > 0 && trans_max_set_clamping_velo && ori_max_act_clamping_velo && trans_max_act_clamping_velo > 0) {
//         return (origin * (trans_max_set_clamping_velo / ori_max_set_clamping_velo) * (ori_max_act_clamping_velo / trans_max_act_clamping_velo)).toFixed(2)
//     } else {
//         return null
//     }
// }

// function transferEjectorBackwardVelocity(origin: number, ori_max_set_back_velo: number, ori_max_act_back_velo: number, trans_max_set_back_velo: number, trans_max_act_back_velo: number, origin_machine: any, transplant_machine: any) {
//     if (origin_machine.oc_velocity_unit == "%"){
//         ori_max_set_back_velo = 1
//     }
//     if (transplant_machine.oc_velocity_unit == "%"){
//         trans_max_set_back_velo = 1
//     }
//     if (origin && ori_max_set_back_velo > 0 && trans_max_set_back_velo && ori_max_act_back_velo && trans_max_act_back_velo > 0) {
//         return (origin * (trans_max_set_back_velo / ori_max_set_back_velo) * (ori_max_act_back_velo / trans_max_act_back_velo)).toFixed(2)
//     } else {
//         return null
//     }
// }

// function transferEjectorForwardVelocity(origin: number, ori_max_set_forward_velo: number, ori_max_act_forward_velo: number, trans_max_set_forward_velo: number, trans_max_act_forward_velo: number, origin_machine: any, transplant_machine: any) {
//     if (origin_machine.oc_velocity_unit == "%"){
//         ori_max_set_forward_velo = 1
//     }
//     if (transplant_machine.oc_velocity_unit == "%"){
//         trans_max_set_forward_velo = 1
//     }
//     if (origin && ori_max_set_forward_velo > 0 && trans_max_set_forward_velo && ori_max_act_forward_velo && trans_max_act_forward_velo > 0) {
//         return (origin * (trans_max_set_forward_velo / ori_max_set_forward_velo) * (ori_max_act_forward_velo / trans_max_act_forward_velo)).toFixed(2)
//     } else {
//         return null
//     }
// }
