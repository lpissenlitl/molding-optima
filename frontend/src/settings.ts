interface ISettings {
  author: string // developer
  version: string // software current version
  user: string // current user
  title: 'molding-optima 智能工艺参数优化系统',
  showSettings: boolean // Controls settings panel display
  showTagsView: boolean // Controls tagsview display
  showSidebarLogo: boolean // Controls siderbar logo display
  fixedHeader: boolean // If true, will fix the header component
  errorLog: string[] // The env to enable the errorlog component, default 'production' only
  sidebarTextTheme: boolean // If true, will change active text color for sidebar based on theme
  devServerPort: number // Port number for webpack-dev-server
  mockServerPort: number // Port number for mock server
}

// You can customize below settings :)
const settings: ISettings = {
  author: 'molding',
  version: 'v5.0.0',
  user: 'molding-optima',
  title: 'molding-optima 智能工艺参数优化系统',
  showSettings: false,
  showTagsView: true,
  fixedHeader: true,
  showSidebarLogo: true,
  errorLog: ['production'],
  sidebarTextTheme: true,
  devServerPort: 9527,
  mockServerPort: 9528
}

export default settings
