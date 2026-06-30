import { VuexModule, Module, MutationAction, Mutation, Action, getModule } from "vuex-module-decorators"
import { login, SSOLogin, logout, getInfo } from "@/api/login"
import { getToken, setToken, removeToken, setUserId, getUserId, removeUserId } from "@/utils/auth"
import store from "@/store"

export interface IUserState {
  id: number;
  company_id: number;
  company_name: string;
  company_code: string | null;
  organization_id: number;
  organization_name: string;
  username: string;  // 登录账号
  is_active: boolean;
  is_staff: boolean;
  is_superuser: boolean;
  is_tenant_admin: boolean;
  engineer_name: string; //名字
  roles: string[];
  groups: string[];
  permissions: string[];
}

@Module({ dynamic: true, store, name: "user" })
class User extends VuexModule implements IUserState {
  public id = 0
  public company_id = 0
  public company_name = "未知"
  public company_code = null
  public organization_id = 0
  public organization_name = "未知"
  public username = "游客"
  public is_active = false
  public is_staff = false
  public is_superuser = true
  public is_tenant_admin = false
  public engineer_name = "未知"
  public roles = []
  public groups = []
  public permissions = []

  @Action({ commit: "SET_DATA" })
  public setLoginData(data: any) {
    setUserId(data.id)
    setToken(data.token)
    return data
  }

  @Action({ commit: "SET_TOKEN" })
  public async FedLogOut() {
    removeUserId()
    return ""
  }
  
  @Action({ commit: "SET_SSOLogin" })
  public async GetSSOLogin(token: string | (string | null)[]) {
    let use_token = null
    if (Array.isArray(token) && token.length > 0) {
      use_token =  token[0]
    } else if (typeof token === "string") {
      use_token = token
    }

    if (use_token === null) { 
      throw Error("GetSSOLogin: token is null!") 
    }
    const { data } = await SSOLogin(use_token)
    setUserId(data.id)
    setToken(data.token)
    return data
  }

  @MutationAction({ mutate: [ 
    "id","company_id", "company_name", "company_code", "organization_id", "organization_name", 
    "username", "is_active", "is_staff", "is_superuser", "is_tenant_admin", 
    "engineer_name", "roles", "groups", "permissions" 
  ] })
  public async GetInfo() {
    const id = getUserId()
    if (id === undefined) {
      throw Error("GetInfo: token is undefined!")
    }
    const { data } = await getInfo()
    // console.log(data)
    if (data.username) {
      return {
        id: data.id,
        company_id: data.company_id,
        company_name: data.company_name,
        company_code: data.company_code,
        organization_id: data.organization_id,
        organization_name: data.organization_name,
        username: data.username,
        is_active: data.is_active,
        is_staff: data.is_staff,
        is_superuser: data.is_superuser,
        is_tenant_admin: data.is_tenant_admin,
        engineer_name: data.engineer_name,
        roles: data.roles,
        groups: data.groups,
        permissions: data.permissions,
      }
    } else {
      throw Error("GetInfo: roles must be a non-null array!")
    }
  }

  
  @MutationAction({ mutate: ["id", "roles"] })
  public async LogOut() {
    if (getToken() === undefined) {
      throw Error("LogOut: token is undefined!")
    }
    await logout()
    removeToken()
    removeUserId()
    return {
      id: null,
      roles: [],
    }
  }

  @Mutation
  private SET_DATA(data: any) {
    this.id = data.id
    this.company_id = data.company_id
    this.company_name = data.company_name
    this.organization_id = data.organization_id
    this.organization_name = data.organization_name
    this.username = data.username
    this.is_active = data.is_active
    this.is_staff = data.is_staff
    this.is_superuser = data.is_superuser
    this.is_tenant_admin = data.is_tenant_admin
    this.engineer_name = data.engineer_name
    this.roles = data.roles
    this.groups = data.groups
    this.permissions = data.permissions
  }
}

export const UserModule = getModule(User)
