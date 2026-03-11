<template>
  <view class="user-avatar">
    <image 
      :src="avatarUrl" 
      class="avatar" 
      @tap.stop="showLoginDialog"
    />
    
    <!-- 登录弹窗 -->
    <login-dialog
      v-model:visible="loginVisible"
      @login-success="onLoginSuccess"
      @update:visible="onLoginVisibleChange"
    />
  </view>
</template>

<script>
import LoginDialog from './LoginDialog.vue'

export default {
  components: {
    LoginDialog
  },
  data() {
    return {
      loginVisible: false,
      userInfo: null
    }
  },
  computed: {
    avatarUrl() {
      // 如果有用户信息，显示用户头像，否则显示默认头像
      return this.userInfo?.avatar || '/static/images/default-avatar.png'
    },
    isLoggedIn() {
      return !!this.userInfo && !!this.userInfo.id
    }
  },
  created() {
    // 获取存储的用户信息
    const userInfoStr = uni.getStorageSync('userInfo');
    if (userInfoStr) {
      try {
        this.userInfo = JSON.parse(userInfoStr);
      } catch (e) {
        console.error('解析用户信息失败:', e);
        this.userInfo = null;
      }
    }
  },
  methods: {
    showLoginDialog() {
      if (this.isLoggedIn) {
        // 已登录，显示用户菜单
        this.showUserMenu()
      } else {
        // 未登录，显示登录弹窗
        this.loginVisible = true
      }
    },
    
    onLoginSuccess(userInfo) {
      this.userInfo = userInfo;
      this.loginVisible = false;
      
      uni.showToast({
        title: '登录成功',
        icon: 'success'
      });
    },
    
    onLoginVisibleChange(visible) {
      this.loginVisible = visible;
    },
    
    showUserMenu() {
      // 简化菜单选项，只保留个人中心和退出登录两个选项
      uni.showActionSheet({
        itemList: ['个人中心', '退出登录'],
        success: (res) => {
          if (res.tapIndex === 0) {
            // 个人中心
            uni.navigateTo({
              url: '/pages/user/profile'
            })
          } else if (res.tapIndex === 1) {
            // 退出登录
            this.logout()
          }
        }
      })
    },
    
    logout() {
      uni.showModal({
        title: '确认退出',
        content: '确定要退出登录吗？',
        success: (res) => {
          if (res.confirm) {
            // 设置标志，表示正在退出登录
            uni.setStorageSync('isLoggingOut', 'true');
            
            // 清除登录状态
            uni.removeStorageSync('token');
            uni.removeStorageSync('userInfo');
            uni.removeStorageSync('token_backup');
            this.userInfo = null;
            
            // 通知其他组件用户已退出
            uni.$emit('userInfoUpdated', null);
            
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
          }
        }
      });
    }
  }
}
</script>

<style lang="scss">
.user-avatar {
  .avatar {
    width: 60rpx;
    height: 60rpx;
    border-radius: 50%;
  }
}
</style>
