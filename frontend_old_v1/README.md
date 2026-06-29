## 前端可视化项目
###代码地址
* https://github.com/hsmolding/HsMoldingWeb

### 线上测试地址
http://18.166.106.94:8200/login  
用户名 admin  
密码 Aa1111  

## 涉及技术点
* VUE基本框架，https://cn.vuejs.org/v2/guide/
* echarts绘图库，https://echarts.apache.org/examples/en/
* axios网络请求库， https://github.com/axios/axios
* 项目支持TS和JS，根据自己的经验选择合适的方式实现VUE实例
* UI框架element-UI，后期可以加入jquery-UI或者其他插件

* 项目框架参照地址， https://github.com/Armour/vue-typescript-admin-template
* 项目可参照demo， https://armour.github.io/vue-typescript-admin-template/#/dashboard

* vue typescript学习指南， https://armour.github.io/vue-typescript-admin-docs/zh/guide/#%E5%8A%9F%E8%83%BD

* babel，浏览器兼容， https://www.babeljs.cn/docs/index.html

* [eslint](https://eslint.org/)，代码格式检查工具  
可以在 .eslintrc.json 文件中修改检查规范，并自定义相关的代码规范，后面的代码书写需要遵循项目统一规范  
[eslint设置](https://eslint.org/docs/user-guide/getting-started)  
[typescript-eslint设置](https://github.com/typescript-eslint/typescript-eslint/blob/master/docs/getting-started/linting/README.md)
```js
//运行eslint检查代码
yarn eslint
```

## 开发工具
* webstorm/VSCode (推荐VSCode，不用每次激活麻烦)

## VSCode插件
* editorConfig， 项目中配置了editorconfig文件，使用该插件，会自动将editorconfig配置的选项覆盖掉settings配置


## 项目依赖安装
* 编译环境需要[node.js](https://nodejs.org/en/)
* 编译命令使用[npm](https://www.npmjs.com/)， 或者[yarn](https://yarnpkg.com/getting-started/install)

```js
yarn
或者
npm install
```

## 项目本地运行
* 如果搭建了本地后端python服务器，要链接本地后端服务，需要修改 vue.config.js 中的HOST 
```js
// 本地后端服务器地址
let HOST = 'http://127.0.0.1:8200'
// 线上后端服务器地址
let HOST = 'http://18.166.106.94:8200'
```

* 运行前项目
```
yarn serve
//或者
npm run serve
```

* 更新依赖库
```
yarn upgrade
```

## 一键发布
* 测试服
```js
yarn deploy_dev
//或者
npm run deploy_dev 
```

* 线上
```js
yarn deploy
//或者
npm run deploy 
```

* 本地APP
```js
yarn electron:serve
```


## 开发问题
* label-width= "auto"会引发异常，不要使用
https://github.com/ElemeFE/element/issues/15775

* const变量放入到特定的文件中

* 多制作组件，不要一个文件写太多内容


## 版本管理
历史版本：


当前版本：
