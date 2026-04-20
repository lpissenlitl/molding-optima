import { UserModule } from '@/store/modules/user';
import request from '@/utils/request';


class BaseRequest {
  url: string;
  constructor(url: string) {
    this.url = url
  }
  add(data: object) {
    return request({
      url: this.url,
      method: 'post',
      data
    })
  }
  getDetail(id: number) {
    return request({
      url: `${this.url}${id}/`,
      method: 'get',
    })
  }
  edit(data: object,id: number) {
    return request({
      url: `${this.url}${id}/`,
      method: 'put',
      data
    })
  }
  delete(id: number) {
    return request({
      url: `${this.url}${id}/`,
      method: 'delete',
    })
  }
  get(params: any) {
    return request({
      url: `${this.url}`,
      method: 'get',
      params
    })
  }
  multipleDel(params: any) {
    return request({
      url: this.url,
      method: 'delete',
      data: params
    })
  }
  multipleHandle(params: any) {
    return request({
      url: this.url,
      method: 'put',
      data: params
    })
  }
}


export var companiesMethod = new BaseRequest('/admin/company/') // 组织信息
export var departmentsMethod = new BaseRequest('/admin/department/') // 部门信息
export var usersMethod = new BaseRequest('/admin/users/') // 用户信息
export var managersMethod = new BaseRequest('/admin/managers/') // 组织管理员
export var rolesMethod = new BaseRequest('/admin/roles/') // 角色信息
export var permissionsMethod = new BaseRequest('/admin/permissions/') // 权限信息
export var groupTreeMethod = new BaseRequest('/admin/group_tree/') // 组织信息
export var userGoupMethod = new BaseRequest('/admin/user_group/') // 用户组织查看范围
export var groupMethod = new BaseRequest('/admin/group/') // 公司组织结构

// 工程数据
export var projectMethod =new BaseRequest('/molding/projects/') // 工程数据&工程列表


// 机器&材料
export var machineMethod = new BaseRequest(`/molding/machines/`) // 机器数据&机器列表
export var auxiliaryMethod = new BaseRequest(`/molding/auxiliaries/`) //辅机列表
export var polymerMethod = new BaseRequest('/molding/polymers/') // 塑料数据&塑料列表

// 增加下拉框选项
export var optionMethod = new BaseRequest('/molding/options/')

// 机器性能测试
export var machineTrialsMethod = new BaseRequest('/molding/machine_trials/')
export var loadSensitivityMethod = new BaseRequest('/molding/machine_trials/load_sensitivity/')  // 载荷敏感性测试
export var checkRingDynamicMethod = new BaseRequest('/molding/machine_trials/check_ring_dynamic/')  // 动态止逆阀测试
export var checkRingStaticMethod = new BaseRequest('/molding/machine_trials/check_ring_static/')  // 静态止逆阀测试
export var injectVeloLineMethod = new BaseRequest('/molding/machine_trials/inject_velocity_linearity/')  // 注射速度线性测试
export var stabilityAssessMethod = new BaseRequest('/molding/machine_trials/stability_assessment/')  // 稳定性评估测试
export var mouldBoardDeflectionMethod = new BaseRequest('/molding/machine_trials/mould_board_deflection/')  // 模版变形测试
export var screwWearMethod = new BaseRequest('/molding/machine_trials/screw_wear/')  // 螺杆磨损测试


// 根据模具id导出excel文件
export function exportMoldById(id: number) {
  return request({
    url: `/molding/export/mold/${id}/`,
    method: 'get'
  })
}

// 根据模具信息导出excel文件
export function exportMold(params: any) {
  return request({
    url: `/molding/export/mold/`,
    method: 'post',
    data: params
  })
}

// 根据约机表单导出excel文件
export function exportReservationForm(params: any) {
  return request({
    url: `/molding/export/reservation/form/`,
    method: 'post',
    data: params
  })
}

// 根据测试记录导出excel文件
export function exportTestingReport(data: object) {
  return request({
    url:`/molding/export/testing/report/`,
    method:'post',
    data
  })
}

// 导出测试zip
export function exportTestingZip(data: object) {
  return request({
    url: `/molding/export/testing/zip/`,
    method: 'post',
    data
  })
}

// 根据机器id导出excel文件
export function exportMachineById(id: number) {
  return request({
    url: `/molding/export/machine/${id}/`,
    method: 'get'
  })
}

// 根据机器信息导出excel文件
export function exportMachine(params: any) {
  return request({
    url: `/molding/export/machine/`,
    method: 'post',
    data: params
  })
}

// 根据塑料id导出excel文件
export function exportPolymerById(id: number) {
  return request({
    url: `/molding/export/polymer/${id}/`,
    method: 'get'
  })
}

// 根据塑料信息导出excel文件
export function exportPolymer(params: any) {
  return request({
    url: `/molding/export/polymer/`,
    method: 'post',
    data: params
  })
}

// 根据工艺id导出excel文件
export function exportProcessById(id: number) {
  return request({
    url: `/molding/export/process/${id}/`,
    method: 'get'
  })
}

// 根据注塑机测试导出Excel文件
export function exportMachineTrialReport(params: any) {
  return request({
    url: `/molding/export/machine_trial/`,
    method: 'post',
    data: params
  })
}

//导出模流对比文件
export function exportMoldFlowReport(params: any) {
  return request({
    url: `/molding/export/moldflow/`,
    method: 'post',
    data: params
  })
}

// 上传文件
export function uploadFile(params: any) {
  return request({
    url: `/molding/upload_file/`,
    method: 'post',
    headers: {'Content-Type': 'multipart/form-data'},
    data: params
  })
}

// 获取文件
export function downloadFile(params: any) {
  return request({
    url: `/molding/upload_file/`,
    method: 'get',
    params
  })
}

// 删除文件
export function deleteFile(id: number) {
  return request({
    url: `/molding/upload_file/${id}/`,
    method: 'delete'
  })
}

// 测试数据--复制测试
export function copyTesting(testingID: Number, params: any) {
  return request({
    url: `/molding/testing/${testingID}/`,
    method: 'post',
    data: params
  })
}
// 从excel读入模具
export function importMold(params: any) {
  return request({
    url: `/molding/upload/mold/`,
    method: 'post',
    headers: {'Content-Type': 'multipart/form-data'},
    data: params
  })
}
// 从excel读入机器
export function importMachine(params: any) {
  return request({
    url: `/molding/upload/machine/`,
    method: 'post',
    headers: {'Content-Type': 'multipart/form-data'},
    data: params
  })
}
// 从excel读入塑料
export function importPolymer(params: any) {
  return request({
    url: `/molding/upload/polymer/`,
    method: 'post',
    headers: {'Content-Type': 'multipart/form-data'},
    data: params
  })
}

// 从excel读入工艺
export function importProcess(params: any) {
  return request({
    url: `/molding/upload/process/`,
    method: 'post',
    headers: {'Content-Type': 'multipart/form-data'},
    data: params
  })
}

// 获取测试报告
export function getTestingReport(data:object) {
  return request({
    url:`/molding/testing/`,
    method:'put',
    data
  })
}

// 批量导入:塑料，机器等
export function importBatch(params: any, table_name:string, company_id: number){
  return request({
    url:`/molding/import/${table_name}/${company_id}/`,
    method: 'POST',
    headers: {'Content-Type': 'multipart/form-data'},
    data: params
  })
}
 
// 获取下拉列表
export function getOptions(optionName: string, params: any) {
  return request({
    url: `/molding/options/${optionName}/`,
    method: 'get',
    params
  })
}
//生成二维码
export function QRCodeProduce(params: any) {
  return request({
    url:'/molding/projects/',
    method: 'put',
    data: params
  })
}

// 制品工艺优化
export var processIndexMethod = new BaseRequest('/molding/process_index/') // 工艺索引（优化、记录...）
export var processRecordMethod = new BaseRequest('/molding/record_process/') // 工艺录入方法
export var processOptimizeMethod = new BaseRequest('/molding/optimize_process/') // 工艺优化详情
export var processQualifiedMethod = new BaseRequest('/molding/workshop_process/') // 合格工艺
export var processGuideMethod = new BaseRequest('/molding/guide_process/') // 工艺调机导航
export var ruleKeywordMethod =new BaseRequest('/molding/rule_keyword/') // 规则关键字
export var ruleDetailMethod =new BaseRequest('/molding/rule_method/') // 规则

export function newDefectMethod(params: any) {
  return request({
    url:'/molding/rule_keyword/',
    method: 'put',
    data: params
  })
}


export function getMesProcessMethod(params: any) {  // 读取MES的工艺参数
  return request({
    url: `/molding/mes_process/`,
    method: 'get',
    params
  })
}

export function setMesProcessMethod(params: any) {  // 通过MES设定工艺参数
  return request({
    url: `/molding/mes_process/`,
    method: 'post',
    data: params
  })
}
// 工艺参数初始化
export function initialProcessAlgorithm(params: any) {
  return request({
    url: `/molding/algorithm/initial/`,
    method: 'post',
    data: params
  })
}
// 工艺参数优化
export function optimizeProcessAlgorithm(params: any) {
  return request({
    url: `/molding/algorithm/optimize/`,
    method: 'post',
    data: params
  })
}

// 伊之密注塑机通讯
export function writeYizumiProcess(params: any) {
  return request({
    url: `/molding/communication/yizumi/`,
    method: 'post',
    data: params
  })
}

// 获取伊之密注塑机参数
export function getYizumiProcess(params: any) {
  return request({
    url: `/molding/communication/yizumi/`,
    method: 'get',
    params
  })
}

// 发送邮件
export function MailMethod(optionName:string, params: any){
  return request({
    url:`/molding/mail/${optionName}/`,
    method: 'POST',
    data: params
  })
}

// 导入moldflow的文件
export function importMoldflow(params: any, mold_no: string, id:number){
  return request({
    url:`/molding/moldflow/${mold_no}/${id}/`,
    method: 'POST',
    headers: {'Content-Type': 'multipart/form-data'},
    data: params
  })
}

// 保存模流分析
export var moldflowMethod = new BaseRequest(`/molding/moldflow/`) //模流相关

// 模流数据列表
export function getMoldflowListMethod(params:any){
  return request({
    url:`/molding/moldflow_list/`,
    method: 'GET',
    params
  })
}

// 获取moldflow的文件
export function getMoldflowMethod(params:any){
  return request({
    url:`/molding/moldflow/`,
    method: 'GET',
    params
  })
}
// 修改moldflow
export function setMoldflowMethod(params:any){
  return request({
    url:`/molding/moldflow/`,
    method: 'PUT',
    data:params
  })
}

// 获取规则流程图
export function getRuleFlowMethod(params:any){
  return request({
    url:`/molding/rule_flow/`,
    method: 'GET',
    params
  }) 
}
// 保存/更新规则流程图
export function setRuleFlowMethod(params:any){
  return request({
    url:`/molding/rule_flow/`,
    method: 'POST',
    data:params
  }) 
}

// 按照子规则库名称删除
export function deleteRule(params:any){
  return request({
    url:`/molding/rule_method_delete/${params}/`,
    method: 'DELETE'
  }) 
}

// 根据subrule_no导出Excel文件
export function exportRuleMethod(params: any) {
  return request({
    url: `/molding/export/rule/`,
    method: 'post',
    data: params
  })
}

//导出模流对比文件
export function importRuleMethod(params: any) {
  return request({
    url: `/molding/upload/rule/`,
    method: 'post',
    data: params
  })
}

// 设置 app-id
export function setUserAppID(data: object, id: number) {
  return request({
    url: `/admin/users/${id}/npauth/`,
    method: 'put',
    data
  })
}