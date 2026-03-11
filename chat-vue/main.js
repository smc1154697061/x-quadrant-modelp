import App from './App'
import { createSSRApp } from 'vue'
import { isAuthRequired, isLoggedIn, redirectToLogin, verifyToken } from './utils/auth.js'
import eventBus from './utils/eventBus.js'

// 全局关闭控制台输出
if (typeof console !== 'undefined') {
  console.log = () => {};
  console.info = () => {};
  console.debug = () => {};
  console.warn = () => {};
  console.error = () => {};
}

// 全局状态
const globalState = {
  statusBarHeight: 0,
  navBarHeight: 44,
  safeAreaBottom: 0,
  tabBarHeight: 50,
  isPc: false,
  contentHeight: '100vh',
  windowWidth: 0,
  windowHeight: 0,
  userInfo: null,
  isLoggedIn: false,
  sidebarWidth: 220,
  platformType: ''
};

// #ifndef VUE3
import Vue from 'vue'
import './uni.promisify.adaptor'
Vue.config.productionTip = false
App.mpType = 'app'
const app = new Vue({
  ...App
})
app.$mount()
// #endif

// #ifdef VUE3
export function createApp() {
  const app = createSSRApp(App);
  
  // 获取系统信息
  uni.getSystemInfo({
    success: (res) => {
      globalState.statusBarHeight = res.statusBarHeight || 20;
      globalState.navBarHeight = globalState.statusBarHeight + 44;
      globalState.safeAreaBottom = res.safeAreaInsets?.bottom || 0;
      globalState.isPc = res.windowWidth >= 768;
      globalState.windowWidth = res.windowWidth;
      globalState.windowHeight = res.windowHeight;
      
      // 同步到全局数据
      if (getApp()) {
        getApp().globalData = getApp().globalData || {};
        Object.assign(getApp().globalData, globalState);
      }
    }
  });
  
  // 设置全局属性
  app.config.globalProperties.$eventBus = eventBus;
  
  // 设置全局错误处理
  app.config.errorHandler = (err, vm, info) => {
    // 静默
  };
  
  return {
    app
  };
}
// #endif