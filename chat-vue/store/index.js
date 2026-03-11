import { createStore } from 'vuex'

export default createStore({
  state: {
    isPc: false,
    windowWidth: 0,
    windowHeight: 0,
    statusBarHeight: 0,
    navBarHeight: 44,
    userInfo: null,
    isLoggedIn: false,
    systemInfo: {}
  },
  mutations: {
    setDeviceInfo(state, info) {
      state.isPc = info.isPc;
      state.windowWidth = info.windowWidth;
      state.windowHeight = info.windowHeight;
    },
    setNavBarInfo(state, info) {
      state.statusBarHeight = info.statusBarHeight;
      state.navBarHeight = info.navBarHeight;
    },
    setUserInfo(state, userInfo) {
      state.userInfo = userInfo;
      state.isLoggedIn = !!userInfo;
    },
    setSystemInfo(state, info) {
      state.systemInfo = info;
    }
  },
  actions: {
    initApp({ commit }) {
      // 获取系统信息
      uni.getSystemInfo({
        success: (res) => {
          const isPc = res.windowWidth >= 768;
          
          commit('setDeviceInfo', {
            isPc,
            windowWidth: res.windowWidth,
            windowHeight: res.windowHeight
          });
          
          commit('setNavBarInfo', {
            statusBarHeight: res.statusBarHeight || 0,
            navBarHeight: (res.statusBarHeight || 0) + 44
          });
          
          commit('setSystemInfo', res);
        }
      });
      
      // 加载用户信息
      try {
        const userInfoStr = uni.getStorageSync('userInfo');
        if (userInfoStr) {
          const userInfo = typeof userInfoStr === 'string' ? JSON.parse(userInfoStr) : userInfoStr;
          commit('setUserInfo', userInfo);
        }
      } catch (e) {
        console.error('加载用户信息失败:', e);
      }
    }
  }
})
