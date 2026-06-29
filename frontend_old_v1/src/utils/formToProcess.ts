export function settingProcessToProcess(process: any, form_info: any){
    process.machine_data_source = form_info["machine_data_source"]
    process.machine_id = form_info["machine_id"]
    process.polymer_abbreviation = form_info["polymer_abbreviation"]
    process.polymer_id = form_info["polymer_id"]
    process.process_no = form_info["process_no"]
    process.mold_no = form_info["mold_no"]
    process.mold_id = form_info["mold_id"]
    process.product_name = form_info["product_name"]
    process.product_catalog = form_info["product_catalog"]
    process.product_type = form_info["product_type"]
    process.polymer_trademark = form_info["polymer_trademark"]
    process.machine_trademark = form_info["machine_trademark"]
    process.screw_diameter = form_info["screw_diameter"]
    let setting_process = form_info.process_list[0]
    return settingProcessToProcessDetail(process, setting_process, form_info)
}
export function transplantedProcessToProcess(transplanted_process: any, transplant_process:any, form_info: any){
    transplanted_process.machine_data_source = form_info.transplant_machine.transplant_machine_search.data_source
    transplanted_process.machine_id = form_info.transplant_machine.transplant_machine_search.id
    transplanted_process.machine_trademark = form_info.transplant_machine.transplant_machine_search.trademark
    transplanted_process.screw_diameter = form_info.transplant_machine.transplant_machine_data.screw_diameter
    return settingProcessToProcessDetail(transplanted_process, transplant_process, form_info.transplant_machine)
}
export function settingProcessToProcessDetail(process: any, setting_process: any, form_info: any){   
    process.barrel_temperature_stage = setting_process.temp_para.barrel_temperature_stage
    if(setting_process.temp_para.barrel_temperature_stage >0){
        process.nozzle_temperature = setting_process.temp_para.barrel_temperature_stage_paras[0].barrel_temperature
    }
    if(setting_process.temp_para.barrel_temperature_stage >1){
        process.barrel_temperature_1 = setting_process.temp_para.barrel_temperature_stage_paras[1].barrel_temperature
    }
    if(setting_process.temp_para.barrel_temperature_stage >2){
        process.barrel_temperature_2 = setting_process.temp_para.barrel_temperature_stage_paras[2].barrel_temperature
    }
    if(setting_process.temp_para.barrel_temperature_stage >3){
        process.barrel_temperature_3 = setting_process.temp_para.barrel_temperature_stage_paras[3].barrel_temperature
    }
    if(setting_process.temp_para.barrel_temperature_stage >4){
        process.barrel_temperature_4= setting_process.temp_para.barrel_temperature_stage_paras[4].barrel_temperature
    }
    if(setting_process.temp_para.barrel_temperature_stage >5){
        process.barrel_temperature_5 = setting_process.temp_para.barrel_temperature_stage_paras[5].barrel_temperature
    }
    if(setting_process.temp_para.barrel_temperature_stage >6){
        process.barrel_temperature_6 = setting_process.temp_para.barrel_temperature_stage_paras[6].barrel_temperature
    }
    if(setting_process.temp_para.barrel_temperature_stage >7){
        process.barrel_temperature_7 = setting_process.temp_para.barrel_temperature_stage_paras[7].barrel_temperature
    }
    if(setting_process.temp_para.barrel_temperature_stage >8){
        process.barrel_temperature_8 = setting_process.temp_para.barrel_temperature_stage_paras[8].barrel_temperature
    }
    if(setting_process.temp_para.barrel_temperature_stage >9){
        process.barrel_temperature_9 = setting_process.temp_para.barrel_temperature_stage_paras[9].barrel_temperature
    }
    process.injection_stage = setting_process.injection_para.injection_stage
    process.injection_time = setting_process.injection_para.injection_time
    process.injection_delay_time = setting_process.injection_para.injection_delay_time    
    if (setting_process.injection_para.injection_stage >0){
        process.injection_pressure_1 = pageToDbPressure(setting_process.injection_para.injection_stage_paras[0].max_injection_pressure,form_info.max_set.max_set_injection_pressure, form_info.max.max_injection_pressure)
        process.injection_velocity_1 = velocityToVolume(setting_process.injection_para.injection_stage_paras[0].max_injection_velocity,process.screw_diameter, form_info.max_set.max_set_injection_velocity, form_info.max.max_injection_velocity)
        process.injection_position_1 = positionToVolume(setting_process.injection_para.injection_stage_paras[0].injection_position,process.screw_diameter)
    }
    if (setting_process.injection_para.injection_stage >1){
        process.injection_pressure_2 = pageToDbPressure(setting_process.injection_para.injection_stage_paras[1].max_injection_pressure,form_info.max_set.max_set_injection_pressure, form_info.max.max_injection_pressure)
        process.injection_velocity_2 = velocityToVolume(setting_process.injection_para.injection_stage_paras[1].max_injection_velocity,process.screw_diameter, form_info.max_set.max_set_injection_velocity, form_info.max.max_injection_velocity)
        process.injection_position_2 = positionToVolume(setting_process.injection_para.injection_stage_paras[1].injection_position,process.screw_diameter)
    }
    if (setting_process.injection_para.injection_stage >2){
        process.injection_pressure_3 = pageToDbPressure(setting_process.injection_para.injection_stage_paras[2].max_injection_pressure,form_info.max_set.max_set_injection_pressure, form_info.max.max_injection_pressure)
        process.injection_velocity_3 = velocityToVolume(setting_process.injection_para.injection_stage_paras[2].max_injection_velocity,process.screw_diameter, form_info.max_set.max_set_injection_velocity, form_info.max.max_injection_velocity)
        process.injection_position_3 = positionToVolume(setting_process.injection_para.injection_stage_paras[2].injection_position,process.screw_diameter)
    }
    if (setting_process.injection_para.injection_stage >3){
        process.injection_pressure_4 = pageToDbPressure(setting_process.injection_para.injection_stage_paras[3].max_injection_pressure,form_info.max_set.max_set_injection_pressure, form_info.max.max_injection_pressure)
        process.injection_velocity_4 = velocityToVolume(setting_process.injection_para.injection_stage_paras[3].max_injection_velocity,process.screw_diameter, form_info.max_set.max_set_injection_velocity, form_info.max.max_injection_velocity)
        process.injection_position_4 = positionToVolume(setting_process.injection_para.injection_stage_paras[3].injection_position,process.screw_diameter)
    }
    if (setting_process.injection_para.injection_stage >4){
        process.injection_pressure_5 = pageToDbPressure(setting_process.injection_para.injection_stage_paras[4].max_injection_pressure,form_info.max_set.max_set_injection_pressure, form_info.max.max_injection_pressure)
        process.injection_velocity_5 = velocityToVolume(setting_process.injection_para.injection_stage_paras[4].max_injection_velocity,process.screw_diameter, form_info.max_set.max_set_injection_velocity, form_info.max.max_injection_velocity)
        process.injection_position_5 = positionToVolume(setting_process.injection_para.injection_stage_paras[4].injection_position,process.screw_diameter)
    }
    if (setting_process.injection_para.injection_stage >5){
        process.injection_pressure_6 = pageToDbPressure(setting_process.injection_para.injection_stage_paras[5].max_injection_pressure,form_info.max_set.max_set_injection_pressure, form_info.max.max_injection_pressure)
        process.injection_velocity_6 = velocityToVolume(setting_process.injection_para.injection_stage_paras[5].max_injection_velocity,process.screw_diameter, form_info.max_set.max_set_injection_velocity, form_info.max.max_injection_velocity)
        process.injection_position_6 = positionToVolume(setting_process.injection_para.injection_stage_paras[5].injection_position,process.screw_diameter)
    }
    // 注射终止位置
    // process.injection_ending_position = setting_process.metering_para.metering_stage
    process.VP_switch_mode = setting_process.holding_para.VP_switch_mode
    process.VP_switch_position = positionToVolume(setting_process.holding_para.VP_switch_position,process.screw_diameter)
    process.VP_switch_time = setting_process.holding_para.VP_switch_time
    process.VP_switch_pressure = pageToDbPressure(setting_process.holding_para.VP_switch_pressure, form_info.max_set.max_set_holding_pressure, form_info.max.max_holding_pressure)
    // VP切换速度
    // process.VP_switch_velocity = setting_process.holding_para.VP_switch_position
    process.holding_stage = setting_process.holding_para.holding_stage
    if (setting_process.holding_para.holding_stage >0){
        process.holding_pressure_1 = pageToDbPressure(setting_process.holding_para.holding_stage_paras[0].max_holding_pressure, form_info.max_set.max_set_holding_pressure, form_info.max.max_holding_pressure)
        process.holding_velocity_1 = velocityToVolume(setting_process.holding_para.holding_stage_paras[0].max_holding_velocity,process.screw_diameter, form_info.max_set.max_set_holding_velocity, form_info.max.max_holding_velocity)
        process.holding_time_1 = setting_process.holding_para.holding_stage_paras[0].holding_time
    }
    if (setting_process.holding_para.holding_stage >1){
        process.holding_pressure_2 = pageToDbPressure(setting_process.holding_para.holding_stage_paras[1].max_holding_pressure, form_info.max_set.max_set_holding_pressure, form_info.max.max_holding_pressure)
        process.holding_velocity_2 = velocityToVolume(setting_process.holding_para.holding_stage_paras[1].max_holding_velocity,process.screw_diameter, form_info.max_set.max_set_holding_velocity, form_info.max.max_holding_velocity)
        process.holding_time_2 = setting_process.holding_para.holding_stage_paras[1].holding_time
    }
    if (setting_process.holding_para.holding_stage >2){
        process.holding_pressure_3 = pageToDbPressure(setting_process.holding_para.holding_stage_paras[2].max_holding_pressure, form_info.max_set.max_set_holding_pressure, form_info.max.max_holding_pressure)
        process.holding_velocity_3 = velocityToVolume(setting_process.holding_para.holding_stage_paras[2].max_holding_velocity,process.screw_diameter, form_info.max_set.max_set_holding_velocity, form_info.max.max_holding_velocity)
        process.holding_time_3 = setting_process.holding_para.holding_stage_paras[2].holding_time
    }
    if (setting_process.holding_para.holding_stage >3){
        process.holding_pressure_4 = pageToDbPressure(setting_process.holding_para.holding_stage_paras[3].max_holding_pressure, form_info.max_set.max_set_holding_pressure, form_info.max.max_holding_pressure)
        process.holding_velocity_4 = velocityToVolume(setting_process.holding_para.holding_stage_paras[3].max_holding_velocity,process.screw_diameter, form_info.max_set.max_set_holding_velocity, form_info.max.max_holding_velocity)
        process.holding_time_4 = setting_process.holding_para.holding_stage_paras[3].holding_time
    }
    if (setting_process.holding_para.holding_stage >4){
        process.holding_pressure_5 = pageToDbPressure(setting_process.holding_para.holding_stage_paras[4].max_holding_pressure, form_info.max_set.max_set_holding_pressure, form_info.max.max_holding_pressure)
        process.holding_velocity_5 = velocityToVolume(setting_process.holding_para.holding_stage_paras[4].max_holding_velocity,process.screw_diameter, form_info.max_set.max_set_holding_velocity, form_info.max.max_holding_velocity)
        process.holding_time_5 = setting_process.holding_para.holding_stage_paras[4].holding_time
    }
    process.cooling_time = setting_process.injection_para.cooling_time
    // 计量模式
    process.metering_mode = setting_process.metering_para.metering_mode
    process.metering_stage = setting_process.metering_para.metering_stage
    process.metering_delay_time = setting_process.metering_para.metering_delay_time
    if ( setting_process.metering_para.metering_stage >0 ){
        process.metering_pressure_1 = pageToDbPressure(setting_process.metering_para.metering_stage_paras[0].metering_pressure, form_info.max_set.max_set_metering_pressure, form_info.max.max_metering_pressure)
        process.metering_screw_rotation_speed_1 = rpmTomms(setting_process.metering_para.metering_stage_paras[0].metering_screw_rotation_speed,process.screw_diameter, form_info.max_set.max_set_screw_rotation_speed, form_info.max.max_screw_rotation_speed)
        process.metering_back_pressure_1 = pageToDbPressure(setting_process.metering_para.metering_stage_paras[0].metering_back_pressure, form_info.max_set.max_set_metering_pressure, form_info.max.max_metering_pressure)
        process.metering_position_1 = positionToVolume(setting_process.metering_para.metering_stage_paras[0].metering_position, process.screw_diameter)
    }
    if ( setting_process.metering_para.metering_stage >1 ){
        process.metering_pressure_2 = pageToDbPressure(setting_process.metering_para.metering_stage_paras[1].metering_pressure, form_info.max_set.max_set_metering_pressure, form_info.max.max_metering_pressure)
        process.metering_screw_rotation_speed_2 = rpmTomms(setting_process.metering_para.metering_stage_paras[1].metering_screw_rotation_speed,process.screw_diameter, form_info.max_set.max_set_screw_rotation_speed, form_info.max.max_screw_rotation_speed)
        process.metering_back_pressure_2 = pageToDbPressure(setting_process.metering_para.metering_stage_paras[1].metering_back_pressure, form_info.max_set.max_set_metering_pressure, form_info.max.max_metering_pressure)
        process.metering_position_2 = positionToVolume(setting_process.metering_para.metering_stage_paras[1].metering_position, process.screw_diameter)
    }
    if ( setting_process.metering_para.metering_stage >2 ){
        process.metering_pressure_3 = pageToDbPressure(setting_process.metering_para.metering_stage_paras[2].metering_pressure, form_info.max_set.max_set_metering_pressure, form_info.max.max_metering_pressure)
        process.metering_screw_rotation_speed_3 = rpmTomms(setting_process.metering_para.metering_stage_paras[2].metering_screw_rotation_speed,process.screw_diameter, form_info.max_set.max_set_screw_rotation_speed, form_info.max.max_screw_rotation_speed)
        process.metering_back_pressure_3 = pageToDbPressure(setting_process.metering_para.metering_stage_paras[2].metering_back_pressure, form_info.max_set.max_set_metering_pressure, form_info.max.max_metering_pressure)
        process.metering_position_3 = positionToVolume(setting_process.metering_para.metering_stage_paras[2].metering_position, process.screw_diameter)
    }
    if ( setting_process.metering_para.metering_stage >3 ){
        process.metering_pressure_4 = pageToDbPressure(setting_process.metering_para.metering_stage_paras[3].metering_pressure, form_info.max_set.max_set_metering_pressure, form_info.max.max_metering_pressure)
        process.metering_screw_rotation_speed_4 = rpmTomms(setting_process.metering_para.metering_stage_paras[3].metering_screw_rotation_speed,process.screw_diameter, form_info.max_set.max_set_screw_rotation_speed, form_info.max.max_screw_rotation_speed)
        process.metering_back_pressure_4 = pageToDbPressure(setting_process.metering_para.metering_stage_paras[3].metering_back_pressure, form_info.max_set.max_set_metering_pressure, form_info.max.max_metering_pressure)
        process.metering_position_4 = positionToVolume(setting_process.metering_para.metering_stage_paras[3].metering_position, process.screw_diameter)
    }
    // process.metering_ending_position = setting_process.metering_para.metering_stage_paras[setting_process.metering_para.metering_stage-1].metering_position
    process.decompressure_mode_before_metering = setting_process.metering_para.decompressure_mode_before_metering
    process.decompressure_pressure_before_metering = pageToDbPressure(setting_process.metering_para.decompressure_paras[0].pressure, form_info.max_set.max_set_metering_pressure, form_info.max.max_metering_pressure)
    process.decompressure_velocity_before_metering = velocityToVolume(setting_process.metering_para.decompressure_paras[0].velocity, process.screw_diameter, form_info.max_set.max_set_metering_pressure, form_info.max.max_metering_pressure)
    process.decompressure_distance_before_metering = positionToVolume(setting_process.metering_para.decompressure_paras[0].distance, process.screw_diameter)
    process.decompressure_time_before_metering = setting_process.metering_para.decompressure_paras[0].time
    process.decompressure_delay_time_before_metering = setting_process.metering_para.metering_stage
    process.decompressure_mode_after_metering = setting_process.metering_para.decompressure_mode_after_metering
    process.decompressure_pressure_after_metering = pageToDbPressure(setting_process.metering_para.decompressure_paras[1].pressure, form_info.max_set.max_set_metering_pressure, form_info.max.max_metering_pressure)
    process.decompressure_velocity_after_metering = velocityToVolume(setting_process.metering_para.decompressure_paras[1].velocity, process.screw_diameter, form_info.max_set.max_set_metering_pressure, form_info.max.max_metering_pressure)
    process.decompressure_distance_after_metering = positionToVolume(setting_process.metering_para.decompressure_paras[1].distance, process.screw_diameter)
    process.decompressure_time_after_metering = setting_process.metering_para.decompressure_paras[0].time
    return process
}
// 注射压力,当前机器的注射压力设定值/最大设定注射压力*成型参数最大注射压力
// 保压压力,当前机器的保压压力设定值/最大设定保压压力*成型参数最大保压压力
// 计量压力,当前机器的计量压力设定值/最大设定计量压力*成型参数最大计量压力
// 计量背压,当前机器的计量背压设定值/最大设定计量背压*成型参数最大计量背压
// 松退压力,当前机器的松退压力设定值/最大设定松退压力*成型参数最大松退压力
// 页面参数到数据库
export function pageToDbPressure(pagePressure: any, max_set:any, max:any){
    return pagePressure/max_set*max
}
// 数据库到页面参数
export function dbToPagePressure(dbPressure: any, max_set:any, max:any){
    return dbPressure/max*max_set
}
// 注射速度,当前机器的注射速度设定值/最大设定注射速度*成型参数最大注射速度
// 保压速度,当前机器的保压速度设定值/最大设定保压速度*成型参数最大保压速度
// 计量速度,当前机器的计量速度设定值/最大设定计量速度*成型参数最大计量速度
// 射退速度,当前机器的射退速度设定值/最大设定射退速度*成型参数最大射退速度
// 工艺优化中,速度的单位是mm/s,存储在process表中时,要转化为cm³/s
export function velocityToVolume(velocity: any, screw_diameter:any, max_set:any, max:any){
    return velocity*3.14*screw_diameter*screw_diameter/4000/max_set*max
}
// 存储在process表中时,速度单位为cm³/s,页面上展示的速度单位是mm/s
export function volumeToVelocity(volume: any, screw_diameter:any, max_set:any, max:any){
    return volume*4000/(3.14*screw_diameter*screw_diameter)*max_set/max
}
// 注射位置:工艺优化中,注射位置的单位是mm,存储在process表中时,要转化为cm³
export function positionToVolume(velocity: any, screw_diameter:any){
    return velocity*3.14*screw_diameter*screw_diameter/4000
}
// 注射位置:存储在process表中时,注射位置单位为cm³,页面上展示的速度单位是mm
export function volumeToPosition(volume: any, screw_diameter:any){
    return volume*4000/(3.14*screw_diameter*screw_diameter)
}
// 螺杆转速:工艺优化中,转速的单位是rpm,存储在process表中时,要转化为mm/s
export function rpmTomms(rpm: any, screw_diameter:any, max_set:any, max:any){
    return rpm/60*3.14*screw_diameter/max_set*max
}
// 螺杆转速:存储在process表中时,转速单位为mm/s,页面上展示的转速单位是rpm
export function mmsTorpm(mms: any, screw_diameter:any, max_set:any, max:any){
    return mms/(3.14*screw_diameter)*60*max_set/max
}
export function processToSettingProcess(process: any, form_info:any){
    let setting_process = form_info.trial_process
    setting_process.temp_para.barrel_temperature_stage = process.barrel_temperature_stage
    if(process.barrel_temperature_stage >0){
        setting_process.temp_para.barrel_temperature_stage_paras[0].barrel_temperature = process.nozzle_temperature
    }
    if ( process.barrel_temperature_stage>1){
        setting_process.temp_para.barrel_temperature_stage_paras[1].barrel_temperature = process.barrel_temperature_1
    }
    if ( process.barrel_temperature_stage>2){
        setting_process.temp_para.barrel_temperature_stage_paras[2].barrel_temperature = process.barrel_temperature_2
    }
    if ( process.barrel_temperature_stage>3){
        setting_process.temp_para.barrel_temperature_stage_paras[3].barrel_temperature = process.barrel_temperature_3
    }
    if ( process.barrel_temperature_stage>4){
        setting_process.temp_para.barrel_temperature_stage_paras[4].barrel_temperature = process.barrel_temperature_4
    }
    if ( process.barrel_temperature_stage>5){
        setting_process.temp_para.barrel_temperature_stage_paras[5].barrel_temperature = process.barrel_temperature_5
    }
    if ( process.barrel_temperature_stage>6){
        setting_process.temp_para.barrel_temperature_stage_paras[6].barrel_temperature = process.barrel_temperature_6
    }
    if ( process.barrel_temperature_stage>7){
        setting_process.temp_para.barrel_temperature_stage_paras[7].barrel_temperature = process.barrel_temperature_7
    }
    if ( process.barrel_temperature_stage>8){
        setting_process.temp_para.barrel_temperature_stage_paras[8].barrel_temperature = process.barrel_temperature_8
    }
    if ( process.barrel_temperature_stage>9){
        setting_process.temp_para.barrel_temperature_stage_paras[9].barrel_temperature = process.barrel_temperature_9
    }
    setting_process.injection_para.injection_stage = process.injection_stage
    setting_process.injection_para.injection_time = process.injection_time
    setting_process.injection_para.injection_delay_time = process.injection_delay_time
    setting_process.injection_para.cooling_time = process.cooling_time
    if ( process.injection_stage>0){
        setting_process.injection_para.injection_stage_paras[0].max_injection_pressure = dbToPagePressure(process.injection_pressure_1,form_info.trial_machine.max_set.max_set_injection_pressure,form_info.trial_machine.max.max_injection_pressure).toFixed(2)
        setting_process.injection_para.injection_stage_paras[0].max_injection_velocity = volumeToVelocity(process.injection_velocity_1, process.screw_diameter,form_info.trial_machine.max_set.max_set_injection_velocity,form_info.trial_machine.max.max_injection_velocity).toFixed(2)
        setting_process.injection_para.injection_stage_paras[0].injection_position = volumeToPosition(process.injection_position_1, process.screw_diameter).toFixed(2)
    }
    if ( process.injection_stage>1){
        setting_process.injection_para.injection_stage_paras[1].max_injection_pressure = dbToPagePressure(process.injection_pressure_2,form_info.trial_machine.max_set.max_set_injection_pressure,form_info.trial_machine.max.max_injection_pressure).toFixed(2)
        setting_process.injection_para.injection_stage_paras[1].max_injection_velocity = volumeToVelocity(process.injection_velocity_2, process.screw_diameter,form_info.trial_machine.max_set.max_set_injection_velocity,form_info.trial_machine.max.max_injection_velocity).toFixed(2)
        setting_process.injection_para.injection_stage_paras[1].injection_position = volumeToPosition(process.injection_position_2, process.screw_diameter).toFixed(2)
    }
    if ( process.injection_stage>2){
        setting_process.injection_para.injection_stage_paras[2].max_injection_pressure = dbToPagePressure(process.injection_pressure_3,form_info.trial_machine.max_set.max_set_injection_pressure,form_info.trial_machine.max.max_injection_pressure).toFixed(2)
        setting_process.injection_para.injection_stage_paras[2].max_injection_velocity = volumeToVelocity(process.injection_velocity_3, process.screw_diameter,form_info.trial_machine.max_set.max_set_injection_velocity,form_info.trial_machine.max.max_injection_velocity).toFixed(2)
        setting_process.injection_para.injection_stage_paras[2].injection_position = volumeToPosition(process.injection_position_3, process.screw_diameter).toFixed(2)
    }
    if ( process.injection_stage>3){
        setting_process.injection_para.injection_stage_paras[3].max_injection_pressure = dbToPagePressure(process.injection_pressure_4,form_info.trial_machine.max_set.max_set_injection_pressure,form_info.trial_machine.max.max_injection_pressure).toFixed(2)
        setting_process.injection_para.injection_stage_paras[3].max_injection_velocity = volumeToVelocity(process.injection_velocity_4, process.screw_diameter,form_info.trial_machine.max_set.max_set_injection_velocity,form_info.trial_machine.max.max_injection_velocity).toFixed(2)
        setting_process.injection_para.injection_stage_paras[3].injection_position = volumeToPosition(process.injection_position_4, process.screw_diameter).toFixed(2)
    }
    if ( process.injection_stage>4){
        setting_process.injection_para.injection_stage_paras[4].max_injection_pressure = dbToPagePressure(process.injection_pressure_5,form_info.trial_machine.max_set.max_set_injection_pressure,form_info.trial_machine.max.max_injection_pressure).toFixed(2)
        setting_process.injection_para.injection_stage_paras[4].max_injection_velocity = volumeToVelocity(process.injection_velocity_5, process.screw_diameter,form_info.trial_machine.max_set.max_set_injection_velocity,form_info.trial_machine.max.max_injection_velocity).toFixed(2)
        setting_process.injection_para.injection_stage_paras[4].injection_position = volumeToPosition(process.injection_position_5, process.screw_diameter).toFixed(2)
    }
    if ( process.injection_stage>5){
        setting_process.injection_para.injection_stage_paras[5].max_injection_pressure = dbToPagePressure(process.injection_pressure_6,form_info.trial_machine.max_set.max_set_injection_pressure,form_info.trial_machine.max.max_injection_pressure).toFixed(2)
        setting_process.injection_para.injection_stage_paras[5].max_injection_velocity = volumeToVelocity(process.injection_velocity_6, process.screw_diameter,form_info.trial_machine.max_set.max_set_injection_velocity,form_info.trial_machine.max.max_injection_velocity).toFixed(2)
        setting_process.injection_para.injection_stage_paras[5].injection_position = volumeToPosition(process.injection_position_6, process.screw_diameter).toFixed(2)
    }
    setting_process.holding_para.VP_switch_mode = process.VP_switch_mode
    setting_process.holding_para.VP_switch_position = volumeToPosition(process.VP_switch_position, process.screw_diameter).toFixed(2)
    setting_process.holding_para.VP_switch_time = process.VP_switch_time
    setting_process.holding_para.VP_switch_pressure = dbToPagePressure(process.VP_switch_pressure,form_info.trial_machine.max_set.max_set_holding_pressure,form_info.trial_machine.max.max_holding_pressure).toFixed(2)
    // VP切换速度
    setting_process.holding_para.holding_stage = process.holding_stage
    if ( process.holding_stage >0){
        setting_process.holding_para.holding_stage_paras[0].max_holding_pressure =dbToPagePressure(process.holding_pressure_1,form_info.trial_machine.max_set.max_set_holding_pressure,form_info.trial_machine.max.max_holding_pressure).toFixed(2)
        setting_process.holding_para.holding_stage_paras[0].max_holding_velocity = volumeToVelocity(process.holding_velocity_1, process.screw_diameter,form_info.trial_machine.max_set.max_set_holding_velocity,form_info.trial_machine.max.max_holding_velocity).toFixed(2)
        setting_process.holding_para.holding_stage_paras[0].holding_time = process.holding_time_1
    }
    if ( process.holding_stage >1){
        setting_process.holding_para.holding_stage_paras[1].max_holding_pressure =dbToPagePressure(process.holding_pressure_2,form_info.trial_machine.max_set.max_set_holding_pressure,form_info.trial_machine.max.max_holding_pressure).toFixed(2)
        setting_process.holding_para.holding_stage_paras[1].max_holding_velocity = volumeToVelocity(process.holding_velocity_2, process.screw_diameter,form_info.trial_machine.max_set.max_set_holding_velocity,form_info.trial_machine.max.max_holding_velocity).toFixed(2)
        setting_process.holding_para.holding_stage_paras[1].holding_time = process.holding_time_2
    }
    if ( process.holding_stage >2){
        setting_process.holding_para.holding_stage_paras[2].max_holding_pressure =dbToPagePressure(process.holding_pressure_3,form_info.trial_machine.max_set.max_set_holding_pressure,form_info.trial_machine.max.max_holding_pressure).toFixed(2)
        setting_process.holding_para.holding_stage_paras[2].max_holding_velocity = volumeToVelocity(process.holding_velocity_3, process.screw_diameter,form_info.trial_machine.max_set.max_set_holding_velocity,form_info.trial_machine.max.max_holding_velocity).toFixed(2)
        setting_process.holding_para.holding_stage_paras[2].holding_time = process.holding_time_3
    }
    if ( process.holding_stage >3){
        setting_process.holding_para.holding_stage_paras[3].max_holding_pressure =dbToPagePressure(process.holding_pressure_4,form_info.trial_machine.max_set.max_set_holding_pressure,form_info.trial_machine.max.max_holding_pressure).toFixed(2)
        setting_process.holding_para.holding_stage_paras[3].max_holding_velocity = volumeToVelocity(process.holding_velocity_4, process.screw_diameter,form_info.trial_machine.max_set.max_set_holding_velocity,form_info.trial_machine.max.max_holding_velocity).toFixed(2)
        setting_process.holding_para.holding_stage_paras[3].holding_time = process.holding_time_4
    }
    if ( process.holding_stage >4){
        setting_process.holding_para.holding_stage_paras[4].max_holding_pressure =dbToPagePressure(process.holding_pressure_5,form_info.trial_machine.max_set.max_set_holding_pressure,form_info.trial_machine.max.max_holding_pressure).toFixed(2)
        setting_process.holding_para.holding_stage_paras[4].max_holding_velocity = volumeToVelocity(process.holding_velocity_5, process.screw_diameter,form_info.trial_machine.max_set.max_set_holding_velocity,form_info.trial_machine.max.max_holding_velocity).toFixed(2)
        setting_process.holding_para.holding_stage_paras[4].holding_time = process.holding_time_5
    }
    setting_process.metering_para.metering_stage = process.metering_stage
    if ( process.metering_stage >0){
        setting_process.metering_para.metering_stage_paras[0].metering_pressure = dbToPagePressure(process.metering_pressure_1,form_info.trial_machine.max_set.max_set_metering_pressure,form_info.trial_machine.max.max_metering_pressure).toFixed(2)
        setting_process.metering_para.metering_stage_paras[0].metering_screw_rotation_speed = mmsTorpm(process.metering_screw_rotation_speed_1, process.screw_diameter,form_info.trial_machine.max_set.max_set_screw_rotation_speed,form_info.trial_machine.max.max_screw_rotation_speed).toFixed(2)
        setting_process.metering_para.metering_stage_paras[0].metering_back_pressure = dbToPagePressure(process.metering_back_pressure_1,form_info.trial_machine.max_set.max_set_metering_pressure,form_info.trial_machine.max.max_metering_pressure).toFixed(2)
        setting_process.metering_para.metering_stage_paras[0].metering_position = volumeToPosition(process.metering_position_1, process.screw_diameter).toFixed(2)
    }
    if ( process.metering_stage >1){
        setting_process.metering_para.metering_stage_paras[1].metering_pressure = dbToPagePressure(process.metering_pressure_2,form_info.trial_machine.max_set.max_set_metering_pressure,form_info.trial_machine.max.max_metering_pressure).toFixed(2)
        setting_process.metering_para.metering_stage_paras[1].metering_screw_rotation_speed = mmsTorpm(process.metering_screw_rotation_speed_2, process.screw_diameter,form_info.trial_machine.max_set.max_set_screw_rotation_speed,form_info.trial_machine.max.max_screw_rotation_speed).toFixed(2)
        setting_process.metering_para.metering_stage_paras[1].metering_back_pressure = dbToPagePressure(process.metering_back_pressure_2,form_info.trial_machine.max_set.max_set_metering_pressure,form_info.trial_machine.max.max_metering_pressure).toFixed(2)
        setting_process.metering_para.metering_stage_paras[1].metering_position = volumeToPosition(process.metering_position_2, process.screw_diameter).toFixed(2)
    }
    if ( process.metering_stage >2){
        setting_process.metering_para.metering_stage_paras[2].metering_pressure = dbToPagePressure(process.metering_pressure_3,form_info.trial_machine.max_set.max_set_metering_pressure,form_info.trial_machine.max.max_metering_pressure).toFixed(2)
        setting_process.metering_para.metering_stage_paras[2].metering_screw_rotation_speed = mmsTorpm(process.metering_screw_rotation_speed_3, process.screw_diameter,form_info.trial_machine.max_set.max_set_screw_rotation_speed,form_info.trial_machine.max.max_screw_rotation_speed).toFixed(2)
        setting_process.metering_para.metering_stage_paras[2].metering_back_pressure = dbToPagePressure(process.metering_back_pressure_3,form_info.trial_machine.max_set.max_set_metering_pressure,form_info.trial_machine.max.max_metering_pressure).toFixed(2)
        setting_process.metering_para.metering_stage_paras[2].metering_position = volumeToPosition(process.metering_position_3, process.screw_diameter).toFixed(2)
    }
    if ( process.metering_stage >3){
        setting_process.metering_para.metering_stage_paras[3].metering_pressure = dbToPagePressure(process.metering_pressure_4,form_info.trial_machine.max_set.max_set_metering_pressure,form_info.trial_machine.max.max_metering_pressure).toFixed(2)
        setting_process.metering_para.metering_stage_paras[3].metering_screw_rotation_speed = mmsTorpm(process.metering_screw_rotation_speed_4, process.screw_diameter,form_info.trial_machine.max_set.max_set_screw_rotation_speed,form_info.trial_machine.max.max_screw_rotation_speed).toFixed(2)
        setting_process.metering_para.metering_stage_paras[3].metering_back_pressure = dbToPagePressure(process.metering_back_pressure_4,form_info.trial_machine.max_set.max_set_metering_pressure,form_info.trial_machine.max.max_metering_pressure).toFixed(2)
        setting_process.metering_para.metering_stage_paras[3].metering_position = volumeToPosition(process.metering_position_4, process.screw_diameter).toFixed(2)
    }    
    setting_process.metering_para.metering_delay_time = process.metering_delay_time
    // 注射终止位置
    setting_process.metering_para.metering_ending_position = process.metering_ending_position 
    setting_process.metering_para.decompressure_mode_before_metering = process.decompressure_mode_before_metering
    setting_process.metering_para.decompressure_paras[0].pressure = dbToPagePressure(process.decompressure_pressure_before_metering,form_info.trial_machine.max_set.max_set_metering_pressure,form_info.trial_machine.max.max_metering_pressure).toFixed(2)
    setting_process.metering_para.decompressure_paras[0].velocity = volumeToVelocity(process.decompressure_velocity_before_metering, process.screw_diameter,form_info.trial_machine.max_set.max_set_metering_pressure,form_info.trial_machine.max.max_metering_pressure).toFixed(2)
    setting_process.metering_para.decompressure_paras[0].distance = volumeToPosition(process.decompressure_distance_before_metering, process.screw_diameter).toFixed(2)
    // setting_process.metering_para.decompressure_paras[0].time = process.decompressure_time_before_metering
    setting_process.metering_para.decompressure_delay_time_before_metering = process.decompressure_delay_time_before_metering
    setting_process.metering_para.decompressure_mode_after_metering = process.decompressure_mode_after_metering
    setting_process.metering_para.decompressure_paras[1].pressure = dbToPagePressure(process.decompressure_pressure_after_metering,form_info.trial_machine.max_set.max_set_metering_pressure,form_info.trial_machine.max.max_metering_pressure).toFixed(2)
    setting_process.metering_para.decompressure_paras[1].velocity = volumeToVelocity(process.decompressure_velocity_after_metering, process.screw_diameter,form_info.trial_machine.max_set.max_set_metering_pressure,form_info.trial_machine.max.max_metering_pressure).toFixed(2)
    setting_process.metering_para.decompressure_paras[1].distance = volumeToPosition(process.decompressure_distance_after_metering, process.screw_diameter).toFixed(2)
    // setting_process.metering_para.decompressure_paras[1].time = process.decompressure_time_after_metering
    return setting_process
}
export function transplantProcess(process: any, form_info:any){
    let transplant_process = form_info.transplant_process
    transplant_process.temp_para.barrel_temperature_stage = process.barrel_temperature_stage
    if(process.barrel_temperature_stage >0){
        transplant_process.temp_para.barrel_temperature_stage_paras[0].barrel_temperature = process.nozzle_temperature
    }
    if ( process.barrel_temperature_stage>1){
        transplant_process.temp_para.barrel_temperature_stage_paras[1].barrel_temperature = process.barrel_temperature_1
    }
    if ( process.barrel_temperature_stage>2){
        transplant_process.temp_para.barrel_temperature_stage_paras[2].barrel_temperature = process.barrel_temperature_2
    }
    if ( process.barrel_temperature_stage>3){
        transplant_process.temp_para.barrel_temperature_stage_paras[3].barrel_temperature = process.barrel_temperature_3
    }
    if ( process.barrel_temperature_stage>4){
        transplant_process.temp_para.barrel_temperature_stage_paras[4].barrel_temperature = process.barrel_temperature_4
    }
    if ( process.barrel_temperature_stage>5){
        transplant_process.temp_para.barrel_temperature_stage_paras[5].barrel_temperature = process.barrel_temperature_5
    }
    if ( process.barrel_temperature_stage>6){
        transplant_process.temp_para.barrel_temperature_stage_paras[6].barrel_temperature = process.barrel_temperature_6
    }
    if ( process.barrel_temperature_stage>7){
        transplant_process.temp_para.barrel_temperature_stage_paras[7].barrel_temperature = process.barrel_temperature_7
    }
    if ( process.barrel_temperature_stage>8){
        transplant_process.temp_para.barrel_temperature_stage_paras[8].barrel_temperature = process.barrel_temperature_8
    }
    if ( process.barrel_temperature_stage>9){
        transplant_process.temp_para.barrel_temperature_stage_paras[9].barrel_temperature = process.barrel_temperature_9
    }
    transplant_process.injection_para.injection_stage = process.injection_stage
    transplant_process.injection_para.injection_time = process.injection_time
    transplant_process.injection_para.injection_delay_time = process.injection_delay_time
    transplant_process.injection_para.cooling_time = process.cooling_time
    if ( process.injection_stage>0){
        transplant_process.injection_para.injection_stage_paras[0].max_injection_pressure = dbToPagePressure(process.injection_pressure_1,form_info.transplant_machine.max_set.max_set_injection_pressure,form_info.transplant_machine.max.max_injection_pressure).toFixed(2)
        transplant_process.injection_para.injection_stage_paras[0].max_injection_velocity = volumeToVelocity(process.injection_velocity_1, form_info.transplant_machine.transplant_machine_data.screw_diameter,form_info.transplant_machine.max_set.max_set_injection_velocity,form_info.transplant_machine.max.max_injection_velocity).toFixed(2)
        transplant_process.injection_para.injection_stage_paras[0].injection_position = volumeToPosition(process.injection_position_1, form_info.transplant_machine.transplant_machine_data.screw_diameter).toFixed(2)
    }
    if ( process.injection_stage>1){
        transplant_process.injection_para.injection_stage_paras[1].max_injection_pressure = dbToPagePressure(process.injection_pressure_2,form_info.transplant_machine.max_set.max_set_injection_pressure,form_info.transplant_machine.max.max_injection_pressure).toFixed(2)
        transplant_process.injection_para.injection_stage_paras[1].max_injection_velocity = volumeToVelocity(process.injection_velocity_2, form_info.transplant_machine.transplant_machine_data.screw_diameter,form_info.transplant_machine.max_set.max_set_injection_velocity,form_info.transplant_machine.max.max_injection_velocity).toFixed(2)
        transplant_process.injection_para.injection_stage_paras[1].injection_position = volumeToPosition(process.injection_position_2, form_info.transplant_machine.transplant_machine_data.screw_diameter).toFixed(2)
    }
    if ( process.injection_stage>2){
        transplant_process.injection_para.injection_stage_paras[2].max_injection_pressure = dbToPagePressure(process.injection_pressure_3,form_info.transplant_machine.max_set.max_set_injection_pressure,form_info.transplant_machine.max.max_injection_pressure).toFixed(2)
        transplant_process.injection_para.injection_stage_paras[2].max_injection_velocity = volumeToVelocity(process.injection_velocity_3, form_info.transplant_machine.transplant_machine_data.screw_diameter,form_info.transplant_machine.max_set.max_set_injection_velocity,form_info.transplant_machine.max.max_injection_velocity).toFixed(2)
        transplant_process.injection_para.injection_stage_paras[2].injection_position = volumeToPosition(process.injection_position_3, form_info.transplant_machine.transplant_machine_data.screw_diameter).toFixed(2)
    }
    if ( process.injection_stage>3){
        transplant_process.injection_para.injection_stage_paras[3].max_injection_pressure = dbToPagePressure(process.injection_pressure_4,form_info.transplant_machine.max_set.max_set_injection_pressure,form_info.transplant_machine.max.max_injection_pressure).toFixed(2)
        transplant_process.injection_para.injection_stage_paras[3].max_injection_velocity = volumeToVelocity(process.injection_velocity_4, form_info.transplant_machine.transplant_machine_data.screw_diameter,form_info.transplant_machine.max_set.max_set_injection_velocity,form_info.transplant_machine.max.max_injection_velocity).toFixed(2)
        transplant_process.injection_para.injection_stage_paras[3].injection_position = volumeToPosition(process.injection_position_4, form_info.transplant_machine.transplant_machine_data.screw_diameter).toFixed(2)
    }
    if ( process.injection_stage>4){
        transplant_process.injection_para.injection_stage_paras[4].max_injection_pressure = dbToPagePressure(process.injection_pressure_5,form_info.transplant_machine.max_set.max_set_injection_pressure,form_info.transplant_machine.max.max_injection_pressure).toFixed(2)
        transplant_process.injection_para.injection_stage_paras[4].max_injection_velocity = volumeToVelocity(process.injection_velocity_5, form_info.transplant_machine.transplant_machine_data.screw_diameter,form_info.transplant_machine.max_set.max_set_injection_velocity,form_info.transplant_machine.max.max_injection_velocity).toFixed(2)
        transplant_process.injection_para.injection_stage_paras[4].injection_position = volumeToPosition(process.injection_position_5, form_info.transplant_machine.transplant_machine_data.screw_diameter).toFixed(2)
    }
    if ( process.injection_stage>5){
        transplant_process.injection_para.injection_stage_paras[5].max_injection_pressure = dbToPagePressure(process.injection_pressure_6,form_info.transplant_machine.max_set.max_set_injection_pressure,form_info.transplant_machine.max.max_injection_pressure).toFixed(2)
        transplant_process.injection_para.injection_stage_paras[5].max_injection_velocity = volumeToVelocity(process.injection_velocity_6, form_info.transplant_machine.transplant_machine_data.screw_diameter,form_info.transplant_machine.max_set.max_set_injection_velocity,form_info.transplant_machine.max.max_injection_velocity).toFixed(2)
        transplant_process.injection_para.injection_stage_paras[5].injection_position = volumeToPosition(process.injection_position_6, form_info.transplant_machine.transplant_machine_data.screw_diameter).toFixed(2)
    }
    transplant_process.holding_para.VP_switch_mode = process.VP_switch_mode
    transplant_process.holding_para.VP_switch_position = volumeToPosition(process.VP_switch_position, form_info.transplant_machine.transplant_machine_data.screw_diameter).toFixed(2)
    transplant_process.holding_para.VP_switch_time = process.VP_switch_time
    transplant_process.holding_para.VP_switch_pressure = dbToPagePressure(process.VP_switch_pressure,form_info.transplant_machine.max_set.max_set_holding_pressure,form_info.transplant_machine.max.max_holding_pressure).toFixed(2)
    // VP切换速度
    // transplant_process.holding_para.VP_switch_position = volumeToVelocity(process.VP_switch_velocity, form_info.transplant_machine.transplant_machine_data.screw_diameter).toFixed(2)
    transplant_process.holding_para.holding_stage = process.holding_stage
    if ( process.holding_stage >0){
        transplant_process.holding_para.holding_stage_paras[0].max_holding_pressure =dbToPagePressure(process.holding_pressure_1,form_info.transplant_machine.max_set.max_set_holding_pressure,form_info.transplant_machine.max.max_holding_pressure).toFixed(2)
        transplant_process.holding_para.holding_stage_paras[0].max_holding_velocity = volumeToVelocity(process.holding_velocity_1, form_info.transplant_machine.transplant_machine_data.screw_diameter,form_info.transplant_machine.max_set.max_set_holding_velocity,form_info.transplant_machine.max.max_holding_velocity).toFixed(2)
        transplant_process.holding_para.holding_stage_paras[0].holding_time = process.holding_time_1
    }
    if ( process.holding_stage >1){
        transplant_process.holding_para.holding_stage_paras[1].max_holding_pressure =dbToPagePressure(process.holding_pressure_2,form_info.transplant_machine.max_set.max_set_holding_pressure,form_info.transplant_machine.max.max_holding_pressure).toFixed(2)
        transplant_process.holding_para.holding_stage_paras[1].max_holding_velocity = volumeToVelocity(process.holding_velocity_2, form_info.transplant_machine.transplant_machine_data.screw_diameter,form_info.transplant_machine.max_set.max_set_holding_velocity,form_info.transplant_machine.max.max_holding_velocity).toFixed(2)
        transplant_process.holding_para.holding_stage_paras[1].holding_time = process.holding_time_2
    }
    if ( process.holding_stage >2){
        transplant_process.holding_para.holding_stage_paras[2].max_holding_pressure =dbToPagePressure(process.holding_pressure_3,form_info.transplant_machine.max_set.max_set_holding_pressure,form_info.transplant_machine.max.max_holding_pressure).toFixed(2)
        transplant_process.holding_para.holding_stage_paras[2].max_holding_velocity = volumeToVelocity(process.holding_velocity_3, form_info.transplant_machine.transplant_machine_data.screw_diameter,form_info.transplant_machine.max_set.max_set_holding_velocity,form_info.transplant_machine.max.max_holding_velocity).toFixed(2)
        transplant_process.holding_para.holding_stage_paras[2].holding_time = process.holding_time_3
    }
    if ( process.holding_stage >3){
        transplant_process.holding_para.holding_stage_paras[3].max_holding_pressure =dbToPagePressure(process.holding_pressure_4,form_info.transplant_machine.max_set.max_set_holding_pressure,form_info.transplant_machine.max.max_holding_pressure).toFixed(2)
        transplant_process.holding_para.holding_stage_paras[3].max_holding_velocity = volumeToVelocity(process.holding_velocity_4, form_info.transplant_machine.transplant_machine_data.screw_diameter,form_info.transplant_machine.max_set.max_set_holding_velocity,form_info.transplant_machine.max.max_holding_velocity).toFixed(2)
        transplant_process.holding_para.holding_stage_paras[3].holding_time = process.holding_time_4
    }
    if ( process.holding_stage >4){
        transplant_process.holding_para.holding_stage_paras[4].max_holding_pressure =dbToPagePressure(process.holding_pressure_5,form_info.transplant_machine.max_set.max_set_holding_pressure,form_info.transplant_machine.max.max_holding_pressure).toFixed(2)
        transplant_process.holding_para.holding_stage_paras[4].max_holding_velocity = volumeToVelocity(process.holding_velocity_5, form_info.transplant_machine.transplant_machine_data.screw_diameter,form_info.transplant_machine.max_set.max_set_holding_velocity,form_info.transplant_machine.max.max_holding_velocity).toFixed(2)
        transplant_process.holding_para.holding_stage_paras[4].holding_time = process.holding_time_5
    }
    transplant_process.metering_para.metering_stage = process.metering_stage
    if ( process.metering_stage >0){
        transplant_process.metering_para.metering_stage_paras[0].metering_pressure = dbToPagePressure(process.metering_pressure_1,form_info.transplant_machine.max_set.max_set_metering_pressure,form_info.transplant_machine.max.max_metering_pressure).toFixed(2)
        transplant_process.metering_para.metering_stage_paras[0].metering_screw_rotation_speed = mmsTorpm(process.metering_screw_rotation_speed_1, form_info.transplant_machine.transplant_machine_data.screw_diameter,form_info.transplant_machine.max_set.max_set_screw_rotation_speed,form_info.transplant_machine.max.max_screw_rotation_speed).toFixed(2)
        transplant_process.metering_para.metering_stage_paras[0].metering_back_pressure = dbToPagePressure(process.metering_back_pressure_1,form_info.transplant_machine.max_set.max_set_metering_pressure,form_info.transplant_machine.max.max_metering_pressure).toFixed(2)
        transplant_process.metering_para.metering_stage_paras[0].metering_position = volumeToPosition(process.metering_position_1, form_info.transplant_machine.transplant_machine_data.screw_diameter).toFixed(2)
    }
    if ( process.metering_stage >1){
        transplant_process.metering_para.metering_stage_paras[1].metering_pressure = dbToPagePressure(process.metering_pressure_2,form_info.transplant_machine.max_set.max_set_metering_pressure,form_info.transplant_machine.max.max_metering_pressure).toFixed(2)
        transplant_process.metering_para.metering_stage_paras[1].metering_screw_rotation_speed = mmsTorpm(process.metering_screw_rotation_speed_2, form_info.transplant_machine.transplant_machine_data.screw_diameter,form_info.transplant_machine.max_set.max_set_screw_rotation_speed,form_info.transplant_machine.max.max_screw_rotation_speed).toFixed(2)
        transplant_process.metering_para.metering_stage_paras[1].metering_back_pressure = dbToPagePressure(process.metering_back_pressure_2,form_info.transplant_machine.max_set.max_set_metering_pressure,form_info.transplant_machine.max.max_metering_pressure).toFixed(2)
        transplant_process.metering_para.metering_stage_paras[1].metering_position = volumeToPosition(process.metering_position_2, form_info.transplant_machine.transplant_machine_data.screw_diameter).toFixed(2)
    }
    if ( process.metering_stage >2){
        transplant_process.metering_para.metering_stage_paras[2].metering_pressure = dbToPagePressure(process.metering_pressure_3,form_info.transplant_machine.max_set.max_set_metering_pressure,form_info.transplant_machine.max.max_metering_pressure).toFixed(2)
        transplant_process.metering_para.metering_stage_paras[2].metering_screw_rotation_speed = mmsTorpm(process.metering_screw_rotation_speed_3, form_info.transplant_machine.transplant_machine_data.screw_diameter,form_info.transplant_machine.max_set.max_set_screw_rotation_speed,form_info.transplant_machine.max.max_screw_rotation_speed).toFixed(2)
        transplant_process.metering_para.metering_stage_paras[2].metering_back_pressure = dbToPagePressure(process.metering_back_pressure_3,form_info.transplant_machine.max_set.max_set_metering_pressure,form_info.transplant_machine.max.max_metering_pressure).toFixed(2)
        transplant_process.metering_para.metering_stage_paras[2].metering_position = volumeToPosition(process.metering_position_3, form_info.transplant_machine.transplant_machine_data.screw_diameter).toFixed(2)
    }
    if ( process.metering_stage >3){
        transplant_process.metering_para.metering_stage_paras[3].metering_pressure = dbToPagePressure(process.metering_pressure_4,form_info.transplant_machine.max_set.max_set_metering_pressure,form_info.transplant_machine.max.max_metering_pressure).toFixed(2)
        transplant_process.metering_para.metering_stage_paras[3].metering_screw_rotation_speed = mmsTorpm(process.metering_screw_rotation_speed_4, form_info.transplant_machine.transplant_machine_data.screw_diameter,form_info.transplant_machine.max_set.max_set_screw_rotation_speed,form_info.transplant_machine.max.max_screw_rotation_speed).toFixed(2)
        transplant_process.metering_para.metering_stage_paras[3].metering_back_pressure = dbToPagePressure(process.metering_back_pressure_4,form_info.transplant_machine.max_set.max_set_metering_pressure,form_info.transplant_machine.max.max_metering_pressure).toFixed(2)
        transplant_process.metering_para.metering_stage_paras[3].metering_position = volumeToPosition(process.metering_position_4, form_info.transplant_machine.transplant_machine_data.screw_diameter).toFixed(2)
    }    
    transplant_process.metering_para.metering_delay_time = process.metering_delay_time
    // 注射终止位置
    transplant_process.metering_para.metering_ending_position = process.metering_ending_position 
    transplant_process.metering_para.decompressure_mode_before_metering = process.decompressure_mode_before_metering
    transplant_process.metering_para.decompressure_paras[0].pressure = dbToPagePressure(process.decompressure_pressure_before_metering,form_info.transplant_machine.max_set.max_set_metering_pressure,form_info.transplant_machine.max.max_metering_pressure).toFixed(2)
    transplant_process.metering_para.decompressure_paras[0].velocity = volumeToVelocity(process.decompressure_velocity_before_metering, form_info.transplant_machine.transplant_machine_data.screw_diameter,form_info.transplant_machine.max_set.max_set_metering_pressure,form_info.transplant_machine.max.max_metering_pressure).toFixed(2)
    transplant_process.metering_para.decompressure_paras[0].distance = volumeToPosition(process.decompressure_distance_before_metering, form_info.transplant_machine.transplant_machine_data.screw_diameter).toFixed(2)
    // transplant_process.metering_para.decompressure_paras[0].time = process.decompressure_time_before_metering
    transplant_process.metering_para.decompressure_delay_time_before_metering = process.decompressure_delay_time_before_metering
    transplant_process.metering_para.decompressure_mode_after_metering = process.decompressure_mode_after_metering
    transplant_process.metering_para.decompressure_paras[1].pressure = dbToPagePressure(process.decompressure_pressure_after_metering,form_info.transplant_machine.max_set.max_set_metering_pressure,form_info.transplant_machine.max.max_metering_pressure).toFixed(2)
    transplant_process.metering_para.decompressure_paras[1].velocity = volumeToVelocity(process.decompressure_velocity_after_metering, form_info.transplant_machine.transplant_machine_data.screw_diameter,form_info.transplant_machine.max_set.max_set_metering_pressure,form_info.transplant_machine.max.max_metering_pressure).toFixed(2)
    transplant_process.metering_para.decompressure_paras[1].distance = volumeToPosition(process.decompressure_distance_after_metering, form_info.transplant_machine.transplant_machine_data.screw_diameter).toFixed(2)
    // transplant_process.metering_para.decompressure_paras[1].time = process.decompressure_time_after_metering
    return transplant_process
}