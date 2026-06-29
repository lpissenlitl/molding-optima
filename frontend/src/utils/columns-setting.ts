
import { AppModule } from "@/store/modules/app"
import { UserModule } from "@/store/modules/user"

export function loadColumnsSetting(view_name: string) {
  const custom_setting = AppModule.customSetting
  const user_id = UserModule.id
  const key = `${view_name}_${user_id}`
  return custom_setting[key] || null
}

export function saveColumnsSetting(view_name: string, col_config: any) {
  const custom_setting = AppModule.customSetting
  const user_id = UserModule.id
  const key = `${view_name}_${user_id}`
  custom_setting[key] = col_config
  localStorage.setItem("custom_setting", JSON.stringify(custom_setting))
}