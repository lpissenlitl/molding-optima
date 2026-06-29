<template>
  <div class="createPolymer">
    <el-form 
      ref="polymer_info" 
      size="mini" 
      label-width="10rem" 
      label-position="right" 
      :model="polymer_info" 
      :inline="true"
      :rules="rules"
    >
      <el-card>
        <div slot="header" class="clearfix">
          塑料描述
        </div>

        <el-form-item 
          label="塑料简称" 
          prop="abbreviation" 
        >
          <el-autocomplete
            v-model="polymer_info.abbreviation"
            placeholder="塑料简称"
            clearable
            :fetch-suggestions="queryPolymerAbbreviation"
          >
          </el-autocomplete>
        </el-form-item>
        
        <el-form-item label="塑料牌号" prop="trademark">
          <el-input
            v-model="polymer_info.trademark"
            placeholder="塑料牌号"
            clearable
          >
          </el-input>
        </el-form-item>
        
        <el-form-item label="制造厂商" prop="manufacturer">
          <el-input v-model="polymer_info.manufacturer">
          </el-input>
        </el-form-item>
        
        <el-form-item label="塑料类别" prop="category">
          <el-select v-model="polymer_info.category">
            <el-option label="结晶型" value="结晶型"></el-option>
            <el-option label="无定形" value="无定形"></el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="数据来源" prop="data_source">
          <el-input v-model="polymer_info.data_source">
          </el-input>
        </el-form-item>
        
        <el-form-item label="塑料状态" prop="data_status">
          <el-input v-model="polymer_info.data_status">
          </el-input>
        </el-form-item>
        
        <el-form-item label="塑料ID" prop="internal_id">
          <el-input v-model="polymer_info.internal_id">
          </el-input>
        </el-form-item>
        
        <el-form-item label="等级代码" prop="level_code">
          <el-input v-model="polymer_info.level_code">
          </el-input>
        </el-form-item>
        
        <el-form-item label="材料供应商" prop="vendor_code">
          <el-input v-model="polymer_info.vendor_code">
          </el-input>
        </el-form-item>
      </el-card>

      <div style="height: 4px" />

      <el-card>
        <div slot="header" class="clearfix">
          成型参数
        </div>

        <el-divider content-position="center">
          <span style="color: blue">推荐成型参数</span>
        </el-divider>

        <el-form-item label="最大成型温度" prop="max_melt_temperature">
          <el-input
            type="number"
            min="0" 
            v-model="polymer_info.max_melt_temperature"
            @input="polymer_info.max_melt_temperature=checkNumberFormat(polymer_info.max_melt_temperature)"
          >
            <span slot="suffix">℃</span>
          </el-input>
        </el-form-item>
        
        <el-form-item label="最小成型温度" prop="min_melt_temperature">
          <el-input
            type="number"
            min="0" 
            v-model="polymer_info.min_melt_temperature"
            @input="polymer_info.min_melt_temperature=checkNumberFormat(polymer_info.min_melt_temperature)"
          >
            <span slot="suffix">℃</span>
          </el-input>
        </el-form-item>
        
        <el-form-item label="推荐成型温度" prop="recommend_melt_temperature">
          <el-input
            type="number"
            min="0" 
            v-model="polymer_info.recommend_melt_temperature"
            @input="polymer_info.recommend_melt_temperature=checkNumberFormat(polymer_info.recommend_melt_temperature)"
          >
            <span slot="suffix">℃</span>
          </el-input>
        </el-form-item>
        
        <el-form-item label="塑料降解温度" prop="degradation_temperature">
          <el-input
            type="number"
            min="0" 
            v-model="polymer_info.degradation_temperature"
            @input="polymer_info.degradation_temperature=checkNumberFormat(polymer_info.degradation_temperature)"
          >
            <span slot="suffix">℃</span>
          </el-input>
        </el-form-item>
        
        <el-form-item label="最大模具温度" prop="max_mold_temperature">
          <el-input 
            type="number" 
            min="0" 
            v-model="polymer_info.max_mold_temperature"
            @input="polymer_info.max_mold_temperature=checkNumberFormat(polymer_info.max_mold_temperature)"
          >
            <span slot="suffix">℃</span>
          </el-input>
        </el-form-item>
        
        <el-form-item label="最小模具温度" prop="min_mold_temperature">
          <el-input 
            type="number" 
            min="0" 
            v-model="polymer_info.min_mold_temperature"
            @input="polymer_info.min_mold_temperature=checkNumberFormat(polymer_info.min_mold_temperature)"
          >
            <span slot="suffix">℃</span>
          </el-input>
        </el-form-item>
        
        <el-form-item label="推荐模具温度" prop="recommend_mold_temperature">
          <el-input 
            type="number" 
            min="0" 
            v-model="polymer_info.recommend_mold_temperature"
            @input="polymer_info.recommend_mold_temperature=checkNumberFormat(polymer_info.recommend_mold_temperature)"
          >
            <span slot="suffix">℃</span>
          </el-input>
        </el-form-item>
        
        <el-form-item label="顶出温度" prop="ejection_temperature">
          <el-input 
            type="number" 
            min="0" 
            v-model="polymer_info.ejection_temperature"
            @input="polymer_info.ejection_temperature=checkNumberFormat(polymer_info.ejection_temperature)"
          >
            <span slot="suffix">℃</span>
          </el-input>
        </el-form-item>
        
        <el-form-item label="最大剪切线速度" prop="max_shear_linear_speed">
          <el-input 
            type="number" 
            min="0" 
            v-model="polymer_info.max_shear_linear_speed"
            @input="polymer_info.max_shear_linear_speed=checkNumberFormat(polymer_info.max_shear_linear_speed)"
          >
            <span slot="suffix">mm/s</span>
          </el-input>
        </el-form-item>
        
        <el-form-item label="最小剪切线速度" prop="min_shear_linear_speed">
          <el-input 
            type="number" 
            min="0" 
            v-model="polymer_info.min_shear_linear_speed"
            @input="polymer_info.min_shear_linear_speed=checkNumberFormat(polymer_info.min_shear_linear_speed)"
          >
            <span slot="suffix">mm/s</span>
          </el-input>
        </el-form-item>
        
        <el-form-item label="推荐剪切线速度" prop="recommend_shear_linear_speed">
          <el-input 
            type="number" 
            min="0" 
            v-model="polymer_info.recommend_shear_linear_speed"
            @input="polymer_info.recommend_shear_linear_speed=checkNumberFormat(polymer_info.recommend_shear_linear_speed)"
          >
            <span slot="suffix">mm/s</span>
          </el-input>
        </el-form-item>
        
        <el-form-item label="推荐注射速率" prop="recommend_injection_rate">
          <el-input
            type="number"
            v-model="polymer_info.recommend_injection_rate"
            @input="polymer_info.recommend_injection_rate=checkNumberFormat(polymer_info.recommend_injection_rate)"
          >
            <span slot="suffix">cm<sup>3</sup>/s</span>
          </el-input>
        </el-form-item>
        
        <el-form-item label="最大剪切速率" prop="max_sheer_rate">
          <el-input
            type="number"
            v-model="polymer_info.max_sheer_rate"
            @input="polymer_info.max_sheer_rate=checkNumberFormat(polymer_info.max_sheer_rate)"
          >
            <span slot="suffix">1/s</span>
          </el-input>
        </el-form-item>
        
        <el-form-item label="最大剪切应力" prop="max_sheer_stress">
          <el-input
            type="number"
            v-model="polymer_info.max_sheer_stress"
            @input="polymer_info.max_sheer_stress=checkNumberFormat(polymer_info.max_sheer_stress)"
          >
            <span slot="suffix">MPa</span>
          </el-input>
        </el-form-item>
        
        <el-form-item label="推荐背压" prop="recommend_back_pressure">
          <el-input 
            type="number" 
            min="0" 
            v-model="polymer_info.recommend_back_pressure"
            @input="polymer_info.recommend_back_pressure=checkNumberFormat(polymer_info.recommend_back_pressure)"
          >
            <span slot="suffix">MPa</span>
          </el-input>
        </el-form-item>
        
        <el-form-item label="料筒停留时间" prop="barrel_residence_time">
          <el-input 
            v-model="polymer_info.barrel_residence_time"
            @input="polymer_info.barrel_residence_time=checkNumberFormat(polymer_info.barrel_residence_time)"
          >
            <span slot="suffix">min</span>
          </el-input>
        </el-form-item>
        
        <el-divider content-position="center">
          <span style="color: blue">塑料干燥</span>
        </el-divider>

        <el-form-item label="干燥方式" prop="dry_method">
          <el-select 
            v-model="polymer_info.dry_method" 
            clearable
            filterable
            allow-create
            default-first-option
          >
            <el-option
              v-for="item in drying_method_options"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            >
            </el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="干燥温度" prop="dry_temperature">
          <el-input 
            type="string" 
            v-model="polymer_info.dry_temperature"
          >
            <span slot="suffix">℃</span>
          </el-input>
        </el-form-item>
        
        <el-form-item label="干燥时间" prop="dry_time">
          <el-input 
            type="string" 
            v-model="polymer_info.dry_time"
          >
            <span slot="suffix">h</span>
          </el-input>
        </el-form-item>
      </el-card>

      <div style="height: 4px" />

      <el-card v-if="polymer_info.company_id > 0 || $store.state.user.userinfo.is_super == 1">
        <div slot="header" class="clearfix">
          pvT属性
        </div>

        <el-form-item label="熔融密度" prop="melt_density">
          <el-input 
            type="number" 
            min="0" 
            v-model="polymer_info.melt_density"
            @input="polymer_info.melt_density=checkNumberFormat(polymer_info.melt_density, fixed=4)"
          >
            <span slot="suffix">g/cm<sup>3</sup></span>
          </el-input>
        </el-form-item>
        
        <el-form-item label="固态密度" prop="solid_density">
          <el-input
            type="number"
            min="0" 
            v-model="polymer_info.solid_density"
            @input="polymer_info.solid_density=checkNumberFormat(polymer_info.solid_density, fixed=4)"
          >
            <span slot="suffix">g/cm<sup>3</sup></span>
          </el-input>
        </el-form-item>
        <el-button 
          type="success"
          size="small"
          @click="setDensity" 
        >
          填入参考密度
        </el-button>
        <br>

        <el-form-item label="b5">
          <el-input
            type="number"
            min="0" 
            v-model="polymer_info.Tait_pvT_b5"
          >
            <span slot="suffix">K</span>
          </el-input>
        </el-form-item>
        
        <el-form-item label="b6">
          <el-input
            type="number"
            min="0" 
            v-model="polymer_info.Tait_pvT_b6"
          >
            <span slot="suffix">K/Pa</span>
          </el-input>
        </el-form-item>
        
        <el-form-item label="b1m">
          <el-input
            type="number"
            min="0" 
            v-model="polymer_info.Tait_pvT_b1m"
          >
            <span slot="suffix">m<sup>3</sup>/kg</span>
          </el-input>
        </el-form-item>
        
        <el-form-item label="b2m">
          <el-input
            type="number"
            min="0" 
            v-model="polymer_info.Tait_pvT_b2m"
          >
            <span slot="suffix">m<sup>3</sup>/kg-K</span>
          </el-input>
        </el-form-item>
        
        <el-form-item label="b3m">
          <el-input 
            type="number"
            min="0" 
            v-model="polymer_info.Tait_pvT_b3m"
          >
            <span slot="suffix">Pa</span>
          </el-input>
        </el-form-item>
        
        <el-form-item label="b4m">
          <el-input 
            type="number"
            min="0" 
            v-model="polymer_info.Tait_pvT_b4m"
          >
            <span slot="suffix">1/K</span>
          </el-input>
        </el-form-item>
        
        <el-form-item label="b1s">
          <el-input 
            type="number"
            min="0" 
            v-model="polymer_info.Tait_pvT_b1s"
          >
            <span slot="suffix">m<sup>3</sup>/kg</span>
          </el-input>
        </el-form-item>
        
        <el-form-item label="b2s">
          <el-input 
            type="number"
            min="0" 
            v-model="polymer_info.Tait_pvT_b2s"
          >
            <span slot="suffix">m<sup>3</sup>/kg-K</span>
          </el-input>
        </el-form-item>
        
 
        <el-form-item label="b3s">
          <el-input 
            type="number"
            min="0" 
            v-model="polymer_info.Tait_pvT_b3s"
          >
            <span slot="suffix">Pa</span>
          </el-input>
        </el-form-item>
        
        <el-form-item label="b4s">
          <el-input 
            type="number"
            min="0" 
            v-model="polymer_info.Tait_pvT_b4s"
          >
            <span slot="suffix">1/k</span>
          </el-input>
        </el-form-item>
        
        <el-form-item label="b7">
          <el-input 
            type="number"
            min="0" 
            v-model="polymer_info.Tait_pvT_b7"
          >
            <span slot="suffix">m<sup>3</sup>/kg</span>
          </el-input>
        </el-form-item>
        
        <el-form-item label="b8">
          <el-input 
            type="number"
            min="0" 
            v-model="polymer_info.Tait_pvT_b8"
          >
            <span slot="suffix">1/K</span>
          </el-input>
        </el-form-item>
        
        <el-form-item label="b9">
          <el-input
            type="number"
            min="0" 
            v-model="polymer_info.Tait_pvT_b9"
          >
            <span slot="suffix">1/Pa</span>
          </el-input>
        </el-form-item>
      </el-card>
      <div style="height: 4px" v-if="polymer_info.company_id > 0 || $store.state.user.userinfo.is_super == 1" />
      <el-card v-if="polymer_info.company_id > 0 || $store.state.user.userinfo.is_super == 1">
        <div slot="header" class="clearfix">
          流变属性
        </div>

        <el-divider content-position="center">
          <span style="color: blue">粘度模型 cross_WLF</span>
        </el-divider>
        
        <el-form-item label="n">
          <el-input
            type="number"
            min="0"
            v-model="polymer_info.cross_WLF_n"
          >
            <span slot="suffix"></span>
          </el-input>
        </el-form-item>
        
        <el-form-item label="Tau">
          <el-input
            type="number"
            min="0"
            v-model="polymer_info.cross_WLF_Tau"
          >
            <span slot="suffix">Pa</span>
          </el-input>
        </el-form-item>
        
        <el-form-item label="D1">
          <el-input
            type="number"
            min="0"
            v-model="polymer_info.cross_WLF_D1"
          >
            <span slot="suffix">Pa-s</span>
          </el-input>
        </el-form-item>
        
        <el-form-item label="D2">
          <el-input
            type="number"
            min="0"
            v-model="polymer_info.cross_WLF_D2"
          >
            <span slot="suffix">k</span>
          </el-input>
        </el-form-item>
        
        <el-form-item label="D3">
          <el-input
            type="number"
            min="0"
            v-model="polymer_info.cross_WLF_D3"
          >
            <span slot="suffix">k/Pa</span>
          </el-input>
        </el-form-item>
        
        <el-form-item label="A1">
          <el-input 
            type="number"
            min="0"
            v-model="polymer_info.cross_WLF_A1"
          >
            <span slot="suffix"></span>
          </el-input>
        </el-form-item>
        
        <el-form-item label="A2">
          <el-input 
            type="number"
            min="0"
            v-model="polymer_info.cross_WLF_A2"
          >
            <span slot="suffix">k</span>
          </el-input>
        </el-form-item>
        
        <el-divider content-position="center">
          <span style="color: blue">接合点损失法系数</span>
        </el-divider>
        
        <el-form-item label="c1">
          <el-input 
            type="number"
            min="0"
            v-model="polymer_info.c1"
          >
            <span slot="suffix">Pa^(1-c2)</span>
          </el-input>
        </el-form-item>
        
        <el-form-item label="c2">
          <el-input 
            type="number"
            min="0"
            v-model="polymer_info.c2"
          >
            <span slot="suffix"></span>
          </el-input>
        </el-form-item>
        
        <el-form-item label="转换温度">
          <el-input 
            type="number"
            min="0"
            v-model="polymer_info.switch_temp"
          >
            <span slot="suffix">℃</span>
          </el-input>
        </el-form-item>
        
        <el-form-item label="粘度指数">
          <el-input 
            type="number"
            min="0"
            v-model="polymer_info.viscosity_index"
          >
            <span slot="suffix"></span>
          </el-input>
        </el-form-item>
        
        <el-form-item label="MFR温度">
          <el-input 
            type="number"
            min="0"
            v-model="polymer_info.MFR_temp"
          >
            <span slot="suffix">℃</span>
          </el-input>
        </el-form-item>
        
        <el-form-item label="MFR载荷">
          <el-input 
            type="number"
            min="0"
            v-model="polymer_info.MFR_load"
          >
            <span slot="suffix">Kg</span>
          </el-input>
        </el-form-item>
        
        <el-form-item 
          label="MFR值"
        >
          <el-input
            type="number"
            min="0"
            v-model="polymer_info.MFR_measure"
          >
            <span slot="suffix">g/10min</span>
          </el-input>
        </el-form-item>
      </el-card>

      <div style="height: 4px" v-if="polymer_info.company_id > 0 || $store.state.user.userinfo.is_super == 1" />

      <el-card v-if="polymer_info.company_id > 0 || $store.state.user.userinfo.is_super == 1">
        <div slot="header" class="clearfix">
          机械属性
        </div>

        <el-divider content-position="center">
          <span style="color: blue">机械属性</span>
        </el-divider>
        
        <el-form-item label="弹性模量E1">
          <el-input 
            type="number"
            min="0" 
            v-model="polymer_info.E1"
            @input="polymer_info.E1=checkNumberFormat(polymer_info.E1)"
          >
            <span slot="suffix">MPa</span>
          </el-input>
        </el-form-item>
        
        <el-form-item label="弹性模量E2">
          <el-input
            type="number"
            min="0" 
            v-model="polymer_info.E2"
            @input="polymer_info.E2=checkNumberFormat(polymer_info.E2)"
          >
            <span slot="suffix">MPa</span>
          </el-input>
        </el-form-item>
        
        <el-form-item label="泊松比v12">
          <el-input
            type="number"
            min="0" 
            v-model="polymer_info.v12"
            @input="polymer_info.v12=checkNumberFormat(polymer_info.v12)"
          >
            <span slot="suffix"></span>
          </el-input>
        </el-form-item>
        
        <el-form-item label="泊松比v23">
          <el-input 
            type="number"
            min="0" 
            v-model="polymer_info.v23"
            @input="polymer_info.v23=checkNumberFormat(polymer_info.v23)"
          >
            <span slot="suffix"></span>
          </el-input>
        </el-form-item>
        
        <el-form-item label="剪切模量G12">
          <el-input
            type="number"
            min="0" 
            v-model="polymer_info.G12"
            @input="polymer_info.G12=checkNumberFormat(polymer_info.G12)"
          >
            <span slot="suffix">MPa</span>
          </el-input>
        </el-form-item>
        
        <el-divider content-position="center">
          <span style="color: blue">热膨胀 (CTE) 数据系数</span>
        </el-divider>
        
        <el-form-item label="Alpha1">
          <el-input 
            type="number"
            min="0" 
            v-model="polymer_info.Alpha1"
            @input="polymer_info.Alpha1=checkNumberFormat(polymer_info.Alpha1)"
          >
            <span slot="suffix">1/C</span>
          </el-input>
        </el-form-item>
        
        <el-form-item label="Alpha2">
          <el-input
            type="number"
            min="0" 
            v-model="polymer_info.Alpha2"
            @input="polymer_info.Alpha2=checkNumberFormat(polymer_info.Alpha2)"
          >
            <span slot="suffix">1/C</span>
          </el-input>
        </el-form-item>
      </el-card>

      <div style="height: 4px" v-if="polymer_info.company_id > 0 || $store.state.user.userinfo.is_super == 1" />

      <el-card v-if="polymer_info.company_id > 0 || $store.state.user.userinfo.is_super == 1">
        <div slot="header" class="clearfix">
          收缩属性
        </div>

        <el-divider content-position="center">
          <span style="color: blue">测试平均收缩率</span>
        </el-divider>
        
        <el-form-item label="平行收缩率">
          <el-input 
            type="number"
            min="0" 
            v-model="polymer_info.average_horizontal_shrinkage"
            @input="polymer_info.average_horizontal_shrinkage=checkNumberFormat(polymer_info.average_horizontal_shrinkage)"
          >
            <span slot="suffix">%</span>
          </el-input>
        </el-form-item>
        
        <el-form-item label="垂直收缩率">
          <el-input 
            type="number"
            min="0" 
            v-model="polymer_info.average_vertical_shrinkage"
            @input="polymer_info.average_vertical_shrinkage=checkNumberFormat(polymer_info.average_vertical_shrinkage)"
          >
            <span slot="suffix">%</span>
          </el-input>
        </el-form-item>
        
        <el-divider content-position="center">
          <span style="color: blue">测试收缩率范围</span>
        </el-divider>
        
        <el-form-item label="最小平行收缩率">
          <el-input 
            type="number"
            min="0" 
            v-model="polymer_info.min_horizontal_shrinkage"
            @input="polymer_info.min_horizontal_shrinkage=checkNumberFormat(polymer_info.min_horizontal_shrinkage)"
          >
            <span slot="suffix">%</span>
          </el-input>
        </el-form-item>
        
        <el-form-item label="最大平行收缩率">
          <el-input 
            type="number"
            min="0" 
            v-model="polymer_info.max_horizontal_shrinkage"
            @input="polymer_info.max_horizontal_shrinkage=checkNumberFormat(polymer_info.max_horizontal_shrinkage)"
          >
            <span slot="suffix">%</span>
          </el-input>
        </el-form-item>
        
        <el-form-item label="最小垂直收缩率">
          <el-input 
            type="number"
            min="0" 
            v-model="polymer_info.min_vertical_shrinkage"
            @input="polymer_info.min_vertical_shrinkage=checkNumberFormat(polymer_info.min_vertical_shrinkage)"
          >
            <span slot="suffix">%</span>
          </el-input>
        </el-form-item>
        
        <el-form-item label="最大垂直收缩率">
          <el-input 
            type="number"
            min="0" 
            v-model="polymer_info.max_vertical_shrinkage"
            @input="polymer_info.max_vertical_shrinkage=checkNumberFormat(polymer_info.max_vertical_shrinkage)"
          >
            <span slot="suffix">%</span>
          </el-input>
        </el-form-item>
      </el-card>

      <div style="height: 4px" v-if="polymer_info.company_id > 0 || $store.state.user.userinfo.is_super == 1" />

      <el-card v-if="polymer_info.company_id > 0 || $store.state.user.userinfo.is_super == 1">
        <div slot="header" class="clearfix">
          填充物属性
        </div>

        <el-divider content-position="center">
          <span style="color: blue">基本信息</span>
        </el-divider>
        
        <el-form-item label="填充物">
          <el-input v-model="polymer_info.filler">
          </el-input>
        </el-form-item>
        
        <el-form-item label="填充物类型">
          <el-input v-model="polymer_info.filler_type">
          </el-input>
        </el-form-item>
        
        <el-form-item label="填充物形状">
          <el-input v-model="polymer_info.filler_shape">
          </el-input>
        </el-form-item>
        
        <el-form-item label="填充物含量">
          <el-input 
            type="number"
            min="0" 
            v-model="polymer_info.filler_percentage"
            @input="polymer_info.filler_percentage=checkNumberFormat(polymer_info.filler_percentage)"
          >
          </el-input>
        </el-form-item>
        
        <el-form-item label="密度(rho)">
          <el-input
            type="number"
            min="0" 
            v-model="polymer_info.filler_density"
            @input="polymer_info.filler_density=checkNumberFormat(polymer_info.filler_density)"
          >
          </el-input>
        </el-form-item>
        
        <el-form-item label="比热(Cp)">
          <el-input 
            type="number"
            min="0" 
            v-model="polymer_info.filler_specific_heat"
            @input="polymer_info.filler_specific_heat=checkNumberFormat(polymer_info.filler_specific_heat)"
          >
          </el-input>
        </el-form-item>
        
        <el-form-item label="比热导律(k)">
          <el-input 
            type="number"
            min="0" 
            v-model="polymer_info.filler_specific_thermal_conductivity"
            @input="polymer_info.filler_specific_thermal_conductivity=checkNumberFormat(polymer_info.filler_specific_thermal_conductivity)"
          >
          </el-input>
        </el-form-item>
        
        <el-divider content-position="center">
          <span style="color: blue">机械属性</span>
        </el-divider>
        
        <el-form-item label="E1">
          <el-input 
            type="number"
            min="0" 
            v-model="polymer_info.filler_E1"
            @input="polymer_info.filler_E1=checkNumberFormat(polymer_info.filler_E1)"
          >
            <span slot="suffix">MPa</span>
          </el-input>
        </el-form-item>
        
        <el-form-item label="E2">
          <el-input 
            type="number"
            min="0" 
            v-model="polymer_info.filler_E2"
            @input="polymer_info.filler_E2=checkNumberFormat(polymer_info.filler_E2)"
          >
            <span slot="suffix">MPa</span>
          </el-input>
        </el-form-item>
        
        <el-form-item label="v12">
          <el-input 
            type="number"
            min="0" 
            v-model="polymer_info.filler_v12"
            @input="polymer_info.filler_v12=checkNumberFormat(polymer_info.filler_v12)"
          >
          </el-input>
        </el-form-item>
        
        <el-form-item label="v23">
          <el-input 
            type="number"
            min="0" 
            v-model="polymer_info.filler_v23"
            @input="polymer_info.filler_v23=checkNumberFormat(polymer_info.filler_v23)"
          >
          </el-input>
        </el-form-item>
        
        <el-form-item label="G12">
          <el-input 
            type="number"
            min="0" 
            v-model="polymer_info.filler_G12"
            @input="polymer_info.filler_G12=checkNumberFormat(polymer_info.filler_G12)"
          >
            <span slot="suffix">MPa</span>
          </el-input>
        </el-form-item>
        
        <el-divider content-position="center">
          <span style="color: blue">热膨胀 (CTE) 数据系数</span>
        </el-divider>
        
        <el-form-item label="Alpha1">
          <el-input 
            type="number"
            min="0" 
            v-model="polymer_info.filler_Alpha1"
            @input="polymer_info.filler_Alpha1=checkNumberFormat(polymer_info.filler_Alpha1)"
          >
          </el-input>
        </el-form-item>
        
        <el-form-item label="Alpha2">
          <el-input 
            type="number"
            min="0" 
            v-model="polymer_info.filler_Alpha2"
            @input="polymer_info.filler_Alpha2=checkNumberFormat(polymer_info.filler_Alpha2)"
          >
          </el-input>
        </el-form-item>
        
        <el-divider content-position="center">
          <span style="color: blue">拉伸强度</span>
        </el-divider>
        
        <el-form-item label="平行纤维/填充物主轴方向" label-width="14rem">
          <el-input 
            type="number"
            min="0" 
            v-model="polymer_info.filler_horizontal_tensile_strength"
            @input="polymer_info.filler_horizontal_tensile_strength=checkNumberFormat(polymer_info.filler_horizontal_tensile_strength)"
          >
          </el-input>
        </el-form-item>
        
        <el-form-item label="垂直纤维/填充物主轴方向" label-width="14rem">
          <el-input 
            type="number"
            min="0" 
            v-model="polymer_info.filler_vertical_tensile_strength"
            @input="polymer_info.filler_vertical_tensile_strength=checkNumberFormat(polymer_info.filler_vertical_tensile_strength)"
          >
          </el-input>
        </el-form-item>
        
        <el-form-item label="纵横比（长度/直径）" label-width="14rem">
          <el-input 
            type="number"
            min="0" 
            v-model="polymer_info.filler_aspect_ratio"
            @input="polymer_info.filler_aspect_ratio=checkNumberFormat(polymer_info.filler_aspect_ratio)"
          >
          </el-input>
        </el-form-item>
      </el-card>

      <el-card v-if="this.id && polymer_info.company_id > 0">
        <div slot="header" class="clearfix">
          附件
        </div>

        <el-upload
          action="#"
          multiple
          :file-list="fileList"
          :http-request="uploadFile"
          :on-preview="handlePreview"
          :on-remove="handleRemove"
        >
          <el-button 
            size="small" 
            type="primary"
          >
            点击上传
          </el-button>
          <div slot="tip" class="el-upload__tip">
            上传材料相关文件，可支持png/jpg/pdf等格式
          </div>
        </el-upload>
      </el-card>
    </el-form>

    <div style="height:25px" />

    <div class="nextButton">
      <el-button
        v-if="viewType=='edit'" 
        type="success" 
        size="small"
        :loading="export_loading" 
        @click="exportPolymerToExcel" 
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
        v-if="id && polymer_info.company_id > 0 && pol_id"
        type="primary" 
        size="small"
        :loading="update_loading"
        @click="updatePolymerDetail" 
        :disabled="!$store.state.user.userinfo.permissions.includes('update_polymer')"
      >
        更  新
      </el-button>
      <el-button 
        v-else-if="polymer_info.company_id > 0"
        type="primary" 
        size="small"
        :loading="save_loading" 
        @click="savePolymerDetail"
        :disabled="!$store.state.user.userinfo.permissions.includes('add_polymer')"
      >
        保  存
      </el-button>
    </div>
  </div>
</template>

<script>
import { getOptions, polymerMethod, uploadFile, downloadFile, deleteFile, exportPolymer } from "@/api"
import { UserModule } from '@/store/modules/user'
import { getFullImageUrl, getFullReportUrl } from "@/utils/assert"
import { polymerAbbreivationOptions, dryingMethodOptions, densityRefer } from '@/utils/polymer-const'

export default {
  name: "PolymerCreate",
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
      default: null,
    },
    excelData:{
      type: Object,
      default: () => { }
    }
  },
  data() {
    return {
      polymer_info: {
        company_id: UserModule.company_id,
        id: null,
        
        series: null,
        abbreviation: null,
        trademark: null,
        manufacturer: null,
        category: null,
        data_source: null,
        data_status: null,
        internal_id: null,
        level_code: null,
        vendor_code: null,

        max_melt_temperature: null,
        min_melt_temperature: null,
        recommend_melt_temperature: null,
        max_mold_temperature: null,
        min_mold_temperature: null,
        recommend_mold_temperature: null,
        max_shear_linear_speed: null,
        min_shear_linear_speed: null,
        recommend_shear_linear_speed: null,
        recommend_injection_rate: null,
        degradation_temperature: null,
        ejection_temperature: null,
        max_sheer_rate: null,
        max_sheer_stress: null,
        recommend_back_pressure: null,
        barrel_residence_time: null,
        dry_temperature: null,
        dry_time: null,
        dry_method: null,

        viscosity_model: null,
        cross_WLF_n: null,
        cross_WLF_Tau: null,
        cross_WLF_D1: null,
        cross_WLF_D2: null,
        cross_WLF_D3: null,
        cross_WLF_A1: null,
        cross_WLF_A2: null,
        c1: null,
        c2: null,
        switch_temp: null,
        viscosity_index: null,
        MFR_temp: null,
        MFR_load: null,
        MFR_measure: null,

        melt_density: null,
        solid_density: null,
        Tait_pvT_b5: null,
        Tait_pvT_b6: null,
        Tait_pvT_b1m: null,
        Tait_pvT_b2m: null,
        Tait_pvT_b3m: null,
        Tait_pvT_b4m: null,
        Tait_pvT_b1s: null,
        Tait_pvT_b2s: null,
        Tait_pvT_b3s: null,
        Tait_pvT_b4s: null,
        Tait_pvT_b7: null,
        Tait_pvT_b8: null,
        Tait_pvT_b9: null,

        E1: null,
        E2: null,
        v12: null,
        v23: null,
        G12: null,
        Alpha1: null,
        Alpha2: null,

        average_horizontal_shrinkage: null,
        average_vertical_shrinkage: null,
        min_horizontal_shrinkage: null,
        max_horizontal_shrinkage: null,
        min_vertical_shrinkage: null,
        max_vertical_shrinkage: null,

        filler: null,
        filler_type: null,
        filler_shape: null,
        filler_percentage: null,
        filler_density: null,
        filler_specific_heat: null,
        filler_specific_thermal_conductivity: null,
        filler_E1: null,
        filler_E2: null,
        filler_v12: null,
        filler_v23: null,
        filler_G12: null,
        filler_Alpha1: null,
        filler_Alpha2: null,
        filler_horizontal_tensile_strength: null,
        filler_vertical_tensile_strength: null,
        filler_aspect_ratio: null,
      },
      fileList: [],
      rules: {
        abbreviation: [
          { required: true, message: '材料名称缩写为空!' }
        ],
        trademark: [
          { required: true, message: '材料牌号为空!' }
        ],
        // max_melt_temperature: [
        //   { required: true, message: '最大成型温度为空!' }
        // ],
        // min_melt_temperature: [
        //   { required: true, message: '最小成型温度为空!' }
        // ],
        recommend_melt_temperature: [
          { required: true, message: '推荐成型温度为空!' }
        ],
        // degradation_temperature: [
        //   { required: true, message: '塑料降解温度为空!' }
        // ],
        // max_mold_temperature: [
        //   { required: true, message: '最大模具温度为空!' }
        // ],
        // min_mold_temperature: [
        //   { required: true, message: '最小模具温度为空!' }
        // ],
        recommend_mold_temperature: [
          { required: true, message: '推荐模具温度为空!' }
        ],
        // ejection_temperature: [
        //   { required: true, message: '顶出温度为空!' }
        // ],
        // max_shear_linear_speed: [
        //   { required: true, message: '最大剪切线速度为空!' }
        // ],
        // min_shear_linear_speed: [
        //   { required: true, message: '最小剪切线速度为空!' }
        // ],
        recommend_shear_linear_speed: [
          { required: true, message: '推荐剪切线速度为空!' }
        ],
        // recommend_injection_rate: [
        //   { required: true, message: '推荐注射速率为空!' }
        // ],
        recommend_back_pressure: [
          { required: true, message: '推荐背压为空!' }
        ],
        melt_density: [
          { required: true, message: '熔融密度为空!' }
        ],
        solid_density: [
          { required: true, message: '固态密度为空!' }
        ],
      },
      export_loading: false,
      update_loading: false,
      save_loading: false,
      poly_abbreviation_options: polymerAbbreivationOptions,
      drying_method_options: dryingMethodOptions,
      pol_id: true,
    };
  },
  mounted() {
    this.getPolymerDetail()
  },
  methods: {
    setDensity(){
      if(!this.polymer_info.abbreviation){
        this.$message({message: '请先填写塑料简称', type: 'warning'})
      } else {
        const densityInfo = densityRefer.find(item => item.abbreviation === this.polymer_info.abbreviation);

        if (densityInfo) {
          this.polymer_info.solid_density = densityInfo.solid
          this.polymer_info.melt_density = densityInfo.melt
        } else {
          this.$message({message: '没有推荐的密度值', type: 'warning'})
        }
      }
    },
    queryPolymerAbbreviation(queryString, cb) {
      let polymer_type_list = this.poly_abbreviation_options
      // getOptions("abbreviation")
      // .then(res => {
      //   if (res.status === 0 && Array.isArray(res.data)) {
      //     for (let i = 0; i < res.data.length; ++i) {
      //       polymer_type_list.push({ "value": res.data[i] })
      //     }
      //   }
      // })
      var results = queryString ? polymer_type_list.filter(this.createStateFilter(queryString)) : polymer_type_list;
      cb(results);
    },
    createStateFilter(queryString) {
      return (state) => {
        return (state.value.toLowerCase().indexOf(queryString.toLowerCase()) === 0);
      };
    },
    exportPolymerToExcel() {
      exportPolymer(this.polymer_info)
      .then(res => {
        if (res.status === 0 && res.data.url) {
          this.$message({message: '导出成功。', type: 'success'})
          this.$emit('close')
          window.location.href = getFullReportUrl(res.data.url)
        }
      })
    },
    getPolymerDetail() {
      if (this.id) {
        polymerMethod.getDetail(this.id)
        .then((res) => {
          if (res.status === 0) {
            this.polymer_info = JSON.parse(JSON.stringify(res.data))
            if (this.viewType == "edit") {
              this.pol_id = true
            } else if (this.viewType == "copy") {
              this.polymer_info.id = null
              this.polymer_info.trademark = ""
              this.pol_id = false
            }

            downloadFile({
              "search_id": this.id,
              "search_type": "polymer"
            }).then(res => {
              if (res.status === 0) {
                this.fileList = []
                for (let i = 0; i < res.data.length; ++i) {
                  this.fileList.push({
                    id: res.data[i].id,
                    name: res.data[i].name,
                    url: getFullImageUrl(res.data[i].url)
                  })
                }
              }
            })
          }
        })
      }
      
      if (this.viewType == "upload" && this.excelData && JSON.stringify(this.excelData)!="{}") {
        this.polymer_info = this.excelData
        this.pol_id = false
      }
    },
    savePolymerDetail() {
      this.$refs["polymer_info"].validate((valid) => {
        if (valid) {
          this.savePolymer()
        } else {
            this.$confirm(`有些必填参数没有填,确认保存吗？`, '保存材料', {
              confirmButtonText: '确定',        
              cancelButtonText: '取消',
              type: 'warning'
            }).then(() => {
              this.savePolymer()
            }).catch(() => {
              this.$message({
                type: 'info',
                message: '已返回'
              })
            })  
          }
      })
    },
    savePolymer(){
      polymerMethod.add(this.polymer_info)
        .then((res) => {
          if (res.status === 0) {
            this.$message({ message: "材料信息新增成功！", type: "success" })
            this.$emit("close")
            this.$router.push('/polymer/list')
          }
        })
    },
    updatePolymerDetail() {
      this.$refs["polymer_info"].validate((valid) => {
        if (valid) {
          polymerMethod.edit(this.polymer_info, this.id)
          .then((res) => {
            if (res.status === 0) {
              this.$message({ message: "材料信息编辑成功！", type: "success" })
              this.$emit("close")
              this.$router.push('/polymer/list')
            }
          })
        }
      })
    },
    uploadFile(data) {
      let params = new FormData()
      params.append("file", data.file)
      params.append("search_id", this.id)
      params.append("search_type", "polymer")
      uploadFile(params).then( res => {
        if (res.status === 0) {
          this.$message({ message: "上传成功！", type: 'success' })
          this.fileList.push({
            id: res.data.id,
            name: res.data.name,
            url: getFullImageUrl(res.data.url)
          })
        } 
      })
    },
    handlePreview(file) {
      window.open(file.url)
    },
    handleRemove(file, fileList) {
      deleteFile(file.id)
      .then( res => {
        if (res.status === 0) {
          this.$message({ message: "删除成功！", type: "success" })
          this.fileList = fileList
        }
      })
    },
    resetView() {
      this.polymer_info = {
        company_id: UserModule.company_id,
        id: null,

        series: null,
        abbreviation: null,
        trademark: null,
        manufacturer: null,
        category: null,
        data_source: null,
        data_status: null,
        internal_id: null,
        level_code: null,
        vendor_code: null,

        max_melt_temperature: null,
        min_melt_temperature: null,
        recommend_melt_temperature: null,
        max_mold_temperature: null,
        min_mold_temperature: null,
        recommend_mold_temperature: null,
        max_shear_linear_speed: null,
        min_shear_linear_speed: null,
        recommend_shear_linear_speed: null,
        recommend_injection_rate: null,
        degradation_temperature: null,
        ejection_temperature: null,
        max_sheer_rate: null,
        max_sheer_stress: null,
        recommend_back_pressure: null,
        barrel_residence_time: null,
        dry_temperature: null,
        dry_time: null,
        dry_method: null,

        viscosity_model: null,
        cross_WLF_n: null,
        cross_WLF_Tau: null,
        cross_WLF_D1: null,
        cross_WLF_D2: null,
        cross_WLF_D3: null,
        cross_WLF_A1: null,
        cross_WLF_A2: null,
        c1: null,
        c2: null,
        switch_temp: null,
        viscosity_index: null,
        MFR_temp: null,
        MFR_load: null,
        MFR_measure: null,

        melt_density: null,
        solid_density: null,
        Tait_pvT_b5: null,
        Tait_pvT_b6: null,
        Tait_pvT_b1m: null,
        Tait_pvT_b2m: null,
        Tait_pvT_b3m: null,
        Tait_pvT_b4m: null,
        Tait_pvT_b1s: null,
        Tait_pvT_b2s: null,
        Tait_pvT_b3s: null,
        Tait_pvT_b4s: null,
        Tait_pvT_b7: null,
        Tait_pvT_b8: null,
        Tait_pvT_b9: null,

        E1: null,
        E2: null,
        v12: null,
        v23: null,
        G12: null,
        Alpha1: null,
        Alpha2: null,

        average_horizontal_shrinkage: null,
        average_vertical_shrinkage: null,
        min_horizontal_shrinkage: null,
        max_horizontal_shrinkage: null,
        min_vertical_shrinkage: null,
        max_vertical_shrinkage: null,

        filler: null,
        filler_type: null,
        filler_shape: null,
        filler_percentage: null,
        filler_density: null,
        filler_specific_heat: null,
        filler_specific_thermal_conductivity: null,
        filler_E1: null,
        filler_E2: null,
        filler_v12: null,
        filler_v23: null,
        filler_G12: null,
        filler_Alpha1: null,
        filler_Alpha2: null,
        filler_horizontal_tensile_strength: null,
        filler_vertical_tensile_strength: null,
        filler_aspect_ratio: null,
      }
    }
  },
  watch: {
    id() {
      if (this.id) {
        this.getPolymerDetail()
      }
    },
    excelData: {
      handler: function() {
        if (this.excelData) {
          this.polymer_info = this.excelData
        }
      },
      deep: true      
    }
  }
};
</script>

<style lang="scss" scoped>
  .button {
    position: fixed;
    // left: auto;
    right: 20px;
    bottom: 8px;
    // _position:absolute;
    z-index: 1000;
    font-size: 11px;
    line-height: 32px;
    height: 34px;
    // padding: 0px 15px 0px 15px;
    // width:666px;
    margin: 0px;
    .el-button {
      width: 8rem;
    }
  }
  .el-autocomplete {
    width: 10rem;
  }
  .el-input {
    width: 10rem;
  }
  .el-select {
    width: 10rem;
  }
</style>
