
import { VuexModule, Module, Mutation, Action, getModule } from "vuex-module-decorators"
import store from "@/store"
import { createStorageKey, setLocalStorage, getLocalStorage, removeLocalStorage, clearLocalStorageByIncludes } from "@/utils/storage"


export interface TrialSession {
    id: number;
    mold_id: number;
    trial_version: string;
    test_plan: string;
    test_items: number;
    status: string;
    [key: string]: any;
}

export interface Mold {
    id: number;
    mold_no: string;
    trial_sessions: TrialSession[];
    [key: string]: any;
}

export interface TreeNode {
    label: string;
    node_key: string;
    node_type: string;
    mold_id: number;
    session_id: number;
    children: TreeNode[];
    [key: string]: any;
}

const STORAGE_KEY_MOLDS = createStorageKey("molds")
const STORAGE_KEY_CURRENT_MOLD = createStorageKey("selected_mold")
const STORAGE_KEY_CURRENT_TRIAL = createStorageKey("selected_trial_session")
const STORAGE_KEY_CURRENT_NODE = createStorageKey("selected_tree_node")

// State 接口
export interface IWorkflowState {
  molds: Mold[]; // 目前只存一个，类型为数组是考虑到未来拓展
  currentMold: Mold | null;
  currentTrialSession: TrialSession | null;
  currentTreeNode: TreeNode | null;
  trialViewStatus: boolean;
}

// 初始状态
const initialState: IWorkflowState = {
  molds: getLocalStorage<Mold[]>(STORAGE_KEY_MOLDS) || [],
  currentMold: getLocalStorage<Mold>(STORAGE_KEY_CURRENT_MOLD) || null,
  currentTrialSession: getLocalStorage<TrialSession>(STORAGE_KEY_CURRENT_TRIAL) || null,
  currentTreeNode: getLocalStorage<TreeNode>(STORAGE_KEY_CURRENT_NODE) || null,
  trialViewStatus: false
}


@Module({ dynamic: true, name: "workflow", store })
class Workflow extends VuexModule implements IWorkflowState {
  molds: Mold[] = initialState.molds
  currentMold: Mold | null = initialState.currentMold
  currentTrialSession: TrialSession | null = initialState.currentTrialSession
  currentTreeNode: TreeNode | null = initialState.currentTreeNode
  trialViewStatus: boolean = initialState.trialViewStatus


  @Action
  public setActiveMold(mold: Mold) {
    this.SET_ACTIVE_MOLD(mold)
  }

  @Mutation
  private SET_ACTIVE_MOLD(mold: Mold) {
    clearLocalStorageByIncludes("app")
    this.molds = [mold] // 只维护一套模具数据
    this.currentMold = mold
    setLocalStorage(STORAGE_KEY_MOLDS, this.molds)
    setLocalStorage(STORAGE_KEY_CURRENT_MOLD, mold)
    this.currentTrialSession = mold.trial_sessions.at(-1) || null
    setLocalStorage(STORAGE_KEY_CURRENT_TRIAL, this.currentTrialSession)
    this.currentTreeNode = null
    setLocalStorage(STORAGE_KEY_CURRENT_NODE, null)
  }

  @Action
  public removeMold(mold: Mold) {
    this.REMOVE_MOLD(mold)
  }

  @Mutation
  private REMOVE_MOLD(mold: Mold) {
    this.molds = this.molds.filter(item => item.id !== mold.id)
    setLocalStorage(STORAGE_KEY_MOLDS, this.molds)
    this.currentMold = this.molds.at(-1) || null
    setLocalStorage(STORAGE_KEY_CURRENT_MOLD, this.currentMold)
    this.currentTrialSession = this.currentMold?.trial_sessions.at(-1) || null
    setLocalStorage(STORAGE_KEY_CURRENT_TRIAL, this.currentTrialSession)
    this.currentTreeNode = null
    setLocalStorage(STORAGE_KEY_CURRENT_NODE, null)
  }

  @Action
  public setActiveTrialSession(trialSession: TrialSession) {
    this.SET_ACTIVE_TRIAL_SESSION(trialSession)
  }

  @Mutation
  private SET_ACTIVE_TRIAL_SESSION(trialSession: TrialSession) {
    this.currentTrialSession = trialSession
    setLocalStorage(STORAGE_KEY_CURRENT_TRIAL, trialSession)

    this.currentMold =  this.molds.filter(item => item.id === trialSession.mold_id)[0]
    this.currentMold.trial_sessions = this.currentMold.trial_sessions.map(item => item.id === trialSession.id ? trialSession : item)
    setLocalStorage(STORAGE_KEY_CURRENT_MOLD, this.currentMold)
    setLocalStorage(STORAGE_KEY_MOLDS, this.molds)
    this.currentTreeNode = null
    setLocalStorage(STORAGE_KEY_CURRENT_NODE, null)
  }

  @Action
  public async setActiveTreeNode(node: TreeNode) {
    this.SET_ACTIVE_TREE_NODE(node)
  }

  @Mutation
  private SET_ACTIVE_TREE_NODE(node: TreeNode) {
    this.currentTreeNode = node
    setLocalStorage(STORAGE_KEY_CURRENT_NODE, node)

    this.currentMold =  this.molds?.filter(item => item.id === node.mold_id)[0]
    setLocalStorage(STORAGE_KEY_CURRENT_MOLD, this.currentMold)

    this.currentTrialSession = this.currentMold?.trial_sessions?.filter(item => item.id === node.session_id)[0]
    setLocalStorage(STORAGE_KEY_CURRENT_TRIAL, this.currentTrialSession)
  }

  @Action
  public removeTrialSession(trialSession: TrialSession) {
    this.REMOVE_TRIAL_SESSION(trialSession)
  }

  @Mutation
  private REMOVE_TRIAL_SESSION(trialSession: TrialSession) {
    this.currentMold =  this.molds.filter(item => item.id === trialSession.mold_id)[0]
    this.currentMold.trial_sessions = this.currentMold.trial_sessions.filter(item => item.id !== trialSession.id)
    setLocalStorage(STORAGE_KEY_CURRENT_MOLD, this.currentMold)
    this.currentTrialSession = this.currentMold.trial_sessions.at(-1) || null
    setLocalStorage(STORAGE_KEY_CURRENT_TRIAL, this.currentTrialSession)
    this.currentTreeNode = null
    setLocalStorage(STORAGE_KEY_CURRENT_NODE, null)
    setLocalStorage(STORAGE_KEY_MOLDS, this.molds)
  }

  @Action
  public updateCurrentTrialSession(trialSession: TrialSession) {
    this.UPDATE_CURRENT_TRIAL_SESSION(trialSession)
  }

  @Mutation
  private UPDATE_CURRENT_TRIAL_SESSION(trialSession: TrialSession) {
    this.currentMold =  this.molds.filter(item => item.id === trialSession.mold_id)[0]
    this.currentMold.trial_sessions = this.currentMold.trial_sessions.map(item => item.id === trialSession.id ? trialSession : item)
    setLocalStorage(STORAGE_KEY_CURRENT_MOLD, this.currentMold)
    this.currentTrialSession = this.currentMold.trial_sessions.filter(item => item.id === trialSession.id)[0]
    setLocalStorage(STORAGE_KEY_CURRENT_TRIAL, this.currentTrialSession)
    this.molds = this.molds.map(item => item.id === trialSession.mold_id ? this.currentMold : item).filter((item): item is Mold => item != null)
    setLocalStorage(STORAGE_KEY_MOLDS, this.molds)
  }

  @Action
  public removeMoldCache(node: TreeNode) {
    this.REMOVE_MOLD_CACHE(node)
  }

  @Mutation
  private REMOVE_MOLD_CACHE(node: TreeNode) {
    const index = this.molds.findIndex(item => item.id === node.mold_id)
    if (index !== -1) {
      this.molds.splice(index, 1)
      removeLocalStorage(STORAGE_KEY_CURRENT_MOLD)
      removeLocalStorage(STORAGE_KEY_CURRENT_TRIAL)
      removeLocalStorage(STORAGE_KEY_CURRENT_NODE)
      setLocalStorage(STORAGE_KEY_MOLDS, this.molds)
    }
  }

  @Action
  public updateTrialViewStatus() {
    this.UPDATE_TRIAL_VIEW_STATUS()
  }

  @Mutation
  private UPDATE_TRIAL_VIEW_STATUS() {
    this.trialViewStatus = !this.trialViewStatus
  }
}


export const WorkflowModule = getModule(Workflow)