import { VuexModule, Module, MutationAction, Mutation, Action, getModule } from 'vuex-module-decorators';
import { login, logout, getInfo } from '@/api/login';
import { getToken, setToken, removeToken, setUserId, getUserId, removeUserId } from '@/utils/auth';
import store from '@/store';

export interface IUserState {
  id: number;
  company_id: number;
  company: string;
  department_id: number;
  department: string;
  group_id: number;
  group: string;
  name: string;  // 登录账号
  engineer: string; //名字
  roles: string[];
  groups: string[];
  permissions: string[];
  userinfo: object;
}

@Module({ dynamic: true, store, name: 'user' })
class User extends VuexModule implements IUserState {
  public id = 0;
  public company_id = 0;
  public company = '';
  public department_id = 0;
  public department = '';
  public group_id = 0;
  public group = '';
  public name = '';
  public engineer = '';
  public roles = [];
  public groups = [];
  public permissions = [];
  public is_super = 0;  //是否是超级管理员
  public userinfo = {};

  @Action({ commit: 'SET_DATA'})
  public setLoginData(data: any) {
    setUserId(data.id);
    setToken(data.token)
    return data
  }

  @Action({ commit: 'SET_TOKEN' })
  public async FedLogOut() {
    removeUserId();
    return '';
  }

  @MutationAction({ mutate: [ 'company_id', 'company', 'department_id', 'department', 'group_id', 'group', 
  'name', 'engineer', 'roles', 'groups', 'permissions', 'is_super', 'userinfo' ] })
  public async GetInfo() {
    const id = getUserId();
    if (id === undefined) {
      throw Error('GetInfo: token is undefined!');
    }
    const { data } = await getInfo();
    if (data.name) {
      return {
        company_id: data.company_id,
        company: data.company,
        department_id: data.department_id,
        department: data.department,
        group_id: data.group_id,
        group: data.group,
        name: data.name,
        engineer: data.engineer,
        roles: data.roles,
        groups: data.groups,
        permissions: data.permissions,
        is_super: data.is_super,
        userinfo: data,
      };
    } else {
      throw Error('GetInfo: roles must be a non-null array!');
    }
  }

  @MutationAction({ mutate: [ 'id', 'roles' ] })
  public async LogOut() {
    // if (getToken() === undefined) {
    //   throw Error('LogOut: token is undefined!');
    // }
    // await logout();
    removeToken();
    removeUserId();
    return {
      id: null,
      roles: [],
    };
  }

  @Mutation
  private SET_DATA(data: any) {
    this.id = data.id
    this.company_id = data.company_id
    this.company = data.company
    this.department_id = data.department_id
    this.department = data.department
    this.group_id = data.group_id
    this.group = data.group
    this.name = data.name
    this.engineer = data.engineer
    this.roles = data.roles
    this.groups = data.groups
    this.permissions = data.permissions
    this.is_super = data.is_super
    this.userinfo = data
  }
}

export const UserModule = getModule(User);
