<template>
  <view class="app-header" :class="{ 'pc-header': isPc }">
    <!-- 状态栏占位 - 仅在移动端显示 -->
    <view v-if="!isPc" class="status-bar-placeholder" :style="{ height: statusBarHeight + 'px' }"></view>
    
    <!-- 标题栏 -->
    <view class="title-bar">
      <!-- 左侧区域：只保留标题，移除返回按钮 -->
      <view class="header-left">
        <text v-if="showTitle" class="header-title">{{ title }}</text>
      </view>
      
      <!-- 右侧用户区域 - 仅PC端显示 -->
      <view v-if="isPc" class="header-right">
        <!-- 用户头像 -->
        <view class="user-avatar" @tap="toggleMenu">
          <image 
            :src="userInfo?.avatar || '/static/images/user.png'" 
            class="avatar-image"
            :class="{'avatar-logged-in': isLoggedIn}"
          ></image>
        </view>
        
        <!-- 用户菜单 - 使用绝对定位 -->
        <div class="menu-container" v-if="isPc">
          <div class="user-menu" v-show="showUserMenu">
            <div class="menu-header">
              <span class="menu-welcome">你好，{{ userInfo?.email || '用户' }}</span>
            </div>
            <div class="menu-item" @tap="navigateTo('/pages/user/profile')">
              <span class="menu-icon">👤</span>
              <span class="menu-text">个人中心</span>
            </div>
            <div class="menu-item" @tap="navigateTo('/pages/settings/index')">
              <span class="menu-icon">⚙️</span>
              <span class="menu-text">系统设置</span>
            </div>
            <div class="menu-divider"></div>
            <div class="menu-item" @tap="logout">
              <span class="menu-icon">🚪</span>
              <span class="menu-text">退出登录</span>
            </div>
          </div>
        </div>
      </view>
    </view>
    
    <!-- 登录弹窗组件 -->
    <login-dialog
      v-model:visible="loginVisible"
      @login-success="onLoginSuccess"
      @update:visible="onLoginVisibleChange"
    />
  </view>
</template>

<script>
import LoginDialog from '../user/LoginDialog.vue'

export default {
  name: 'AppHeader',
  components: {
    LoginDialog
  },
  props: {
    title: {
      type: String,
      default: '智能对话平台'
    }
  },
  data() {
    return {
      showUserMenu: false,
      currentPath: '',
      isPc: false,
      userInfo: null,
      loginVisible: false,
      statusBarHeight: 0
    }
  },
  computed: {
    isLoggedIn() {
      return !!this.userInfo && !!this.userInfo.email && !!this.userInfo.email.trim();
    },
    showTitle() {
      return !!this.title && !!this.title.trim();
    }
  },
  created() {
    this.getCurrentPagePath();
    this.checkDeviceType();
    this.loadUserInfo();
    this.getStatusBarHeight();
    
    uni.$on('deviceTypeChange', this.handleDeviceTypeChange);
    uni.$on('userInfoUpdated', this.onUserInfoUpdated);
    uni.$on('pageChange', this.handlePageChange);
    
    // 监听页面显示事件
    uni.$on('onShow', this.onPageShow);
    
    // #ifdef H5
    document.addEventListener('click', this.handleDocumentClick);
    // #endif
  },
  beforeDestroy() {
    uni.$off('deviceTypeChange', this.handleDeviceTypeChange);
    uni.$off('userInfoUpdated', this.onUserInfoUpdated);
    uni.$off('pageChange', this.handlePageChange);
    uni.$off('onShow', this.onPageShow);
    
    // #ifdef H5
    document.removeEventListener('click', this.handleDocumentClick);
    // #endif
  },
  methods: {
    // 切换菜单显示状态
    toggleMenu(event) {
      if (event) event.stopPropagation();
      this.showUserMenu = !this.showUserMenu;
    },
    
    // 处理文档点击事件，关闭菜单
    handleDocumentClick(event) {
      // #ifdef H5
      // 如果菜单未显示，无需处理
      if (!this.showUserMenu) return;
      
      // 检查点击是否在头像或菜单内
      const avatar = event.target.closest('.user-avatar');
      const menu = event.target.closest('.user-menu');
      
      // 如果点击在头像或菜单外，关闭菜单
      if (!avatar && !menu) {
        this.showUserMenu = false;
      }
      // #endif
    },
    
    // 检测设备类型
    checkDeviceType() {
      uni.getSystemInfo({
        success: (res) => {
          this.isPc = res.windowWidth >= 768;
        }
      });
    },
    
    // 处理设备类型变化
    handleDeviceTypeChange(data) {
      if (data) {
        this.isPc = data.isPc;
      }
    },
    
    // 获取当前页面路径
    getCurrentPagePath() {
      try {
        const pages = getCurrentPages();
        if (pages.length > 0) {
          const currentPage = pages[pages.length - 1];
          const newPath = `/${currentPage.route}`;
          
          // 更新路径
          if (this.currentPath !== newPath) {
            this.currentPath = newPath;
          }
        } else {
          // #ifdef H5
          // 在H5环境下，尝试使用location.hash获取路径
          if (typeof window !== 'undefined' && window.location && window.location.hash) {
            const hash = window.location.hash;
            if (hash.startsWith('#/')) {
              this.currentPath = hash.substring(1);
            }
          }
          // #endif
        }
        
        return this.currentPath;
      } catch (e) {
        console.error('获取页面路径出错:', e);
        return '';
      }
    },
    
    // 处理页面切换事件
    handlePageChange(data) {
      if (data && data.path) {
        // 更新当前路径
        this.currentPath = data.path;
      }
      
      // 每次页面切换时，重新检查页面栈
      setTimeout(() => {
        const pages = getCurrentPages();
        
        if (pages.length > 0) {
          // 确保currentPath与实际页面一致
          const actualPath = `/${pages[pages.length - 1].route}`;
          if (this.currentPath !== actualPath) {
            this.currentPath = actualPath;
          }
        }
        
        // 强制更新视图
        this.$forceUpdate();
      }, 100);
    },
    
    // 加载用户信息
    loadUserInfo() {
      try {
        const userInfoStr = uni.getStorageSync('userInfo');
        if (userInfoStr) {
          this.userInfo = typeof userInfoStr === 'string' ? JSON.parse(userInfoStr) : userInfoStr;
        }
      } catch (e) {
        console.error('解析用户信息失败:', e);
      }
    },
    
    // 处理用户信息更新
    onUserInfoUpdated(userData) {
      this.userInfo = userData;
    },
    
    // 导航到指定页面
    navigateTo(url) {
      this.showUserMenu = false;
      uni.navigateTo({ url });
    },
    
    // 退出登录
    logout() {
      this.showUserMenu = false;
      
      uni.showModal({
        title: '确认退出',
        content: '确定要退出登录吗？',
        success: (res) => {
          if (res.confirm) {
            // 设置标志，表示正在退出登录
            uni.setStorageSync('isLoggingOut', 'true');
            
            // 显示加载提示
            uni.showLoading({
              title: '正在退出...',
              mask: true
            });
            
            // 清除登录状态
            setTimeout(() => {
              uni.removeStorageSync('token');
              uni.removeStorageSync('userInfo');
              uni.removeStorageSync('token_backup');
              this.userInfo = null;
              
              // 通知其他组件用户已退出
              uni.$emit('userInfoUpdated', null);
              
              uni.hideLoading();
              uni.showToast({
                title: '已退出登录',
                icon: 'success'
              });
              
              // 直接跳转到登录页面
              setTimeout(() => {
                uni.reLaunch({
                  url: '/pages/user/login/index',
                  complete: () => {
                    // 清除退出标志，确保在页面跳转完成后再清除
                    setTimeout(() => {
                      uni.removeStorageSync('isLoggingOut');
                    }, 500);
                  }
                });
              }, 1000);
            }, 500);
          }
        }
      });
    },
    
    // 获取状态栏高度
    getStatusBarHeight() {
      uni.getSystemInfo({
        success: (res) => {
          this.statusBarHeight = res.statusBarHeight || 0;
        }
      });
    },
    
    // 从LoginDialog接收登录成功的回调
    onLoginSuccess(userInfo) {
      // 确保数据格式正确
      if (typeof userInfo === 'string') {
        try {
          this.userInfo = JSON.parse(userInfo);
        } catch (e) {
          console.error('解析用户数据失败:', e);
          this.userInfo = userInfo;
        }
      } else {
        this.userInfo = userInfo;
      }
      
      // 确保存储到本地
      uni.setStorageSync('userInfo', JSON.stringify(this.userInfo));
      
      // 关闭登录对话框和用户菜单
      this.loginVisible = false;
      this.showUserMenu = false;
      
      // 发送全局事件通知其他组件
      uni.$emit('userInfoUpdated', this.userInfo);
    
      // 显示成功提示
      uni.showToast({
        title: '登录成功',
        icon: 'success'
      });
    },
    
    // 显示登录弹窗
    showLoginDialog(event) {
      // 防止点击冒泡
      if (event) {
        event.stopPropagation();
      }
      
      // 先确保用户菜单关闭
      this.showUserMenu = false;
      
      // 使用延时确保菜单先关闭再显示登录弹窗
      setTimeout(() => {
        this.loginVisible = true;
      }, 200);
    },
    
    // 处理登录弹窗可见性变化
    onLoginVisibleChange(visible) {
      this.loginVisible = visible;
      // 如果弹窗关闭，确保用户菜单也关闭
      if (!visible) {
        this.showUserMenu = false;
      }
    },
    
    // 页面显示事件处理
    onPageShow() {
      // 更新当前页面路径
      this.getCurrentPagePath();
      
      // 强制更新视图
      this.$forceUpdate();
      
      // 延时再次检查，解决某些平台上页面栈更新延迟问题
      setTimeout(() => {
        this.getCurrentPagePath();
        this.$forceUpdate();
      }, 200);
    }
  }
}
</script>

<style>
.app-header {
  width: 100%;
  position: fixed;
  top: 0;
  left: 0;
  z-index: 100;
  background-color: #fff;
  box-shadow: 0 1px 5px rgba(0,0,0,0.1);
}

/* PC端特殊样式 */
.pc-header {
  position: fixed;
  top: 0;
  left: var(--sidebar-width);
  width: calc(100% - var(--sidebar-width));
  z-index: 100;
}

.status-bar-placeholder {
  width: 100%;
  background-color: #fff;
}

.title-bar {
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 15px;
}

.header-left {
  display: flex;
  align-items: center;
}

.header-title {
  font-size: 16px;
  font-weight: bold;
}

.header-right {
  display: flex;
  align-items: center;
  position: relative;
}

.user-avatar {
  width: 30px;
  height: 30px;
  border-radius: 15px;
  overflow: hidden;
  cursor: pointer;
  z-index: 102;
}

.avatar-image {
  width: 100%;
  height: 100%;
  border-radius: 50%;
}

.avatar-logged-in {
  border: 2px solid #007AFF;
}

.menu-container {
  position: relative;
}

.user-menu {
  position: absolute;
  top: 40px;
  right: 0;
  width: 180px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.15);
  z-index: 999;
  overflow: hidden;
}

/* 确保菜单在PC端正确显示 */
@media screen and (min-width: 768px) {
  .user-menu {
    display: block;
  }
}

.menu-header {
  padding: 10px 15px;
  background-color: #f5f7fa;
  border-bottom: 1px solid #eee;
}

.menu-welcome {
  font-size: 14px;
  color: #333;
  font-weight: bold;
}

.menu-item {
  display: flex;
  align-items: center;
  padding: 12px 15px;
  cursor: pointer;
  pointer-events: auto;
}

.menu-item:hover {
  background-color: #f5f7fa;
}

.menu-icon {
  margin-right: 10px;
  font-size: 16px;
}

.menu-text {
  font-size: 14px;
  color: #333;
}

.menu-divider {
  height: 1px;
  background-color: #eee;
  margin: 5px 0;
}
</style> 