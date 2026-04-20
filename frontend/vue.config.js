
const debug = process.env.NODE_ENV !== 'production'

let HOST = 'http://127.0.0.1:8200'

module.exports = {
  productionSourceMap: false,
  pluginOptions: {
    electronBuilder: {
      chainWebpackRendererProcess(config) {
        config.plugins.delete('workbox')
        config.plugins.delete('pwa')
      },
      //安装包图标
      builderOptions:{
        win: {
          icon:'./public/app.ico'
        }
      }
    }
  },
  configureWebpack: config => {
    if (debug) { // 开发环境配置
      config.devtool = 'source-map'
    }
  },
  devServer: {
    open: true,
    proxy: {
      '/admin':{target:HOST},
      '/molding':{target:HOST},
      '/storage':{target:HOST},
      '/media':{target:HOST},
      '/report':{target:HOST},
    }
  },
  pwa: {
    name: 'vue-typescript-admin-template',
    iconPaths: {
      favicon32: 'logo.ico',
      favicon16: 'logo.ico',
      appleTouchIcon: 'logo.ico',
      maskIcon: 'logo.ico',
      msTileImage: 'logo.ico',
    }
  }
}
