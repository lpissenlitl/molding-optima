import Cookies from 'js-cookie';
import { VuexModule, Module, Mutation, Action, getModule } from 'vuex-module-decorators';
import store from '@/store';
import {saveLocalStorageObject, getLocalStorageObject, removeLocalStorage} from '@/storage/storage'

export enum DeviceType {
  Mobile,
  Desktop,
}

export interface IAppState {
  device: DeviceType
  sidebar: {
    opened: boolean
    withoutAnimation: boolean
  };
  language: string
  pageSizeArray: number[]
  customSetting: Object
}

@Module({ dynamic: true, store, name: 'app' })
class App extends VuexModule implements IAppState {
  public sidebar = {
    opened: Cookies.get('sidebarStatus') !== 'closed',
    withoutAnimation: false,
  };
  public device = DeviceType.Desktop
  public language = "cn"
  public customSetting = getLocalStorageObject('custom_setting') || {};

  @Action({ commit: 'TOGGLE_SIDEBAR' })
  public ToggleSideBar(withoutAnimation: boolean) {
    return withoutAnimation;
  }

  @Action({ commit: 'CLOSE_SIDEBAR' })
  public CloseSideBar(withoutAnimation: boolean) {
    return withoutAnimation;
  }

  @Action({ commit: 'TOGGLE_DEVICE' })
  public ToggleDevice(device: DeviceType) {
    return device;
  }

  @Action({ commit: 'SAVE_CUSTOM_SETTING' })
  public SaveCustomSetting(customSetting: any) {
    return customSetting
  }

  @Action({ commit: 'DEL_CUSTOM_SETTING' })
  public DelCustomSetting() {
    return 
  }

  @Mutation
  private TOGGLE_SIDEBAR(withoutAnimation: boolean) {
    if (this.sidebar.opened) {
      Cookies.set('sidebarStatus', 'closed');
    } else {
      Cookies.set('sidebarStatus', 'opened');
    }
    this.sidebar.opened = !this.sidebar.opened;
    this.sidebar.withoutAnimation = withoutAnimation;
  }

  @Mutation
  private CLOSE_SIDEBAR(withoutAnimation: boolean) {
    Cookies.set('sidebarStatus', 'closed');
    this.sidebar.opened = false;
    this.sidebar.withoutAnimation = withoutAnimation;
  }

  @Mutation
  private TOGGLE_DEVICE(device: DeviceType) {
    this.device = device;
  }

  @Mutation
  private SAVE_CUSTOM_SETTING(custom_setting: any) {
    this.customSetting = custom_setting
  } 

  @Mutation
  private DEL_CUSTOM_SETTING() {
    this.customSetting = {}
    removeLocalStorage("custom_setting")
  } 

  public pageSizeArray= [30,100,200];
}

export const AppModule = getModule(App);
