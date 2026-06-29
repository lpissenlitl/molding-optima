<template>
  <el-form 
    size="mini" 
    label-width="10rem" 
    label-position="right" 
    :inline="true"
    :model="injector_info"
    ref="injector_info"
  >
    <el-button type="text" @click="drawer = true">
      单位换算
    </el-button>
    <el-drawer
      title="单位换算"
      size="28%"
      driection="rtl"
      :visible.sync="drawer"
      :append-to-body="true"
      :destroy-on-close="true"
    >
      <unit-conversion
        :mac-trademark="mac_trademark"
        :injector-info="injector_info"
      >
      </unit-conversion>
    </el-drawer>

    <el-divider content-position="center"></el-divider>
    <el-tooltip class="item" effect="dark" content="与注塑机建立通讯的关键字,单色默认和设备编码相同,多色必填" placement="top-start">
      <el-form-item 
        label="射台编码" 
        prop="serial_no"
      >
        <el-input v-model="injector_info.serial_no"></el-input>
      </el-form-item>
    </el-tooltip>
    <el-divider content-position="center">
      <span style="color: blue">喷嘴参数</span>
    </el-divider>

    <el-form-item 
      label="喷嘴类别" 
      prop="nozzle_type"
      class="required"
    >
      <el-select v-model="injector_info.nozzle_type">
        <el-option label="直通型" value="直通型"></el-option>
        <el-option label="锁闭型" value="锁闭型"></el-option>
      </el-select>
    </el-form-item>

    <el-form-item 
      label="喷嘴伸出量" 
      prop="nozzle_protrusion"
    >
      <el-input 
        type="number" 
        min="0" 
        v-model="injector_info.nozzle_protrusion"
        @input="injector_info.nozzle_protrusion=checkNumberFormat(injector_info.nozzle_protrusion)"
      >
        <span slot="suffix">mm</span>
      </el-input>
    </el-form-item>

    <el-form-item 
      label="喷嘴孔直径" 
      prop="nozzle_hole_diameter"
    >
      <el-autocomplete 
        v-model.trim="injector_info.nozzle_hole_diameter"
        type="number" 
        :fetch-suggestions="query_nozzle_hole_diameter_options"
        placeholder="请选择"
        :debounce="0"
        @input="injector_info.nozzle_hole_diameter=checkNumberFormat(String(injector_info.nozzle_hole_diameter))"
      >
        <span slot="suffix">mm</span>
      </el-autocomplete>
    </el-form-item>

    <el-form-item 
      label="喷嘴球半径" 
      prop="nozzle_sphere_diameter"
    >
      <el-autocomplete 
        v-model.trim="injector_info.nozzle_sphere_diameter"
        type="number" 
        :fetch-suggestions="query_nozzle_sphere_diameter_options"
        placeholder="请选择"
        :debounce="0"
        @input="injector_info.nozzle_sphere_diameter=checkNumberFormat(String(injector_info.nozzle_sphere_diameter))"
      >
        <span slot="suffix">mm</span>
      </el-autocomplete>
    </el-form-item>
    
    <el-form-item 
      label="喷嘴接触力" 
      prop="nozzle_force"
    >
      <el-input 
        type="number" 
        min="0" 
        v-model="injector_info.nozzle_force"
        @input="injector_info.nozzle_force=checkNumberFormat(injector_info.nozzle_force)"
      >
        <span slot="suffix">KN</span>
      </el-input>
    </el-form-item>
    
    <el-divider content-position="center">
      <span style="color: blue">螺杆、料筒、油缸参数</span>
    </el-divider>

    <el-form-item 
      label="螺杆类别" 
      prop="screw_type"
    >
      <el-select v-model="injector_info.screw_type">
        <el-option label="通用型" value="通用型"></el-option>
        <el-option label="渐变型" value="渐变型"></el-option>
        <el-option label="突变型" value="突变型"></el-option>
      </el-select>
    </el-form-item>
    
    <el-form-item 
      label="螺杆直径" 
      prop="screw_diameter"
      class="required"
    >
      <el-tooltip class="item" effect="dark" :content="'螺杆面积 '+[injector_info.screw_area]+' mm2  螺杆周长 '+[injector_info.screw_circumference]+' mm'" placement="top-start">
        <el-input 
          type="number" 
          min="0" 
          v-model="injector_info.screw_diameter"
          @input="injector_info.screw_diameter=checkNumberFormat(injector_info.screw_diameter, fixed=0)"
        >
          <span slot="suffix">mm</span>
        </el-input>
      </el-tooltip>
    </el-form-item>
    
    <!-- <el-form-item 
      label="螺杆长度" 
      prop="screw_length"
    >
      <el-input 
        type="number" 
        min="0" 
        v-model="injector_info.screw_length"
        @input="injector_info.screw_length=checkNumberFormat(injector_info.screw_length)"
      >
        <span slot="suffix">mm</span>
      </el-input>
    </el-form-item>-->
    
    <el-form-item 
      label="螺杆长径比L/D" 
      prop="screw_length_diameter_ratio"
    >
      <el-input 
        type="number" 
        min="0" 
        v-model="injector_info.screw_length_diameter_ratio"
        @input="injector_info.screw_length_diameter_ratio=checkNumberFormat(injector_info.screw_length_diameter_ratio)"
      >
      </el-input>
    </el-form-item>
    
    <el-form-item 
      label="螺杆压缩比" 
      prop="screw_compression_ratio"
    >
      <el-input 
        type="number" 
        min="0" 
        v-model="injector_info.screw_compression_ratio"
        @input="injector_info.screw_compression_ratio=checkNumberFormat(injector_info.screw_compression_ratio)"
      >
      </el-input>
    </el-form-item>
    
    
    <el-form-item 
      label="塑化能力" 
      prop="plasticizing_capacity"
    >
      <el-input 
        type="number" 
        min="0" 
        v-model="injector_info.plasticizing_capacity"
        @input="injector_info.plasticizing_capacity=checkNumberFormat(injector_info.plasticizing_capacity, fixed=0)"
      >
        <span slot="suffix">Kg/h</span>
      </el-input>
    </el-form-item>    
    
    <el-form-item 
      label="料筒加热功率" 
      prop="barrel_heating_power"
    >
      <el-input 
        type="number" 
        min="0" 
        v-model="injector_info.barrel_heating_power"
        @input="injector_info.barrel_heating_power=checkNumberFormat(injector_info.barrel_heating_power)"
      >
        <span slot="suffix">KW</span>
      </el-input>
    </el-form-item>

    <el-form-item 
      label="最大注射行程" 
      prop="max_injection_stroke"
      class="required"
    >
      <el-input 
        type="number" 
        min="0" 
        v-model="injector_info.max_injection_stroke"
        @input="injector_info.max_injection_stroke=checkNumberFormat(injector_info.max_injection_stroke)"
      >
        <span slot="suffix">mm</span>
      </el-input>
    </el-form-item>

    <el-form-item 
      label="最大注射容积" 
      prop="max_injection_volume"
    >
      <el-input 
        type="number" 
        min="0" 
        v-model="injector_info.max_injection_volume"
        @input="injector_info.max_injection_volume=checkNumberFormat(injector_info.max_injection_volume)"
      >
        <span slot="suffix">cm<sup>3</sup></span>
      </el-input>
    </el-form-item>
    
    <el-form-item 
      label="最大注射重量" 
      prop="max_injection_weight"
    >
      <el-input 
        type="number" 
        min="0" 
        v-model="injector_info.max_injection_weight"
        @input="injector_info.max_injection_weight=checkNumberFormat(injector_info.max_injection_weight)"
      >
        <span slot="suffix">(PS)g</span>
      </el-input>
    </el-form-item>
    
    <!-- <el-form-item 
      label="活塞杆位于注射侧" 
      prop="use_small_size"
    >
      <el-select v-model="injector_info.use_small_size">
        <el-option label="是" :value=1></el-option>
        <el-option label="否" :value=0></el-option>
      </el-select>
    </el-form-item>

    <el-form-item 
      label="活塞杆直径" 
      prop="piston_rod_diameter"
    >
      <el-input 
        type="number" 
        min="0" 
        v-model="injector_info.piston_rod_diameter"
        @input="injector_info.piston_rod_diameter=checkNumberFormat(injector_info.piston_rod_diameter)"
      >
        <span slot="suffix">mm</span>
      </el-input>
    </el-form-item>

    <el-form-item 
      label="油缸数" 
      prop="cylinder_numer"
    >
      <el-input 
        type="number" 
        min="0" 
        v-model="injector_info.cylinder_numer"
      >
      </el-input>
    </el-form-item>

    <el-form-item 
      label="油缸直径" 
      prop="cylinder_diameter"
    >
      <el-tooltip class="item" effect="dark" :content="'油缸面积 '+[injector_info.cylinder_area]+' mm2'" placement="top-start">
        <el-input 
          type="number" 
          min="0" 
          v-model="injector_info.cylinder_diameter"
          @input="injector_info.cylinder_diameter=checkNumberFormat(injector_info.cylinder_diameter)"
        >
          <span slot="suffix">mm</span>
        </el-input>
      </el-tooltip>
    </el-form-item> -->

    <el-divider content-position="center">      
      <span style="color: blue">成型参数</span>     
    </el-divider>
      
    <el-form-item 
      label="最大注射压力" 
      prop="max_injection_pressure"
      class="required"
    >
      <el-tooltip class="item" effect="dark" content="料管" placement="top-start">>
        <el-input 
          type="number" 
          min="0" 
          v-model="injector_info.max_injection_pressure"
          @input="injector_info.max_injection_pressure=checkNumberFormat(injector_info.max_injection_pressure, fixed=2)"
        >
          <span slot="suffix">MPa</span>
        </el-input>
      </el-tooltip>
    </el-form-item>
    
    <el-form-item 
      label="最大注射速度" 
      prop="max_injection_velocity"
      class="required"
    >
      <el-tooltip class="item" effect="dark" :content="'最大注射速率 '+[injector_info.max_injection_rate]+' cm³/s'" placement="top-start">
        <el-input 
          type="number" 
          min="0" 
          v-model="injector_info.max_injection_velocity"
          @input="injector_info.max_injection_velocity=checkNumberFormat(injector_info.max_injection_velocity, fixed=2)"
        >
          <span slot="suffix">mm/s</span>
        </el-input>
      </el-tooltip>
    </el-form-item>
    
    <el-form-item 
      label="最大保压压力" 
      prop="max_holding_pressure"
      class="required"
    >
      <el-input 
        type="number" 
        min="0" 
        v-model="injector_info.max_holding_pressure"
        @input="injector_info.max_holding_pressure=checkNumberFormat(injector_info.max_holding_pressure, fixed=2)"
      >
        <span slot="suffix">MPa</span>
      </el-input>
    </el-form-item>
    
    <el-form-item 
      label="最大保压速度" 
      prop="max_holding_velocity"
      class="required"
    >
      <el-tooltip class="item" effect="dark" :content="'最大保压速率 '+[injector_info.max_holding_rate]+' cm³/s'" placement="top-start">
        <el-input 
          type="number" 
          min="0" 
          v-model="injector_info.max_holding_velocity"
          @input="injector_info.max_holding_velocity=checkNumberFormat(injector_info.max_holding_velocity, fixed=2)"
        >
          <span slot="suffix">mm/s</span>
        </el-input>
      </el-tooltip>
    </el-form-item>
    
    <el-form-item 
      label="最大计量压力" 
      prop="max_metering_pressure"
      v-show="power_method==='液压机'"
      class="required"
    >
      <el-input 
        type="number" 
        min="0" 
        v-model="injector_info.max_metering_pressure"
        @input="injector_info.max_metering_pressure=checkNumberFormat(injector_info.max_metering_pressure, fixed=2)"
      >
        <span slot="suffix">MPa</span>
      </el-input>
    </el-form-item>
    
    <el-form-item 
      label="最大螺杆转速" 
      prop="max_screw_rotation_speed"
      class="required"
    >
      <el-tooltip class="item" effect="dark" :content="'最大螺杆转速线速度 '+[injector_info.max_screw_linear_velocity]+' cm/s'" placement="top-start">
        <el-input 
          type="number" 
          min="0" 
          v-model="injector_info.max_screw_rotation_speed"
          @input="injector_info.max_screw_rotation_speed=checkNumberFormat(injector_info.max_screw_rotation_speed, fixed=2)"
        >
          <span slot="suffix">rpm</span>
        </el-input>
      </el-tooltip>
    </el-form-item>
    
    <el-form-item 
      label="最大计量背压" 
      prop="max_metering_back_pressure"
      class="required"
    >
      <el-input 
        type="number" 
        min="0" 
        v-model="injector_info.max_metering_back_pressure"
        @input="injector_info.max_metering_back_pressure=checkNumberFormat(injector_info.max_metering_back_pressure, fixed=2)"
      >
        <span slot="suffix">MPa</span>
      </el-input>
    </el-form-item>
    
    <el-form-item 
      label="最大松退压力" 
      prop="max_decompression_pressure"
      v-show="power_method==='液压机'"
      class="required"
    >
      <el-input 
        type="number" 
        min="0" 
        v-model="injector_info.max_decompression_pressure"
        @input="injector_info.max_decompression_pressure=checkNumberFormat(injector_info.max_decompression_pressure, fixed=2)"
      >
        <span slot="suffix">MPa</span>
      </el-input>
    </el-form-item>
    
    <el-form-item 
      label="最大松退速度" 
      prop="max_decompression_velocity"
      class="required"
    >
      <el-tooltip class="item" effect="dark" :content="'最大松退速率 '+[injector_info.max_decompression_rate]+' cm³/s'" placement="top-start">
        <el-input 
          type="number" 
          min="0" 
          v-model="injector_info.max_decompression_velocity"
          @input="injector_info.max_decompression_velocity=checkNumberFormat(injector_info.max_decompression_velocity, fixed=2)"
        >
          <span slot="suffix">mm/s</span>
        </el-input>
      </el-tooltip>
    </el-form-item>

    <el-form-item 
      label="最大顶进速度" 
      prop="max_ejector_forward_velocity"
    >
      <el-input 
        type="number" 
        min="0" 
        v-model="injector_info.max_ejector_forward_velocity"
        @input="injector_info.max_ejector_forward_velocity=checkNumberFormat(injector_info.max_ejector_forward_velocity, fixed=2)"
      >
        <span slot="suffix">mm/s</span>
      </el-input>
    </el-form-item>

    <el-form-item 
      label="最大顶退速度" 
      prop="max_ejector_backward_velocity"
    >
      <el-input 
        type="number" 
        min="0" 
        v-model="injector_info.max_ejector_backward_velocity"
        @input="injector_info.max_ejector_backward_velocity=checkNumberFormat(injector_info.max_ejector_backward_velocity, fixed=2)"
      >
        <span slot="suffix">mm/s</span>
      </el-input>
    </el-form-item>

    <el-form-item 
      label="最大开模速度" 
      prop="max_mold_opening_velocity"
    >
      <el-input 
        type="number" 
        min="0" 
        v-model="injector_info.max_mold_opening_velocity"
        @input="injector_info.max_mold_opening_velocity=checkNumberFormat(injector_info.max_mold_opening_velocity, fixed=2)"
      >
        <span slot="suffix">mm/s</span>
      </el-input>
    </el-form-item>

    <el-form-item 
      label="最大合模速度" 
      prop="max_mold_clamping_velocity"
    >
      <el-input 
        type="number" 
        min="0" 
        v-model="injector_info.max_mold_clamping_velocity"
        @input="injector_info.max_mold_clamping_velocity=checkNumberFormat(injector_info.max_mold_clamping_velocity, fixed=2)"
      >
        <span slot="suffix">mm/s</span>
      </el-input>
    </el-form-item>
    
    <el-divider content-position="center">
      <el-tooltip class="item" effect="dark" content="对于液压机,指油压" placement="top-start">
        <span style="color: blue">注塑机界面最大可设定参数</span>
      </el-tooltip>
    </el-divider>
      
    <el-form-item 
      label="最大可设定注射压力" 
      prop="max_set_injection_pressure"
      class="required"
    >
      <el-input 
        :disabled="is_editor"
        type="number" 
        min="0" 
        v-model="injector_info.max_set_injection_pressure"
        @input="injector_info.max_set_injection_pressure=checkNumberFormat(injector_info.max_set_injection_pressure)"
      >
        <span slot="suffix">{{ pressureUnit }}</span>
      </el-input>
    </el-form-item>
    
    <el-form-item 
      label="最大可设定注射速度" 
      prop="max_set_injection_velocity"
      class="required"
    >
      <el-input 
        type="number" 
        min="0" 
        v-model="injector_info.max_set_injection_velocity"
        @input="injector_info.max_set_injection_velocity=checkNumberFormat(injector_info.max_set_injection_velocity)"
      >
        <span slot="suffix">{{ velocityUnit }}</span>
      </el-input>
    </el-form-item>
    
    <el-form-item 
      label="最大可设定保压压力" 
      prop="max_set_holding_pressure"
      class="required"
    >
      <el-input 
        :disabled="is_editor"
        type="number" 
        min="0" 
        v-model="injector_info.max_set_holding_pressure"
        @input="injector_info.max_set_holding_pressure=checkNumberFormat(injector_info.max_set_holding_pressure)"
      >
        <span slot="suffix">{{ pressureUnit }}</span>
      </el-input>
    </el-form-item>
    
    <el-form-item 
      label="最大可设定保压速度" 
      prop="max_set_holding_velocity"
      class="required"
    >
      <el-input 
        type="number" 
        min="0" 
        v-model="injector_info.max_set_holding_velocity"
        @input="injector_info.max_set_holding_velocity=checkNumberFormat(injector_info.max_set_holding_velocity)"
      >
        <span slot="suffix">{{ velocityUnit }}</span>
      </el-input>
    </el-form-item>
    
    <el-form-item 
      label="最大可设定计量压力" 
      prop="max_set_metering_pressure"
      v-show="power_method==='液压机'"
      class="required"
    >
      <el-input 
        :disabled="is_editor"
        type="number" 
        min="0" 
        v-model="injector_info.max_set_metering_pressure"
        @input="injector_info.max_set_metering_pressure=checkNumberFormat(injector_info.max_set_metering_pressure)"
      >
        <span slot="suffix">{{ pressureUnit }}</span>
      </el-input>
    </el-form-item>
    
    <el-form-item 
      label="最大可设定螺杆转速" 
      prop="max_set_screw_rotation_speed"
      class="required"
    >
      <el-input 
        type="number" 
        min="0" 
        v-model="injector_info.max_set_screw_rotation_speed"
        @input="injector_info.max_set_screw_rotation_speed=checkNumberFormat(injector_info.max_set_screw_rotation_speed)"
      >
        <span slot="suffix">{{ rotationUnit }}</span>
      </el-input>
    </el-form-item>
    
    <el-form-item 
      label="最大可设定计量背压" 
      prop="max_set_metering_back_pressure"
      class="required"
    >
      <el-input 
        :disabled="is_editor"
        type="number" 
        min="0" 
        v-model="injector_info.max_set_metering_back_pressure"
        @input="injector_info.max_set_metering_back_pressure=checkNumberFormat(injector_info.max_set_metering_back_pressure)"
      >
        <span slot="suffix">{{ backpressureUnit }}</span>
      </el-input>
    </el-form-item>
    
    <el-form-item 
      label="最大可设定松退压力" 
      prop="max_set_decompression_pressure"
      v-show="power_method==='液压机'"
      class="required"
    >
      <el-input 
        :disabled="is_editor"
        type="number" 
        min="0" 
        v-model="injector_info.max_set_decompression_pressure"
        @input="injector_info.max_set_decompression_pressure=checkNumberFormat(injector_info.max_set_decompression_pressure)"
      >
        <span slot="suffix">{{ pressureUnit }}</span>
      </el-input>
    </el-form-item>
    
    <el-form-item 
      label="最大可设定松退速度" 
      prop="max_set_decompression_velocity"
      class="required"
    >
      <el-input 
        type="number" 
        min="0" 
        v-model="injector_info.max_set_decompression_velocity"
        @input="injector_info.max_set_decompression_velocity=checkNumberFormat(injector_info.max_set_decompression_velocity)"
      >
        <span slot="suffix">{{ velocityUnit }}</span>
      </el-input>
    </el-form-item>

    <el-form-item 
      label="最大可设定顶进速度" 
      prop="max_set_ejector_forward_velocity"
    >
      <el-input 
        type="number" 
        min="0" 
        v-model="injector_info.max_set_ejector_forward_velocity"
        @input="injector_info.max_set_ejector_forward_velocity=checkNumberFormat(injector_info.max_set_ejector_forward_velocity)"
      >
        <span slot="suffix">{{ ocvelocityUnit }}</span>
      </el-input>
    </el-form-item>

    <el-form-item 
      label="最大可设定顶退速度" 
      prop="max_set_ejector_backward_velocity"
    >
      <el-input 
        type="number" 
        min="0" 
        v-model="injector_info.max_set_ejector_backward_velocity"
        @input="injector_info.max_set_ejector_backward_velocity=checkNumberFormat(injector_info.max_set_ejector_backward_velocity)"
      >
        <span slot="suffix">{{ ocvelocityUnit }}</span>
      </el-input>
    </el-form-item>

    <el-form-item 
      label="最大可设定开模速度" 
      prop="max_set_mold_opening_velocity"
    >
      <el-input 
        type="number" 
        min="0" 
        v-model="injector_info.max_set_mold_opening_velocity"
        @input="injector_info.max_set_mold_opening_velocity=checkNumberFormat(injector_info.max_set_mold_opening_velocity)"
      >
        <span slot="suffix">{{ ocvelocityUnit }}</span>
      </el-input>
    </el-form-item>

    <el-form-item 
      label="最大可设定合模速度" 
      prop="max_set_mold_clamping_velocity"
    >
      <el-input 
        type="number" 
        min="0" 
        v-model="injector_info.max_set_mold_clamping_velocity"
        @input="injector_info.max_set_mold_clamping_velocity=checkNumberFormat(injector_info.max_set_mold_clamping_velocity)"
      >
        <span slot="suffix">{{ ocvelocityUnit }}</span>
      </el-input>
    </el-form-item>

    <el-divider content-position="center">
      <span style="color: blue">注塑机最大可设定段数</span>
    </el-divider>

    <el-form-item 
      label="注射段数" 
      prop="max_injection_stage"
    >
      <el-input 
        type="number" 
        min="0" 
        v-model="injector_info.max_injection_stage"
        @input="injector_info.max_injection_stage=checkNumberFormat(injector_info.max_injection_stage, fixed=0)"
      >
        <span slot="suffix">段</span>
      </el-input>
    </el-form-item>

    <el-form-item 
      label="保压段数" 
      prop="max_holding_stage"
    >
      <el-input 
        type="number" 
        min="0" 
        v-model="injector_info.max_holding_stage"
        @input="injector_info.max_holding_stage=checkNumberFormat(injector_info.max_holding_stage, fixed=0)"
      >
        <span slot="suffix">段</span>
      </el-input>
    </el-form-item>

    <el-form-item 
      label="计量段数" 
      prop="max_metering_stage"
    >
      <el-input 
        type="number" 
        min="0" 
        v-model="injector_info.max_metering_stage"
        @input="injector_info.max_metering_stage=checkNumberFormat(injector_info.max_metering_stage, fixed=0)"
      >
        <span slot="suffix">段</span>
      </el-input>
    </el-form-item>

    <el-form-item 
      label="料筒加热段数" 
      prop="max_temperature_stage"
    >
      <el-input
        type="number" 
        min="0" 
        v-model="injector_info.max_temperature_stage"
        @input="injector_info.max_temperature_stage=checkNumberFormat(injector_info.max_temperature_stage, fixed=0)"
      >
        <span slot="suffix">段</span>
      </el-input>
    </el-form-item>

    <el-form-item 
      label="开合模设定段数" 
      prop="max_opening_and_clamping_stage"
    >
      <el-input
        type="number" 
        min="0" 
        v-model="injector_info.max_opening_and_clamping_stage"
        @input="injector_info.max_opening_and_clamping_stage=checkNumberFormat(injector_info.max_opening_and_clamping_stage, fixed=0)"
      >
        <span slot="suffix">段</span>
      </el-input>
    </el-form-item>

    <el-form-item 
      label="顶针设定段数" 
      prop="max_ejector_stage"
    >
      <el-input
        type="number" 
        min="0" 
        v-model="injector_info.max_ejector_stage"
        @input="injector_info.max_ejector_stage=checkNumberFormat(injector_info.max_ejector_stage, fixed=0)"
      >
        <span slot="suffix">段</span>
      </el-input>
    </el-form-item>
  </el-form>
</template>

<script>
import { nozzleHoleDiameterOptions, nozzleSphereDiameterOptions } from "@/utils/machine-const";
import * as unit_change from "@/utils/unit-change";
import UnitConversion from "./unitConversion.vue";

export default {
  name: "MacInjectPart",
  components: { UnitConversion },
  props: {
    pressureUnit: {
      type: String,
      default: "MPa"
    },
    velocityUnit: {
      type: String,
      default: "mm/s"
    },
    ocpressureUnit: {
      type: String,
      default: "MPa"
    },
    ocvelocityUnit: {
      type: String,
      default: "mm/s"
    },
    rotationUnit: {
      type: String,
      default: "rpm"
    },
    backpressureUnit:{
      type: String,
      default: "MPa"
    },
    injectorInfo: {
      type: Object,
      default:() => ({
        id: null,
        nozzle_type: null,
        nozzle_protrusion: null,
        nozzle_hole_diameter: null,
        nozzle_sphere_diameter: null,
        nozzle_force: null,

        screw_type: null,
        screw_diameter: null,
        screw_length: null,
        screw_length_diameter_ratio: null,
        screw_compression_ratio: null,
        plasticizing_capacity: null,
        // barrel_heating_sections: null,
        barrel_heating_power: null,
        max_injection_volume: null,
        max_injection_weight: null,
        max_injection_stroke: null,

        cylinder_numer:null,
        cylinder_diameter: null,
        use_small_size: null,
        piston_rod_diameter: null,
        cylinder_area: null,
        intensification_ratio: null,

        max_injection_pressure: null,
        max_injection_velocity: null,
        max_holding_pressure: null,
        max_holding_velocity: null,
        max_metering_pressure: null,
        max_screw_rotation_speed: null,
        max_metering_back_pressure: null,
        max_decompression_pressure: null,
        max_decompression_velocity: null,
        max_injection_rate: null,
        max_holding_rate: null,
        max_decompression_rate: null,
        max_screw_linear_velocity: null,
        screw_area: null,
        screw_circumference: null,

        max_ejector_forward_velocity: null,
        max_ejector_backward_velocity: null,
        max_mold_opening_velocity: null,
        max_mold_clamping_velocity: null,

        max_set_ejector_forward_velocity: null,
        max_set_ejector_backward_velocity: null,
        max_set_mold_opening_velocity: null,
        max_set_mold_clamping_velocity: null,
        max_set_injection_pressure: null,
        max_set_injection_velocity: null,
        max_set_holding_pressure: null,
        max_set_holding_velocity: null,
        max_set_metering_pressure: null,
        max_set_screw_rotation_speed: null,
        max_set_metering_back_pressure: null,
        max_set_decompression_pressure: null,
        max_set_decompression_velocity: null,
      })
    },
    macTrademark: null,
    powerMethod: null,
  },
  data() {
    return {
      injector_info: this.injectorInfo,
      NozzleHoleDiaOptions: nozzleHoleDiameterOptions,
      NozzleSpDiaOptions: nozzleSphereDiameterOptions,
      rules: {
        nozzle_type: [
          { required: true, message: '喷嘴类别为空!' }
        ],
        screw_diameter: [
          { required: true, message: '螺杆直径为空!' }
        ],
        max_injection_stroke:[
          { required: true, message: '最大注射行程为空!' }
        ],
        max_injection_pressure: [
          { required: true, message: '最大注射压力为空!' }
        ],
        max_injection_velocity: [
          { required: true, message: '最大注射速度为空!' }
        ],
        max_holding_pressure: [
          { required: true, message: '最大保压压力为空!' }
        ],
        max_holding_velocity: [
          { required: true, message: '最大保压速度为空!' }
        ],
        max_screw_rotation_speed: [
          { required: true, message: '最大螺杆转速为空!' }
        ],
        // 全电机没有计量压力
        max_metering_pressure:[
          { required: true, message: '最大计量压力为空!' }
        ],
        max_metering_back_pressure: [
          { required: true, message: '最大计量背压为空!' }
        ],
        max_decompression_velocity: [
          { required: true, message: '最大射退速度为空!' }
        ],
        // 全电机没有松退压力
        max_decompression_pressure:[
          { required: true, message: '最大松退压力为空!' }
        ],

        max_set_injection_pressure: [
          { required: true, message: '最大可设定注射压力为空!' }
        ],
        max_set_injection_velocity: [
          { required: true, message: '最大可设定注射速度为空!' }
        ],
        max_set_holding_pressure: [
          { required: true, message: '最大可设定保压压力为空!' }
        ],
        max_set_holding_velocity: [
          { required: true, message: '最大可设定保压速度为空!' }
        ],
        max_set_screw_rotation_speed: [
          { required: true, message: '最大可设定螺杆转速为空!' }
        ],
        max_set_metering_back_pressure: [
          { required: true, message: '最大可设定计量背压为空!' }
        ],
        max_set_decompression_velocity: [
          { required: true, message: '最大可设定松退速度为空!' }
        ],
        // 全电机没有计量压力
        max_set_metering_pressure:[
          { required: true, message: '最大可设定计量压力为空!' }
        ],
        // 全电机没有松退压力
        max_set_decompression_pressure:[
          { required: true, message: '最大可设定松退压力为空!' }
        ], 
        max_injection_stage: [
          { required: true, message: '注射段数为空!' }
        ],
        max_holding_stage: [
          { required: true, message: '保压段数为空!' }
        ],
        max_metering_stage: [
          { required: true, message: '计量段数为空!' }
        ],
        max_temperature_stage: [
          { required: true, message: '料筒加热段数为空!' }
        ],   
      },
      drawer: false,
      mac_trademark: this.macTrademark,
      power_method: this.powerMethod,
      is_editor: false,
    }
  },
  mounted() {
    // this.get_pressure_coefficient()
  },
  methods: {
    query_nozzle_hole_diameter_options(str, cb) {
      cb(this.NozzleHoleDiaOptions)
    },
    query_nozzle_sphere_diameter_options(str, cb) {
      cb(this.NozzleSpDiaOptions)
    },
    // 获得MPa和bar转换的压力系数
    // 如果是电动机,系数是10
    // 如果是液压机,检查是否能计算油缸单位,如果能计算,则返回压力系数,如果不能计算,提示没有油缸面积,需要手动填写
    // get_pressure_coefficient(){
    //   // 不管是电动机还是液压机,都可以计算油缸面积
    //   if(this.injector_info.cylinder_numer && this.injector_info.cylinder_diameter && this.injector_info.piston_rod_diameter && this.injector_info.use_small_size){
    //     this.injector_info.cylinder_area = unit_change.getCylinderArea(this.injector_info)
    //   }
    //   if (this.power_method == "电动机") {
    //     this.injector_info.pressure_coefficient = 10
    //   } else if (this.power_method == "液压机"){
    //     if(this.injector_info.cylinder_numer && this.injector_info.cylinder_diameter && this.injector_info.piston_rod_diameter && this.injector_info.use_small_size){
    //       this.injector_info.pressure_coefficient = unit_change.getPressureCoefficient(this.injector_info)
    //     }
    //   }
    // }
  },
  watch: {
    injectorInfo: function () {
      this.injector_info = this.injectorInfo
    },
    macTrademark() {
      this.mac_trademark = this.macTrademark;
    },
    powerMethod: {
      handler() {
        this.power_method = this.powerMethod
      },
      immediate: true
    },  
    // powerMethod: {
    //   handler() {
    //     this.power_method = this.powerMethod
    //     if (this.power_method == "电动机") {
    //       this.is_editor = true
    //     } else if (this.power_method == "液压机" && this.pressureUnit == "MPa"){
    //       this.is_editor = true
    //     } else {
    //       this.is_editor = false
    //     }
    //     动力方式改变后,自动计算油缸面积和压力系数
    //     this.get_pressure_coefficient()
    //   },
    //   immediate: true
    // },
    // pressureUnit() {
    //   if ((this.pressureUnit == "MPa" && this.power_method == "液压机") || this.power_method == "电动机") {
    //     this.is_editor = true
    //   } else {
    //     this.is_editor = false
    //   }
    // },
    // 油缸直径
    // "injector_info.cylinder_diameter":{
    //   handler: function() {
    //     this.get_pressure_coefficient()
    //   },
    //   deep: true,
    // },
    // 注射压力
    // "injector_info.max_injection_pressure": {
    //   handler: function() {
    //     // 判断是否有压力系数,如果有,自动换算.如果没有,则空着,让用户自己填写
    //       if(this.pressureUnit === "%"){
    //         this.injector_info.max_set_injection_pressure = 100
    //       } else {
    //         this.injector_info.max_set_injection_pressure = unit_change.conversion("MPa", this.pressureUnit, this.injector_info.max_injection_pressure, this.injector_info)
    //       }
    //   },
    //   deep: true,
    // },
    // 保压压力
    // "injector_info.max_holding_pressure": {
    //   handler: function() {
    //       if(this.pressureUnit === "%"){
    //         this.injector_info.max_set_holding_pressure = 100
    //       } else {
    //         this.injector_info.max_set_holding_pressure = unit_change.conversion("MPa", this.pressureUnit, this.injector_info.max_holding_pressure, this.injector_info)
    //       }
    //   },
    //   deep: true,
    // },
    // 计量压力
    //  "injector_info.max_metering_pressure": {
    //   handler: function() {
    //       if(this.pressureUnit === "%"){
    //         this.injector_info.max_set_metering_pressure = 100
    //       } else {
    //         this.injector_info.max_set_metering_pressure = unit_change.conversion("MPa", this.pressureUnit, this.injector_info.max_metering_pressure, this.injector_info)
    //       }
    //   },
    //   deep: true,
    // },
    // 松退压力
    // "injector_info.max_decompression_pressure": {
    //   handler: function() {
    //       if(this.pressureUnit === "%"){
    //         this.injector_info.max_set_decompression_pressure = 100
    //       } else { 
    //         this.injector_info.max_set_decompression_pressure = unit_change.conversion("MPa", this.pressureUnit, this.injector_info.max_decompression_pressure, this.injector_info)
    //       }
    //   },
    //   deep: true,
    // },
    // 背压
    // "injector_info.max_metering_back_pressure": {
    //   handler: function() {
    //       if(this.pressureUnit === "%"){
    //         this.injector_info.max_set_metering_back_pressure = 100
    //       } else { 
    //         this.injector_info.max_set_metering_back_pressure = unit_change.conversion("MPa", this.backpressureUnit, this.injector_info.max_metering_back_pressure, this.injector_info)
    //       }
    //   },
    //   deep: true,
    // },
    // 注射速度
    // "injector_info.max_injection_velocity": {
    //   handler: function() {
    //     // 计算最大注射速率
    //     this.injector_info.max_injection_rate = unit_change.conversion("mm/s", "cm³/s", this.injector_info.max_injection_velocity, this.injector_info)
    //       if(this.velocityUnit === "%"){
    //         this.injector_info.max_set_injection_velocity = 100
    //       }
    //       else{
    //         this.injector_info.max_set_injection_velocity = unit_change.conversion("mm/s", this.velocityUnit, this.injector_info.max_injection_velocity, this.injector_info)
    //       }
    //   },
    //   deep: true,
    // },
    // // 保压速度
    // "injector_info.max_holding_velocity": {
    //   handler: function() {
    //     // 最大保压速率
    //     this.injector_info.max_holding_rate = unit_change.conversion("mm/s", "cm³/s", this.injector_info.max_holding_velocity, this.injector_info)
    //       if(this.velocityUnit === "%"){
    //         this.injector_info.max_set_holding_velocity = 100
    //       } else {
    //       this.injector_info.max_set_holding_velocity = unit_change.conversion("mm/s", this.velocityUnit, this.injector_info.max_holding_velocity, this.injector_info)
    //       }
    //   },
    //   deep: true,
    // },
    // 松退速度:只有长度相关的单位,没有体积相关的单位
    // "injector_info.max_decompression_velocity": {
    //   handler: function() {
    //     //最大松退速率
    //     this.injector_info.max_decompression_rate = unit_change.conversion("mm/s", "cm³/s", this.injector_info.max_decompression_velocity, this.injector_info)
    //       if(this.velocityUnit === "%"){
    //         this.injector_info.max_set_decompression_velocity = 100
    //       } else {
    //       this.injector_info.max_set_decompression_velocity = unit_change.conversion("mm/s", this.velocityUnit, this.injector_info.max_decompression_velocity, this.injector_info)
    //       }
    //   },
    //   deep: true,
    // },
    // // 螺杆转速
    // "injector_info.max_screw_rotation_speed": {
    //   handler: function() {
    //     //计算线速度
    //     this.injector_info.max_screw_linear_velocity = unit_change.conversion("rpm", "cm/s", this.injector_info.max_screw_rotation_speed, this.injector_info)
    //       if(this.rotationUnit === "%"){
    //         this.injector_info.max_set_screw_rotation_speed = 100
    //       } else {
    //         this.injector_info.max_set_screw_rotation_speed = unit_change.conversion("rpm", this.rotationUnit, this.injector_info.max_screw_rotation_speed, this.injector_info)
    //       }
    //   },
    //   deep: true,
    // },
    // // 顶进速度
    // "injector_info.max_ejector_forward_velocity": {
    //   handler: function() {
    //       if(this.ocvelocityUnit === "%"){
    //         this.injector_info.max_set_ejector_forward_velocity = 100
    //       } else {
    //         this.injector_info.max_set_ejector_forward_velocity = unit_change.conversion("mm/s", this.ocvelocityUnit, this.injector_info.max_ejector_forward_velocity, this.injector_info)
    //       }
    //   },
    //   deep: true,
    // },
    // // 顶退速度
    // "injector_info.max_ejector_backward_velocity": {
    //   handler: function() {
    //       if(this.ocvelocityUnit === "%"){
    //         this.injector_info.max_set_ejector_backward_velocity = 100
    //       } else {
    //         this.injector_info.max_set_ejector_backward_velocity = unit_change.conversion("mm/s", this.ocvelocityUnit, this.injector_info.max_ejector_backward_velocity, this.injector_info)
    //       }
    //   },
    //   deep: true,
    // },
    // // 开模速度
    // "injector_info.max_mold_opening_velocity": {
    //   handler: function() {
    //       if(this.ocvelocityUnit === "%"){
    //         this.injector_info.max_set_mold_opening_velocity = 100
    //       } else {
    //         this.injector_info.max_set_mold_opening_velocity = unit_change.conversion("mm/s", this.ocvelocityUnit, this.injector_info.max_mold_opening_velocity, this.injector_info)
    //       }
    //   },
    //   deep: true,
    // },
    // // 合模速度
    // "injector_info.max_mold_clamping_velocity": {
    //   handler: function() {
    //       if(this.ocvelocityUnit === "%"){
    //         this.injector_info.max_set_mold_clamping_velocity = 100
    //       } else {
    //         this.injector_info.max_set_mold_clamping_velocity = unit_change.conversion("mm/s", this.ocvelocityUnit, this.injector_info.max_mold_clamping_velocity, this.injector_info)
    //       }
    //   },
    //   deep: true,
    // },
    // 螺杆直径
    "injector_info.screw_diameter":{
      handler: function() {
        this.injector_info.screw_area = unit_change.getScrewArea(this.injector_info).toFixed(2)
        this.injector_info.screw_circumference = unit_change.getScrewCircumference(this.injector_info).toFixed(2)
        
        // 用螺杆直径和最大注射行程,计算最大注射容积和最大注射重量
        // this.injector_info.max_injection_volume = (this.injector_info.screw_area*this.injector_info.max_injection_stroke/1000).toFixed(2)
        // this.injector_info.max_injection_weight = (this.injector_info.max_injection_volume*0.945).toFixed(2)
      },
      deep: true,
    },
    // 用螺杆直径和最大注射行程,计算最大注射容积和最大注射重量
    "injector_info.max_injection_stroke":{
      handler: function() {
        if(this.injector_info.max_injection_stroke){
          // this.injector_info.max_injection_volume = (this.injector_info.screw_area*this.injector_info.max_injection_stroke/1000).toFixed(2)
          // this.injector_info.max_injection_weight = (this.injector_info.max_injection_volume*0.945).toFixed(2)
        }
      },
      deep: true,
    }
  }
}
</script>

<style lang="scss" scoped>
  .el-input {
    width: 10rem;
  }
  .el-select {
    width: 10rem;
  }
  .el-autocomplete {
    width: 10rem;
  }
  .required ::v-deep .el-form-item__label::before {
    content: '*';
    color: #ff4949;
    margin-right: 4px;
  }
</style>

