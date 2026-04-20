
import { VuexModule, Module, Mutation, Action, getModule } from 'vuex-module-decorators';
import store from '@/store';
import {saveLocalStorageObject, getLocalStorageObject, removeLocalStorage} from '@/storage/storage'


export interface IProjectsInfo {
  projects: any | [];
  selectedProject: any | null;
  selectedTesting: any | null;
  selectedNode: object | null;
  testingViewStatus: boolean; // 与testing相关的状态，不要关注具体的值，每一次改变，通知到相关的页面改变即可
}

// 查询 projects （数组）
function getProjects() {
  let projects = getLocalStorageObject('list_of_project')
  if (projects) {
    return projects
  } else {
    return []
  }
}

// 查询 project 在 list 中的 index
function getSelectedProjectIndexById(project_list: any, project_id: Number){
  for(let i = 0; i < project_list.length; ++i) {
    if(project_id == project_list[i].mold_info.id) {
      return i;
    }
  }
  return -1;
}

// 查询 testing 在 project 中的 index
function getSelectedTestingIndexById(project: any, testing_id: Number){
  for(let i = 0; i < project.testing_list.length; ++i) {
    if(testing_id == project.testing_list[i].id) {
      return i;
    }
  }
  return -1;
}

// 查询 selected_project 在 list 中的 index
export function getSelectedProjectById(project_list: any, project_id: Number){
  let index = getSelectedProjectIndexById(project_list, project_id)
  return index >= 0? project_list[index] : null
}

@Module({ dynamic: true, store, name: 'projects' })
class ProjectsInfo extends VuexModule implements IProjectsInfo {
  projects = getProjects() || [];
  selectedProject = null || getLocalStorageObject('selected_project')
  selectedTesting = null || getLocalStorageObject('selected_testing');
  selectedNode = null || getLocalStorageObject('selected_node');
  testingViewStatus = false;

  @Action({ commit: 'PUSH_PROJECT' })
  public PushProject(project: object) {
    return project;
  }

  @Action({ commit: 'UPDATE_PROJECT'})
  public UpdateProject(project: object) {
    return project;
  }

  @Action({ commit: 'REMOVE_PROJECT'})
  public RemoveProject(project: object) {
    return project;
  }

  @Action({ commit: 'SET_SELECTED_PROJECT' })
  public SetSelectedProject(selectedProject: object) {
    return selectedProject;
  }

  @Action({ commit: 'PUSH_TESTING' })
  public PushTesting(testing: any) {
    return testing
  }

  @Action({ commit: 'UPDATE_TESTING' })
  public UpdateTesting(testing: any) {
    return testing
  }

  @Action({ commit: 'REMOVE_TESTING' })
  public RemoveTesting(testing: any) {
    return testing
  }

  @Action({ commit: 'SET_SELECTED_TESTING' })
  public SetSelectedTesting(selectedTesting: any) {
    this.SET_SELECTED_TESTING(selectedTesting);
    return selectedTesting;
  }

  @Action({ commit: 'SET_SELECTED_NODE' })
  public SetSelectedNode(selectedNode: any) {
    return selectedNode;
  }

  @Action({ commit: 'CLEAR_LOCALSTORAGE'})
  public ClearLocalstorage() {
    return
  }

  @Mutation
  private PUSH_PROJECT(project: any) {
    // 限制工程数量，只显示1个
    // 清空历史数据
    while (localStorage.length > 0) {
      removeLocalStorage(String(localStorage.key(0)))
    }
    this.projects = []
    this.selectedProject = null
    this.selectedTesting = null
    this.selectedNode = null

    let projectIndex = getSelectedProjectIndexById(this.projects, project.id);
    if (projectIndex < 0) {
      // 添加工程数据
      this.projects.push(project);
      this.selectedProject = project
      this.selectedTesting = null
      this.selectedNode = null
      saveLocalStorageObject('list_of_project', this.projects)
      saveLocalStorageObject('selected_project', this.selectedProject)
      removeLocalStorage('selected_testing')
      removeLocalStorage('selected_node')
    }
  }

  @Mutation
  private UPDATE_PROJECT(project: any) {
    let projectIndex = getSelectedProjectIndexById(this.projects, project.id);
    if(projectIndex >= 0) {
      this.projects[projectIndex] = project
      this.selectedProject = project
      this.selectedTesting = null
      this.selectedNode = null
      saveLocalStorageObject('list_of_project', this.projects)
      saveLocalStorageObject('selected_project', this.selectedProject)
      removeLocalStorage('selected_testing')
      removeLocalStorage('selected_node')
    }
  }

  @Mutation
  private REMOVE_PROJECT(project: any) {
    let projectIndex = getSelectedProjectIndexById(this.projects, project.id);
    if(projectIndex >= 0) {
      // 清空历史数据，保留个人配置
      while (localStorage.length > 1) {
        if (String(localStorage.key(0)) !== "custom_setting") {
          removeLocalStorage(String(localStorage.key(0)))
        }
      }
      this.projects.splice(projectIndex, 1)
      this.selectedProject = null
      this.selectedTesting = null
      this.selectedNode = null
      saveLocalStorageObject('list_of_project', this.projects)
    }
  }

  @Mutation
  private SET_SELECTED_PROJECT(project: any) {
    let projectIndex = getSelectedProjectIndexById(this.projects, project.id);
    if(projectIndex >= 0) {
      this.selectedProject = project
      this.selectedTesting = null
      this.selectedNode = null
      saveLocalStorageObject('selected_project', this.selectedProject)
      removeLocalStorage('selected_testing')
      removeLocalStorage('selected_node')
    }
  }

  @Mutation
  public PUSH_TESTING(testing: any) {
    let projectIndex = getSelectedProjectIndexById(this.projects, testing.project_id);
    if (projectIndex >= 0) {
      this.projects[projectIndex].testing_list.push(testing)
      this.selectedProject = this.projects[projectIndex]
      this.selectedTesting = testing
      this.selectedNode = null
      saveLocalStorageObject('list_of_project', this.projects)
      saveLocalStorageObject('selected_project', this.selectedProject)
      saveLocalStorageObject('selected_testing', this.selectedTesting)
      removeLocalStorage('selected_node')
    }
  }

  @Mutation
  public UPDATE_TESTING(testing: any) {
    let projectIndex = getSelectedProjectIndexById(this.projects, testing.project_id);
    if (projectIndex >= 0) {
      let testingIndex = getSelectedTestingIndexById(this.projects[projectIndex], testing.id)

      if (testingIndex >= 0) {
        this.projects[projectIndex].testing_list[testingIndex] = testing
        this.selectedProject = this.projects[projectIndex]
        this.selectedTesting = testing
        this.selectedNode = null
        saveLocalStorageObject('list_of_project', this.projects)
        saveLocalStorageObject('selected_project', this.selectedProject)
        saveLocalStorageObject('selected_testing', this.selectedTesting)
        removeLocalStorage('selected_node')
      }
    }
  }

  @Mutation
  public REMOVE_TESTING(testing: any) {
    let projectIndex = getSelectedProjectIndexById(this.projects, testing.project_id);
    if(projectIndex >= 0) {
      const index = this.projects[projectIndex].testing_list.findIndex((d: any) => d.id === testing.id);
      this.projects[projectIndex].testing_list.splice(index, 1);
      this.selectedProject = this.projects[projectIndex]
      this.selectedTesting = null
      this.selectedNode = null
      saveLocalStorageObject('list_of_project', this.projects)
      saveLocalStorageObject('selected_project', this.selectedProject)
      removeLocalStorage('selected_testing')
      removeLocalStorage('selected_node')
    }
  }

  @Mutation
  private SET_SELECTED_TESTING(testing: any) {
    this.selectedTesting = testing
    let projectIndex = getSelectedProjectIndexById(this.projects, testing.project_id);
    if (projectIndex >= 0) {
      let testingIndex = getSelectedTestingIndexById(this.projects[projectIndex], testing.id)

      if (testingIndex >= 0) {
        this.projects[projectIndex].testing_list[testingIndex] = testing
        this.selectedProject = this.projects[projectIndex]
        this.selectedTesting = testing
        this.selectedNode = null
        saveLocalStorageObject('list_of_project', this.projects)
        saveLocalStorageObject('selected_project', this.selectedProject)
        saveLocalStorageObject('selected_testing', this.selectedTesting)
        removeLocalStorage('selected_node')
      }
    }
  }

  @Mutation
  private SET_SELECTED_NODE(node: any) {
    this.selectedNode = node
    if(node == null) {
      removeLocalStorage('selected_node')
    } else {
      let projectIndex = getSelectedProjectIndexById(this.projects, node.proID);
        if (projectIndex >= 0) {
        let testingIndex = getSelectedTestingIndexById(this.projects[projectIndex], node.testingID)

        if (testingIndex >= 0) {
          this.selectedProject = this.projects[projectIndex]
          this.selectedTesting = this.projects[projectIndex].testing_list[testingIndex]
          this.selectedNode = node
          saveLocalStorageObject('list_of_project', this.projects)
          saveLocalStorageObject('selected_project', this.selectedProject)
          saveLocalStorageObject('selected_testing', this.selectedTesting)
          saveLocalStorageObject('selected_node', this.selectedNode)
        }
      }
    }
  }

  @Mutation
  private CLEAR_LOCALSTORAGE() {
    // 清空历史数据，保留个人配置
    while (localStorage.length > 1) {
      if (String(localStorage.key(0)) !== "custom_setting") {
        removeLocalStorage(String(localStorage.key(0)))
      }
    }
  }

  @Mutation
  private UPDATE_PROJECT_FOR_TESTING(selectedTesting: any) {
    for(let i = 0; i < this.projects.length; ++i) {
      let testingList = this.projects[i].testing_list;
      for (let j = 0; j < testingList.length; ++j) {
        let testing = testingList[j]
        if (testing.id == selectedTesting.id) {
          testingList[j] = Object.assign({}, selectedTesting)
          saveLocalStorageObject('list_of_project', this.projects)
          return
        }
      }
    }
  }

  @Mutation
  private UPDATE_TESTING_VIEW_STATUS() {
    this.testingViewStatus = !this.testingViewStatus
  }
}

export const ProjectsInfoModule = getModule(ProjectsInfo);
