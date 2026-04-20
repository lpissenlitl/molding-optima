<template>
  <div>
    <el-form
      ref="mold_info" 
      label-width="8rem"
      size="mini"
      :model="detail_info" 
      :inline="true" 
      :rules="rules"
    >
      <el-card class="box-card">
        <div slot="header" class="clearfix">
          <span>基本信息</span>
        </div>

        <el-form-item 
          label="模具编号"
          prop="mold_no"
        >
          <el-input v-model.trim="detail_info.mold_no"></el-input>
        </el-form-item>

        <el-form-item 
          label="模具类别"
          prop="mold_type"
        >
          <el-select v-model="detail_info.mold_type">
            <el-option 
              v-for="option, index in mold_type_options"
              :key="index"
              :label="option.label"
              :value="option.value"
            >
            </el-option>
          </el-select>
        </el-form-item>

        <el-form-item 
          label="模具名称"
          prop="mold_name"
        >
          <el-input v-model.trim="detail_info.mold_name"></el-input>
        </el-form-item>

        <el-form-item 
          label="型腔数"
          prop="cavity_num"
        >
          <el-tooltip class="item" effect="dark" content="请输入正确格式,如(1、1+1、1*2)" placement="top-start">
            <el-input v-model="detail_info.cavity_num"></el-input>
          </el-tooltip>
        </el-form-item>

        <el-form-item 
          label="注塑周期要求"
          prop="inject_cycle_require"
        >
          <el-input 
            v-model.trim="detail_info.inject_cycle_require"
            type="number" 
            @input="detail_info.inject_cycle_require=checkNumberFormat(detail_info.inject_cycle_require)"
          >
            <span slot="suffix">s</span>
          </el-input>
        </el-form-item>
        <el-form-item 
          label="绑定规则库" 
          prop="subrule_no"
        >
          <el-autocomplete 
            v-model="detail_info.subrule_no"
            :fetch-suggestions="querySubRuleNoList"
            placeholder="请输入内容"
            clearable
            :debounce="0"
          >
          </el-autocomplete>
        </el-form-item>
      </el-card>

      <div style="height: 4px"></div>

      <el-card class="box-card">
        <div slot="header" class="clearfix">
          <span>制品信息</span>
        </div>

        <el-form-item
          label="制品大类"
          prop="product_category"
        >
          <el-select 
            allow-create
            clearable
            filterable
            v-model="detail_info.product_category"
          >
            <el-option 
              v-for="option, index in product_category_options"
              :key="index"
              :label="option.label"
              :value="option.value"
            >
            </el-option>
          </el-select>
        </el-form-item>

        <el-form-item
          label="制品中类"
          prop="product_type"
        >
          <el-select
            allow-create
            clearable
            filterable
            v-model="detail_info.product_type"
          >
            <el-option
              v-for="option, index in product_type_options"
              :key="index"
              :label="option.label"
              :value="option.value"
            >
            </el-option>
          </el-select>

        </el-form-item>
        <el-form-item
          label="制品类别"
          prop="product_small_type"
        >
          <el-select
            allow-create
            clearable
            filterable
            v-model="detail_info.product_small_type"
          >
            <el-option
              v-for="option, index in product_small_type_options"
              :key="index"
              :label="option.label"
              :value="option.value"
            >
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item
          label="制品名称"
          prop="product_name"
        >
          <el-input v-model.trim="detail_info.product_name"></el-input>
        </el-form-item>

        <el-form-item
          label="制品编号"
          prop="product_no"
        >
          <el-input v-model.trim="detail_info.product_no"></el-input>
        </el-form-item>
        <el-tooltip class="item" effect="dark" content="各型腔产品总重，不包含冷流道重量" placement="top-start">
          <el-form-item
            label="总重量"
            prop="product_total_weight"
          >
            <el-input 
              v-model.trim="detail_info.product_total_weight"
              type="number" 
              @input="detail_info.product_total_weight=checkNumberFormat(detail_info.product_total_weight)"
            >
              <span slot="suffix">g</span>
            </el-input>
          </el-form-item>
        </el-tooltip>
        <el-form-item
          label="总投射面积"
          prop="product_projected_area"
        >
          <el-input 
            v-model.trim="detail_info.product_projected_area"
            type="number" 
            @input="detail_info.product_projected_area=checkNumberFormat(detail_info.product_projected_area)"
          >
            <span slot="suffix">cm<sup>2</sup></span>
          </el-input>
        </el-form-item>

        <div 
          v-for="product_info, index in detail_info.product_infos"
          :key="index"
        >
          <el-divider content-position="center">
            <span style="color:blue">{{ (index + 1) + "射制品信息 " }}</span>
          </el-divider>
          <el-tooltip class="item" effect="dark" content="从浇口处到产品最远端的流动距离" placement="top-start">
            <el-form-item
              label="制品流长"
              :prop="'product_infos.' + index + '.flow_length'"
              :rules="rules.flow_length"
            >
              <el-input 
                v-model.trim="product_info.flow_length"
                type="number" 
                @input="product_info.flow_length=checkNumberFormat(product_info.flow_length)"
              >
                <span slot="suffix">mm</span>
              </el-input>
            </el-form-item>
          </el-tooltip>
          <el-form-item
            label="最大壁厚"
            :prop="'product_infos.' + index + '.max_thickness'"
            :rules="rules.max_thickness"
          >
            <el-input 
              v-model.trim="product_info.max_thickness"
              type="number" 
              @input="product_info.max_thickness=checkNumberFormat(product_info.max_thickness)"
            >
              <span slot="suffix">mm</span>
            </el-input>
          </el-form-item>

          <el-form-item
            label="平均壁厚"
            :prop="'product_infos.' + index + '.ave_thickness'"
            :rules="rules.ave_thickness"
          >
            <el-input 
              v-model.trim="product_info.ave_thickness"
              type="number" 
              @input="product_info.ave_thickness=checkNumberFormat(product_info.ave_thickness)"
            >
              <span slot="suffix">mm</span>
            </el-input>
          </el-form-item>

          <el-form-item
            label="单件体积"
            prop="single_volume"
          >
            <el-input 
              v-model.trim="product_info.single_volume"
              type="number" 
              @input="product_info.single_volume=checkNumberFormat(product_info.single_volume)"
            >
              <span slot="suffix">cm<sup>3</sup></span>
            </el-input>
          </el-form-item>

          <el-form-item
            label="单件重量"
            prop="single_weight"
          >
            <el-input 
              v-model.trim="product_info.single_weight"
              type="number" 
              @input="product_info.single_weight=checkNumberFormat(product_info.single_weight)"
            >
              <span slot="suffix">g</span>
            </el-input>
          </el-form-item>
        </div>
      </el-card>

      <div style="height: 4px"></div>

      <el-card class="box-card">
        <div slot="header" class="clearfix">
          <span>浇注系统</span>
        </div>

        <div 
          v-for="product_info, index in detail_info.product_infos"
          :key="index"
        >
          <el-divider content-position="center">
            <span style="color:blue">{{ (index + 1) + "射浇注系统 " }}</span>
          </el-divider>

          <el-form-item 
            label="喷嘴孔直径"
            prop="sprue_hole_diameter"
          >
            <div style="display: flex; align-items: center;">
              <el-select
                v-model.trim="product_info.sprue_hole_diameter"
                placeholder="请选择"
                @change="(value) => product_info.sprue_hole_diameter = checkNumberFormat(value)"
                clearable
                filterable
                style="flex: 1;"
              >
                <el-option
                  v-for="option in sprue_hole_diameter_options"
                  :key="option.value"
                  :label="option.label"
                  :value="option.value"
                />
              </el-select>
              <span class='unit-suffix'
                    style="margin-left: -1px; padding: 0 10px; height: 40px; line-height: 40px; font-size:12px">
                mm
              </span>
            </div>
          </el-form-item>

          <el-form-item
            label="喷嘴球半径"
            prop="sprue_sphere_radius"
          >
            <div style="display: flex; align-items: center;">
              <el-select
                v-model.trim="product_info.sprue_sphere_radius"
                placeholder="请选择"
                @change="(value) => product_info.sprue_sphere_radius = checkNumberFormat(value)"
                clearable
                filterable
                style="flex: 1;"
              >
                <el-option
                  v-for="option in sprue_sphere_radius_options"
                  :key="option.value"
                  :label="option.label"
                  :value="option.value"
                />
              </el-select>
              <span class="unit-suffix"
                    style="margin-left: -1px; padding: 0 10px; height: 40px; line-height: 40px; font-size:12px">
                mm
              </span>
            </div>
          </el-form-item>

          <el-form-item 
            label="流道类别"
            :prop="'product_infos.' + index + '.runner_type'"
            :rules="rules.runner_type"
          >
            <el-select 
              v-model="product_info.runner_type"
              clearable
              filterable 
              allow-create
              default-first-option
              @change="changeRunnerType"
            >
              <el-option label="热流道" value="热流道"></el-option>
              <el-option label="冷流道" value="冷流道"></el-option>
              <el-option label="热转冷" value="热转冷"></el-option>
            </el-select>
          </el-form-item>

          <el-form-item 
            label="热流道段数"             
            :prop="'product_infos.' + index + '.hot_runner_num'"
            :rules="rules.hot_runner_num" 
            v-if="product_info.runner_type=='热流道'"
          >
            <el-select filterable allow-create v-model="product_info.hot_runner_num">
              <el-option
                v-for="(option, index) in 36"
                :key="index"
                :label="option"
                :value="option"
              >
              </el-option>
            </el-select>
          </el-form-item>

          <el-form-item
            label="阀口数量"
            prop="valve_num"
          >
            <el-input 
              v-model.trim="product_info.valve_num"
              type="number" 
              @input="product_info.valve_num=checkNumberFormat(product_info.valve_num, 0)"
              :disabled="product_info.runner_type !== '热流道'"
            >
            </el-input>
          </el-form-item>

          <el-form-item
            label="流道长度"
            :prop="'product_infos.' + index + '.runner_length'"
            :rules="rules.runner_length"
          >
            <el-input 
              v-model.trim="product_info.runner_length"
              type="number" 
              @input="product_info.runner_length=checkNumberFormat(product_info.runner_length)"
            >
              <span slot="suffix">mm</span>
            </el-input>
          </el-form-item>
          <el-tooltip class="item" effect="dark" content="各型腔所有冷流道的总重量" placement="top-start">
            <el-form-item
              label="流道重量"
              :prop="'product_infos.' + index + '.runner_weight'"
              :rules="rules.runner_weight"
            >
              <el-input 
                v-model.trim="product_info.runner_weight"
                type="number" 
                @input="product_info.runner_weight=checkNumberFormat(product_info.runner_weight)"
              >
                <span slot="suffix">g</span>
              </el-input>
            </el-form-item>
          </el-tooltip>
          <el-form-item 
            label="浇口类别"
            :prop="'product_infos.' + index + '.gate_type'"
            :rules="rules.gate_type"
          >
            <el-select 
              v-model="product_info.gate_type"
              clearable
              filterable 
              allow-create
              default-first-option
            >
              <el-option 
                v-for="item in gate_type_options"
                :key="item.value" 
                :label="item.label" 
                :value="item.value"
              ></el-option>
            </el-select>
          </el-form-item>

          <el-form-item
            label="浇口数量"
            :prop="'product_infos.' + index + '.gate_num'"
            :rules="rules.gate_num"
          >
            <el-input 
              v-model.trim="product_info.gate_num"
              type="number" 
              @input="product_info.gate_num=checkNumberFormat(product_info.gate_num, 0)"
            >
              <span slot="suffix">个</span>
            </el-input>
          </el-form-item>
          <el-form-item
            label="浇口形状"
            :prop="'product_infos.' + index + '.gate_shape'"
            :rules="rules.gate_shape"
          >
            <el-select v-model.trim="product_info.gate_shape">
              <el-option label="圆形" value="圆形"></el-option>
              <el-option label="矩形" value="矩形"></el-option>
            </el-select>
          </el-form-item>
          
          <el-form-item
            label="浇口横截面积"
            prop="gate_area"
          >
            <el-input 
              v-model.trim="product_info.gate_area"
              type="number" 
              @input="product_info.gate_area=checkNumberFormat(product_info.gate_area)"
            >
              <span slot="suffix">cm<sup>2</sup></span>
            </el-input>
          </el-form-item>

          <el-form-item
            v-if="product_info.gate_shape === '圆形'"
            label="浇口半径(圆)"
            :prop="'product_infos.' + index + '.gate_radius'"
            :rules="rules.gate_radius"
          >
            <el-input 
              v-model.trim="product_info.gate_radius"
              type="number" 
              @input="product_info.gate_radius=checkNumberFormat(product_info.gate_radius)"
            >
              <span slot="suffix">mm</span>
            </el-input>
          </el-form-item>

          <el-form-item
            v-if="product_info.gate_shape === '矩形'"
            label="浇口长(矩形)"
            :prop="'product_infos.' + index + '.gate_length'"
            :rules="rules.gate_length"
          >
            <el-input 
              v-model.trim="product_info.gate_length"
              type="number" 
              @input="product_info.gate_length=checkNumberFormat(product_info.gate_length)"
            >
              <span slot="suffix">mm</span>
            </el-input>
          </el-form-item>

          <el-form-item
            v-if="product_info.gate_shape === '矩形'"
            label="浇口宽(矩形)"
            :prop="'product_infos.' + index + '.gate_width'"
            :rules="rules.gate_width"
          >
            <el-input 
              v-model.trim="product_info.gate_width"
              type="number" 
              @input="product_info.gate_width=checkNumberFormat(product_info.gate_width)"
            >
              <span slot="suffix">mm</span>
            </el-input>
          </el-form-item>
        </div>
      </el-card>

      <div style="height: 4px"></div>

      <el-card class="box-card">
        <div slot="header" class="clearfix">
          <span>冷却系统</span>
        </div>

        <el-divider content-position="center">
          <span style="color:blue">前模（定模、型腔、母模）</span>
        </el-divider>

        <el-form-item
          label="冷却回路组数"
          prop="cavity_cooling_circuit_number"
        >
          <el-input 
            v-model.trim="detail_info.cavity_cooling_circuit_number"
            type="number" 
            @input="detail_info.cavity_cooling_circuit_number=checkNumberFormat(detail_info.cavity_cooling_circuit_number, 0)"
          >
            <span slot="suffix">组</span>
          </el-input>
        </el-form-item>

        <el-form-item
          label="冷却水直径"
          prop="cavity_cooling_water_diameter"
        >
          <el-input 
            v-model.trim="detail_info.cavity_cooling_water_diameter"
            type="number" 
            @input="detail_info.cavity_cooling_water_diameter=checkNumberFormat(detail_info.cavity_cooling_water_diameter, 0)"
          >
            <span slot="suffix">mm</span>
          </el-input>
        </el-form-item>

        <el-form-item
          label="水嘴安装规格"
          prop="cavity_water_nozzle_specification"
        >
          <el-input 
            v-model.trim="detail_info.cavity_water_nozzle_specification"
            type="number" 
            @input="detail_info.cavity_water_nozzle_specification=checkNumberFormat(detail_info.cavity_water_nozzle_specification, 0)"
          >
            <span slot="suffix">mm</span>
          </el-input>
        </el-form-item>

        <el-divider content-position="center">
          <span style="color:blue">后模（动模、型芯、公模）</span>
        </el-divider>

        <el-form-item
          label="冷却回路组数"
          prop="core_cooling_circuit_number"
        >
          <el-input 
            v-model.trim="detail_info.core_cooling_circuit_number"
            type="number" 
            @input="detail_info.core_cooling_circuit_number=checkNumberFormat(detail_info.core_cooling_circuit_number, 0)"
          >
            <span slot="suffix">组</span>
          </el-input>
        </el-form-item>

        <el-form-item
          label="冷却水直径"
          prop="core_cooling_water_diameter"
        >
          <el-input 
            v-model.trim="detail_info.core_cooling_water_diameter"
            type="number" 
            @input="detail_info.core_cooling_water_diameter=checkNumberFormat(detail_info.core_cooling_water_diameter, 0)"
          >
            <span slot="suffix">mm</span>
          </el-input>
        </el-form-item>

        <el-form-item
          label="水嘴安装规格"
          prop="core_water_nozzle_specification"
        >
          <el-input 
            v-model.trim="detail_info.core_water_nozzle_specification"
            type="number" 
            @input="detail_info.core_water_nozzle_specification=checkNumberFormat(detail_info.core_water_nozzle_specification, 0)"
          >
            <span slot="suffix">mm</span>
          </el-input>
        </el-form-item>

        <el-divider content-position="center">
          <span style="color:blue">附件</span>
        </el-divider>

        <el-form-item
          label="运水示意图"
        >
          <upload-single-file
            :value="circuit_picture_info"
            search-type="mold"
            @upload-file-info="onFileUploaded"
          >
          </upload-single-file>
        </el-form-item>
      </el-card>

      <div style="height: 4px"></div>

      <el-card class="box-card">
        <div slot="header" class="clearfix">
          <span>脱模系统</span>
        </div>

        <el-form-item 
          label="顶出行程"
          prop="ejector_stroke"
        >
          <el-input 
            v-model.trim="detail_info.ejector_stroke"
            type="number" 
            @input="detail_info.ejector_stroke=checkNumberFormat(detail_info.ejector_stroke)"
          >
            <span slot="suffix">mm</span>
          </el-input>
        </el-form-item>

        <el-form-item 
          label="顶棍孔直径"
          prop="ejector_rod_hole_diameter"
        >
          <el-input 
            v-model.trim="detail_info.ejector_rod_hole_diameter"
            type="number" 
            @input="detail_info.ejector_rod_hole_diameter=checkNumberFormat(detail_info.ejector_rod_hole_diameter, 0)"
          >
            <span slot="suffix">mm</span>
          </el-input>
        </el-form-item>

        <el-form-item 
          label="顶棍孔间距"
          prop="ejector_rod_hole_spacing"
        >
          <el-input 
            v-model.trim="detail_info.ejector_rod_hole_spacing"
            type="number" 
            @input="detail_info.ejector_rod_hole_spacing=checkNumberFormat(detail_info.ejector_rod_hole_spacing)"
          >
            <span slot="suffix">mm</span>
          </el-input>
        </el-form-item>

        <el-form-item 
          label="顶棍数量"
          prop="ejector_rod_number"
        >
          <el-input 
            v-model.trim="detail_info.ejector_rod_number"
            type="number" 
            @input="detail_info.ejector_rod_number=checkNumberFormat(detail_info.ejector_rod_number, 0)"
          >
            <span slot="suffix">个</span>
          </el-input>
        </el-form-item>

        <el-form-item 
          label="顶出力"
          prop="ejector_force"
        >
          <el-input 
            v-model.trim="detail_info.ejector_force"
            type="number" 
            @input="detail_info.ejector_force=checkNumberFormat(detail_info.ejector_force)"
          >
            <span slot="suffix">KN</span>
          </el-input>
        </el-form-item>

        <el-form-item 
          label="顶出次数"
          prop="ejector_times"
        >
          <el-input 
            v-model.trim="detail_info.ejector_times"
            type="number" 
            @input="detail_info.ejector_times=checkNumberFormat(detail_info.ejector_times, 0)"
          >
            <span slot="suffix">次</span>
          </el-input>
        </el-form-item>

        <el-form-item 
          label="复位方式"
          prop="reset_method"
        >
          <el-select 
            v-model="detail_info.reset_method"
            clearable
            filterable 
            allow-create
            default-first-option
          >
            <el-option label="弹回" value="弹回"></el-option>
            <el-option label="拉回" value="拉回"></el-option>
            <el-option label="压回" value="压回"></el-option>
          </el-select>
        </el-form-item>

        <el-form-item 
          label="顶出方式"
          prop="ejection_method"
        >
          <el-select 
            v-model="detail_info.ejection_method"
            clearable
            filterable 
            allow-create
            default-first-option
          >
            <el-option label="油缸" value="油缸"></el-option>
            <el-option label="机械" value="机械"></el-option>
          </el-select>
        </el-form-item>

        <el-form-item 
          label="顶出孔位置"
          prop="ejector_position_length"
        >
          <el-input 
            v-model.trim="detail_info.ejector_position_length"
            type="number" 
            @input="detail_info.ejector_position_length=checkNumberFormat(detail_info.ejector_position_length, 0)"
          >
            <span slot="suffix">mm</span>
          </el-input>&nbsp;&nbsp;×
        </el-form-item>
        <el-form-item 
          label=""
          prop="ejector_position_width"
        >
          <el-input 
            v-model.trim="detail_info.ejector_position_width"
            type="number" 
            @input="detail_info.ejector_position_width=checkNumberFormat(detail_info.ejector_position_width, 0)"
          >
            <span slot="suffix">mm</span>
          </el-input>
        </el-form-item>
      </el-card>

      <div style="height: 4px"></div>

      <el-card class="box-card">
        <div slot="header" class="clearfix">
          <span>吊装</span>
        </div>

        <el-form-item 
          label="模具重量"
          prop="mold_weight"
        >
          <el-input 
            v-model.trim="detail_info.mold_weight"
            type="number" 
            @input="detail_info.mold_weight=checkNumberFormat(detail_info.mold_weight)"
          >
            <span slot="suffix">kg</span>
          </el-input>
        </el-form-item>

        <el-form-item 
          label="吊模孔规格"
          prop="hanging_mold_hole_specification"
        >
          <el-select 
            v-model.trim="detail_info.hanging_mold_hole_specification"
            clearable
            filterable 
            allow-create
            default-first-option
          >
            <el-option
              v-for="item in hanging_mold_hole_specification_options" 
              :key="item.value" 
              :label="item.label" 
              :value="item.value"
            >
            </el-option>
          </el-select>
        </el-form-item> 
      </el-card>

      <div style="height: 4px"></div>

      <el-card class="box-card">
        <div slot="header" class="clearfix" id="machine_adaptive">
          <span>注塑机适配</span>
        </div>

        <el-form-item 
          label="定位圈直径"
          prop="locate_ring_diameter"
        >
          <div style="display: flex; align-items: center;">
            <el-select
              v-model.trim="detail_info.locate_ring_diameter"
              placeholder="请选择"
              @change="(value) => detail_info.locate_ring_diameter = checkNumberFormat(value)"
              clearable
              filterable
              style="flex: 1;"
            >
              <el-option
                v-for="option in locate_ring_diameter_options"
                :key="option.value"
                :label="option.label"
                :value="option.value"
              />
            </el-select>
            <span class="unit-suffix"
                  style="margin-left: -1px; padding: 0 10px; height: 40px; line-height: 40px; font-size:12px">
              mm
            </span>
          </div>
        </el-form-item>

        <el-form-item 
          label="模具尺寸（横）"
          prop="size_horizon"
        >
          <el-input 
            v-model.trim="detail_info.size_horizon"              
            type="number" 
            @input="detail_info.size_horizon=checkNumberFormat(detail_info.size_horizon)"
          >
            <span slot="suffix">mm</span>
          </el-input>
        </el-form-item>

        <el-form-item 
          label="模具尺寸（竖）"
          prop="size_vertical"
        >
          <el-input 
            v-model.trim="detail_info.size_vertical"
            type="number" 
            @input="detail_info.size_vertical=checkNumberFormat(detail_info.size_vertical)"
          >
            <span slot="suffix">mm</span>
          </el-input>
        </el-form-item>

        <el-form-item 
          label="模具厚度"
          prop="size_thickness"
        >
          <el-input 
            v-model.trim="detail_info.size_thickness"
            type="number" 
            @input="detail_info.size_thickness=checkNumberFormat(detail_info.size_thickness)"
          >
            <span slot="suffix">mm</span>
          </el-input>
        </el-form-item>

        <el-form-item 
          label="开模行程"
          prop="mold_opening_stroke"
        >
          <el-input 
            v-model.trim="detail_info.mold_opening_stroke"
            type="number" 
            @input="detail_info.mold_opening_stroke=checkNumberFormat(detail_info.mold_opening_stroke)"
          >
            <span slot="suffix">mm</span>
          </el-input>
        </el-form-item>

        <el-form-item 
          label="最小锁模力"
          prop="min_clamping_force"
        >
          <el-input 
            v-model.trim="detail_info.min_clamping_force"
            type="number" 
            @input="detail_info.min_clamping_force=checkNumberFormat(detail_info.min_clamping_force)"
          >
            <span slot="suffix">Ton</span>
          </el-input>
        </el-form-item>

        <el-form-item 
          label="取流道距离"
          prop="drain_distance"
          v-if="isShow"
        >
          <el-tooltip class="item" effect="dark" content="取出浇注系统所需的定模座板与流道板间分离的距离" placement="top-start">
            <el-input 
              v-model.trim="detail_info.drain_distance"
              type="number" 
              @input="detail_info.drain_distance=checkNumberFormat(detail_info.drain_distance)"
            >
              <span slot="suffix">mm</span>
            </el-input>
          </el-tooltip>
        </el-form-item>
      </el-card>

      <div style="height: 4px"></div>

      <el-card class="box-card">
        <div slot="header" class="clearfix">
          <span>特殊辅助装置</span>
        </div>
 
        <el-checkbox-group v-model="checkedEquipments">
          <el-checkbox
            v-for="(item,index) in assisting_equipment_options"
            :key="index"
            :label="item.label"
          >
          </el-checkbox>        
        </el-checkbox-group>
      </el-card>

      <div style="height: 4px"></div>

      <el-card class="box-card">
        <div slot="header" class="clearfix">
          <span>订单信息</span>
        </div>

        <el-form-item 
          label="客户"
          prop="customer"
        >
          <el-autocomplete
            v-model="detail_info.customer" 
            suffix-icon="el-icon-search"
            :fetch-suggestions="((str, cb)=>{querySuggestionOptions(str, cb, 'customer')})"
          > 
          </el-autocomplete>
        </el-form-item> 

        <el-form-item 
          label="项目工程师"
          prop="project_engineer"
        >
          <el-autocomplete
            v-model="detail_info.project_engineer" 
            suffix-icon="el-icon-search"
            :fetch-suggestions="((str, cb)=>{querySuggestionOptions(str, cb, 'project_engineer')})"
          > 
          </el-autocomplete>
        </el-form-item>

        <el-form-item 
          label="设计工程师"
          prop="design_engineer"
        >
          <el-autocomplete
            v-model="detail_info.design_engineer" 
            suffix-icon="el-icon-search"
            :fetch-suggestions="((str, cb)=>{querySuggestionOptions(str, cb, 'design_engineer')})"
          > 
          </el-autocomplete>
        </el-form-item>

        <el-form-item 
          label="制作工程师"
          prop="production_engineer"
        >
          <el-autocomplete
            v-model="detail_info.production_engineer" 
            suffix-icon="el-icon-search"
            :fetch-suggestions="((str, cb)=>{querySuggestionOptions(str, cb, 'production_engineer')})"
          > 
          </el-autocomplete>
        </el-form-item>

        <el-form-item 
          label="落单日期"
          prop="order_date" 
        >
          <el-date-picker
            v-model="detail_info.order_date" 
            type="date"
            placeholder="请选择日期"
            format="yyyy-MM-dd"
            value-format="yyyy-MM-dd"
            suffix-icon="el-icon-date"
          >
          </el-date-picker>
        </el-form-item>

      </el-card>
    </el-form>

    <div style="height:25px" />

    <div class="nextButton">
      <el-button
        v-if="viewType=='edit'" 
        type="success" 
        size="small"
        :loading="export_loading" 
        @click="exportMoldToExcel" 
      >
        导  出
      </el-button>
      <el-button 
        v-if="dialog"
        type="danger"
        size="small"
        @click="$emit('close')" 
      >
        返  回
      </el-button>
      <el-button 
        v-else
        type="danger"
        size="small"
        @click="resetView" 
      >
        重  置
      </el-button>
      <el-button 
        v-if="id && viewType !== 'copy' || $route.query.id" 
        type="primary" 
        size="small"
        :loading="update_loading" 
        @click="updateMoldDetail" 
        :disabled="!$store.state.user.userinfo.permissions.includes('update_mold')"
      >
        更  新
      </el-button>
      <el-button 
        v-else
        type="primary" 
        size="small"
        :loading="save_loading" 
        @click="saveMoldDetail"
        :disabled="!$store.state.user.userinfo.permissions.includes('add_mold')"
      >
        保  存
      </el-button>
    </div>
  </div>
</template>

<script>
import * as mold_const from '@/utils/mold-const'
import suggestionOptions from "@/mixins/suggestionOptions.vue"
import { projectMethod, exportMold, downloadFile, MailMethod, getOptions } from "@/api"
import { UserModule } from '@/store/modules/user'
import { dateToday } from '@/utils/datetime'
import { getFullReportUrl } from '@/utils/assert'
import UploadSingleFile from '@/components/uploadSingleFile'

export default {
  name: "MoldCreate",
  mixins: [suggestionOptions],
  components: { UploadSingleFile },
  props: {
    id: {
      type: Number,
      default: null
    },
    dialog: {
      type: Boolean,
      default: false
    },
    viewType: {
      type: String,
      default: null
    },
    excelData: {
      type: Object,
      default: () => ({})
    }
  },
  data() {
    return {
      detail_info: {
        company_id: UserModule.company_id,
        id: null,
        status: 1,

        mold_no: null,
        mold_name: null,
        mold_type: null,
        cavity_num: null,

        product_category: null,
        product_type: null,
        product_small_type: null,
        product_no: null,
        product_name: null,
        product_total_weight: null,
        product_projected_area: null,
        product_infos: [{
          inject_part: "0",
          mold_type: null,
          flow_length: null,
          ave_thickness: null,
          max_thickness: null,
          min_thickness: null,
          single_volume: null,
          single_weight: null,

          locate_ring_diameter: null,
          sprue_hole_diameter: null,
          sprue_sphere_radius: null,
          runner_type: null,
          hot_runner_num:null, //14,
          valve_num: null,
          runner_length: null,
          runner_weight: null,
          gate_type: null,
          gate_num: null,
          gate_shape: null,
          gate_area: null,
          gate_radius: null,
          gate_length: null,
          gate_width: null,
        }],

        cavity_cooling_water_diameter: null,
        cavity_cooling_circuit_number: null,
        cavity_water_nozzle_specification: null,
        core_cooling_water_diameter: null,
        core_cooling_circuit_number: null,
        core_water_nozzle_specification: null,
        circuit_picture_url: null,

        ejector_stroke: null,
        ejector_rod_hole_diameter: null,
        ejector_rod_hole_spacing: null,
        ejector_rod_number: null,
        ejector_force: null,
        ejector_times: null,
        reset_method: null,
        ejection_method: null,
        ejector_position_length: null,
        ejector_position_width: null,

        mold_weight: null,
        hanging_mold_hole_specification: null,

        locate_ring_diameter: null,
        size_horizon: null,
        size_vertical: null,
        size_thickness: null,
        mold_opening_stroke: null,
        min_clamping_force: null,
        drain_distance: null,
        inject_cycle_require: null,
        subrule_no: null,

        assisting_equipments: null,

        customer: null,
        project_engineer: null,
        design_engineer: null,
        production_engineer: null,
        mold_engineer: UserModule.engineer,
        product_engineer: null,
        junior_product_engineer: null,
        injection_engineer: null,
        senior_injection_engineer: null,

        order_date: dateToday(),
        entry_date: dateToday()
      },
      circuit_picture_info: {
        id: null,
        name: null,
        url: null
      },
      rules: {
        "mold_no": [
          { required: true, message: '模具编号不能为空', trigger: 'blur' },
        ],
        "cavity_num": [
          { required: true, message:'型腔数不能为空' },
          { pattern: /(^[1-9]+[+*]?[1-9]+$)|(^[1-9]+$)/, message: '请输入正确格式,如(1、1+1、1*2)' }
        ],
        "product_small_type": [{ required: true, message: '制品类别不能为空', trigger: 'blur' },],
        "product_name": [{ required: true, message: '制品名称不能为空', trigger: 'blur' },],    
        "product_total_weight": [{ required: true, message: '总重量不能为空', trigger: 'blur' },],
        "flow_length": [{ required: true, message: '制品流长不能为空', trigger: 'blur' },],   
        "max_thickness": [{ required: true, message: '最大壁厚不能为空', trigger: 'blur' },],
        "ave_thicknes": [{ required: true, message: '平均壁厚不能为空', trigger: 'blur' },],    
        "runner_type": [{ required: true, message: '流道类别不能为空', trigger: 'blur' },],
        "runner_length": [{ required: true, message: '流道长度不能为空', trigger: 'blur' },],    
        "runner_weight": [{ required: true, message: '流道重量不能为空', trigger: 'blur' },],
        "gate_type": [{ required: true, message: '浇口类别不能为空', trigger: 'blur' },],   
        "gate_num": [{ required: true, message: '浇口数量不能为空', trigger: 'blur' },],
        "gate_shape": [{ required: true, message: '浇口形状不能为空', trigger: 'blur' },],
        "hot_runner_num": [{ required: true, message: '热流道段数不能为空', trigger: 'blur' },],   
        "gate_length": [{ required: true, message: '浇口长不能为空', trigger: 'blur' },],
        "gate_width": [{ required: true, message: '浇口宽不能为空', trigger: 'blur' },],
        "gate_radius": [{ required: true, message: '浇口半径不能为空', trigger: 'blur' },],
      },
      export_loading: false,
      update_loading: false,
      save_loading: false,
      mold_type_options: mold_const.moldTypeOptions,
      gate_type_options: mold_const.gateTypeOptions,
      product_category_options: mold_const.productCategoryOptions,
      product_type_options: null,
      product_small_type_options: null,
      hanging_mold_hole_specification_options: mold_const.hangingMoldHoleSpeOptions, 
      sprue_sphere_radius_options: mold_const.sprueSphereRadiusOptions,
      sprue_hole_diameter_options: mold_const.sprueHoleDiameterOptions,
      locate_ring_diameter_options: mold_const.locateRingDiameterOptions,
      assisting_equipment_options: mold_const.assistingEquipmentOptions,
      isShow: false,
      mold_id: null,
    }
  },
  created() {
    // 带着query的id来
    this.$nextTick(() => {
      if (this.$route.query.id) {
        document.getElementById("machine_adaptive").scrollIntoView()
      }
    })
  },
  mounted() {
    this.mold_id = this.id
    if (this.$route.query.id) {
      this.mold_id = this.$route.query.id
    }
    this.getMoldDetail()
  },
  methods: {
    querySubRuleNoList(str, cb) {
      str = str == null ? "" : str 
      let promptList = []
      getOptions("rule_library", { "form_input": str, "db_table": "rule_flow" })
      .then( res => {
        if(res.status == 0) {
          for(let i = 0; i < res.data.length; i++) {
            promptList.push({ value: res.data[i] })
          }
        }
      })
      cb(promptList)
    }, 
    querySuggestionOptions(input, cb, type) {
      if (["product_type", "customer", "project_engineer", 
      "design_engineer", "production_engineer"].includes(type)) {
        cb(this.queryOptions(input, type, "mold"))
      } else if (type == "locate_ring_diameter") {
        cb(this.locate_ring_diameter_options)
      } else if (type == "sprue_hole_diameter") {
        cb(this.sprue_hole_diameter_options)
      } else if (type == "sprue_sphere_radius") {
        cb(this.sprue_sphere_radius_options)
      }
    },
    changeRunnerType(val) {
      if (val == "热流道") {
        this.gate_type_options = mold_const.hotRunnerGateTypeOptions
        this.detail_info.product_infos.runner_weight = null
      } else if (val == "冷流道") {
        this.gate_type_options = mold_const.gateTypeOptions
        this.detail_info.product_infos.valve_num = null
      } else if (val == "热转冷") {
        this.gate_type_options = mold_const.hotToColdTypeOptions
      }
    },
    exportMoldToExcel() {
      exportMold(this.detail_info)
      .then(res => {
        if (res.status === 0 && res.data.url) {
          this.$message({message: '导出成功。', type: 'success'})
          this.$emit('close')
          window.location.href = getFullReportUrl(res.data.url)
        }
      })
    },
    getMoldDetail() {
      if (this.mold_id) {
        projectMethod.getDetail(this.mold_id)
        .then(res => {
          if (res.status === 0) {
            this.detail_info = res.data.mold_info
            if (this.viewType == "edit") {

            } else if (this.viewType == "copy") {
              this.detail_info.id = null
              this.detail_info.mold_no = null
              for(let i = 0; i < this.detail_info.product_infos.length; i++) {
                this.detail_info.product_infos[i].id = null
              }
            }

            if (this.detail_info.circuit_picture_url) {
              downloadFile({
                "search_type": "mold",
                "file_url": this.detail_info.circuit_picture_url
              }).then(res => {
                if (res.status === 0 && res.data.length > 0) {
                  this.circuit_picture_info.id = res.data[0].id
                  this.circuit_picture_info.name = res.data[0].name
                  this.circuit_picture_info.url = res.data[0].url
                }
              })
            } else {
              this.circuit_picture_info.id = null
              this.circuit_picture_info.name = null
              this.circuit_picture_info.url = null
            }
          }
        })
      }
      if (this.viewType == "add") {
        this.detail_info.status = 1 // 新增
      } else if (this.viewType == "upload" && this.excelData && JSON.stringify(this.excelData)!="{}") {
        this.detail_info = this.excelData
        if (this.detail_info.mold_type && this.detail_info.mold_type.indexOf('三板模')!=-1) {
          this.isShow = true
        } else {
          this.isShow = false
        }    
      }
    },
    saveMoldDetail() {
      this.$refs["mold_info"].validate((valid) => {
        if (valid) {
          this.saveMold()
        } else {
          if(!this.detail_info.mold_no){
            this.$message({ message: '请填写模具编号', type: 'warning' })
            return
          } else {
            this.$confirm(`有些必填参数没有填,确认保存吗？`, '保存模具', {
              confirmButtonText: '确定',        
              cancelButtonText: '取消',
              type: 'warning'
            }).then(() => {
              this.saveMold()
            }).catch(() => {
              this.$message({
                type: 'info',
                message: '已返回'
              })
            })  
          }
        }
      })
    },
    saveMold(){
      projectMethod.add({ 
        mold_info: this.detail_info
      }).then(res => {
        if (res.status === 0) {
          this.$message({ message: '模具信息新增成功！', type: 'success' })
          // 发送邮件
          // let local_mold_info = this.detail_info
          // local_mold_info.id = res.data.id
          // this.sendEmail(local_mold_info)
          this.$emit("close")
          this.$router.push('/mold/list')
        }
      })
    },
    updateMoldDetail() {
      this.$refs["mold_info"].validate((valid) => {
        if (valid) {
          projectMethod.edit({ mold_info: this.detail_info }, this.mold_id)
          .then(res => {
            if(res.status === 0) {
              this.$message({ message: '模具信息编辑成功！', type: 'success' })
              this.$emit("close")
              this.$router.push('/mold/list')
            }
          })
        }
      })
    },
    onFileUploaded(fileInfo) {
      if (fileInfo) {
        this.detail_info.circuit_picture_url = fileInfo.url
      } else {
        this.detail_info.circuit_picture_url = null
      }
    },
    resetView() {
      this.detail_info = {
        company_id: UserModule.company_id,
        id: null,
        status: 1,

        mold_no: null,
        mold_name: null,
        mold_type: null,
        cavity_num: null,

        product_category: null,
        product_type: null,
        product_small_type: null,
        product_no: null,
        product_name: null,
        product_total_weight: null,
        product_projected_area: null,
        product_infos: [{
          inject_part: "0",
          mold_type: null,
          flow_length: null,
          ave_thickness: null,
          max_thickness: null,
          min_thickness: null,
          single_volume: null,
          single_weight: null,

          locate_ring_diameter: null,
          sprue_hole_diameter: null,
          sprue_sphere_radius: null,
          runner_type: null,
          hot_runner_num: null, //14, 
          valve_num: null,
          runner_length: null,
          runner_weight: null,
          // hot_runner_volume: null,
          gate_type: null,
          gate_num: null,
          gate_shape: null,
          gate_area: null,
          gate_radius: null,
          gate_length: null,
          gate_width: null,          
        }],

        cavity_cooling_water_diameter: null,
        cavity_cooling_circuit_number: null,
        cavity_water_nozzle_specification: null,
        core_cooling_water_diameter: null,
        core_cooling_circuit_number: null,
        core_water_nozzle_specification: null,
        circuit_picture_url: null,

        ejector_stroke: null,
        ejector_rod_hole_diameter: null,
        ejector_rod_hole_spacing: null,
        ejector_rod_number: null,
        ejector_force: null,
        ejector_times: null,
        reset_method: null,
        ejection_method: null,
        ejector_position_length: null,
        ejector_position_width: null,

        mold_weight: null,
        hanging_mold_hole_specification: null,

        locate_ring_diameter: null,
        size_horizon: null,
        size_vertical: null,
        size_thickness: null,
        mold_opening_stroke: null,
        min_clamping_force: null,
        drain_distance: null,
        inject_cycle_require: null,

        assisting_equipments: null,

        customer: null,
        project_engineer: null,
        design_engineer: null,
        production_engineer: null,
        mold_engineer: UserModule.engineer,
        product_engineer: null,
        junior_product_engineer: null,
        injection_engineer: null,
        senior_injection_engineer: null,

        order_date: dateToday(),
        entry_date: dateToday()
      }
    },
    sendEmail(project) {
      MailMethod("mold", { "project": project })
      .then((res) => {
        if(res.data.message) {
          this.$notify({
            title: '提示', 
            message: res.data.message, 
            dangerouslyUseHTMLString: true
          });
        }
      })
    },
  },
  computed: {
    checkedEquipments: {
      get:function() {
        if (this.detail_info.assisting_equipments) {
          return this.detail_info.assisting_equipments.split("|")
        }
        return []
      },
      set:function(value) {
        if (value) {
          this.detail_info.assisting_equipments = value.join("|")
        }
      }
    },
    gateSectionalArea: {
      get: function() {
        let area = null
        if (this.detail_info.gate_shape == "矩形") {
          if (this.detail_info.gate_length && this.detail_info.gate_width) {
            area = Number(this.detail_info.gate_length) * Number(this.detail_info.gate_width) / 100
          }
        } else if (this.detail_info.gate_shape == "圆形") {
          if (this.detail_info.gate_radius) {
            area = 3.14 * (Number(this.detail_info.gate_radius) ** 2) / 100
          }
        }
        return area
      }
    }
  },
  watch: {
    id() {
      if (this.id) {
        this.mold_id = this.id
        this.getMoldDetail()
      }
    },
    'detail_info.runner_type' () {
      if (this.detail_info.product_infos.runner_type == "热流道") {
        this.gate_type_options = mold_const.hotRunnerGateTypeOptions
        this.detail_info.product_infos.runner_weight = null
      } else if (this.detail_info.product_infos.runner_type == "冷流道") {
        this.gate_type_options = mold_const.gateTypeOptions
        this.detail_info.product_infos.valve_num = null
      } else if (this.detail_info.product_infos.runner_type == "热转冷") {
        this.gate_type_options = mold_const.hotToColdTypeOptions
      }
    },
    'detail_info.mold_type' () {
      let mold_product = {
        "两板模|单色模": 1,
        "两板模|双色模": 2,
        "两板模|三色模": 3,
        "三板模|单色模": 1,
        "三板模|双色模": 2,
        "三板模|三色模": 3
      }

      if (this.detail_info.mold_type) {
        let mold_type = this.detail_info.mold_type
        let prod_num = mold_product[mold_type]
        let curr_prod_num = this.detail_info.product_infos.length

        if (prod_num < curr_prod_num) {
          this.detail_info.product_infos = this.detail_info.product_infos.slice(0, prod_num)
        } else {
          for (let i = 0; i < prod_num; ++i) {
            if (i < curr_prod_num) {
              this.detail_info.product_infos[i].mold_type = mold_type
              this.detail_info.product_infos[i].inject_part = String(i)
            } else {
              this.detail_info.product_infos.push({
                mold_type: mold_type,
                inject_part: String(i),
                flow_length: null,
                ave_thickness: null,
                max_thickness: null,
                min_thickness: null,
                single_volume: null,
                single_weight: null,

                locate_ring_diameter: null,
                sprue_hole_diameter: null,
                sprue_sphere_radius: null,
                runner_type: null,
                valve_num: null,
                runner_length: null,
                runner_weight: null,
                // hot_runner_volume: null,
                gate_type: null,
                gate_num: null,
                gate_shape: null,
                gate_area: null,
                gate_radius: null,
                gate_length: null,
                gate_width: null,  
              })
            }
          }
        }
      }

      if (this.detail_info.mold_type && this.detail_info.mold_type.indexOf('三板模')!=-1) {
        this.isShow = true
      } else {
        this.isShow = false
      }
    },
    excelData: {
      handler: function() {
        if (this.excelData) {
          this.detail_info = this.excelData
        }
      },
      deep: true
    },
    'detail_info.product_category' () {
      const categoryOptions = {
        '家用电器': mold_const.electricApplianceOptions,
        '消费电子': mold_const.electronicOptions,
        '交通运输': mold_const.trafficOptions,
        '医疗健康': mold_const.medicalHealthOptions,
        '建材家居': mold_const.buildingFurnishingsOptions,
        '包装': mold_const.packagingOptions,
        '办公文教': mold_const.officeEducationOptions,
        '玩具休闲': mold_const.toysLeisureOptions,
      }
      this.product_type_options = categoryOptions[this.detail_info.product_category] || null;
    },
    'detail_info.product_type' () {
      this.product_small_type_options = mold_const.smallTypeOptions[this.detail_info.product_type] || null;
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
  .el-date-picker {
    width: 10rem;
  }

</style>
