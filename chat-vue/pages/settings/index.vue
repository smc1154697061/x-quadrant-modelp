<template>
  <app-layout title="渡渡鸟设置">
    <view class="settings-container">
      <!-- 手机端登录入口 -->
      <view v-if="!isPc && !isLoggedIn" class="mobile-login-section">
        <view class="login-prompt">
          <text class="login-text">登录以使用更多功能</text>
          <button class="login-btn" @tap="showLoginDialog">立即登录</button>
        </view>
      </view>
      
      <!-- 手机端用户信息展示 -->
      <view v-if="!isPc && isLoggedIn" class="mobile-user-section">
        <view class="user-info">
          <text class="user-email">{{userInfo.email}}</text>
          <text class="user-status">已登录</text>
        </view>
      </view>
      
      <!-- 应用设置 -->
      <view class="section">
        <view class="section-title">渡渡鸟设置</view>
        <view class="setting-group">
          <view class="setting-item">
            <text class="setting-label">消息通知</text>
            <view class="setting-control">
              <switch :checked="notifications" @change="onNotificationsChange" color="#007bff" />
            </view>
          </view>
          
          <view class="setting-item">
            <text class="setting-label">自动保存对话历史</text>
            <view class="setting-control">
              <switch :checked="autoSave" @change="onAutoSaveChange" color="#007bff" />
            </view>
          </view>
        </view>
      </view>
      
      <!-- 登录弹窗组件 -->
      <login-dialog
        v-model:visible="loginVisible"
        @login-success="onLoginSuccess"
        @update:visible="onLoginVisibleChange"
      />
      
      <!-- 组织管理 -->
      <view class="section">
        <view class="section-title">组织管理</view>
        <view class="setting-group">
          <view class="setting-item clickable" @tap="navigateToOrganization">
            <text class="setting-label">我的组织</text>
            <view class="setting-value">
              <text class="icon-arrow">›</text>
            </view>
          </view>
        </view>
      </view>
      
      <!-- 关于 -->
      <view class="section">
        <view class="section-title">关于</view>
        <view class="setting-group">
          <view class="setting-item">
            <text class="setting-label">版本信息</text>
            <view class="setting-value">V1.0.0</view>
          </view>
          
          <view class="setting-item clickable" @tap="showUserAgreement">
            <text class="setting-label">渡渡鸟用户协议</text>
            <view class="setting-value">
              <text class="icon-arrow">›</text>
            </view>
          </view>
          
          <view class="setting-item clickable" @tap="showPrivacyPolicy">
            <text class="setting-label">渡渡鸟隐私政策</text>
            <view class="setting-value">
              <text class="icon-arrow">›</text>
            </view>
          </view>
        </view>
      </view>
      
      <!-- 退出登录按钮 -->
      <view class="btn-section">
        <button v-if="isLoggedIn" class="logout-btn" @tap="confirmLogout">退出登录</button>
      </view>
    </view>
  </app-layout>
</template>

<script>
import AppLayout from '../../components/layout/AppLayout.vue';
import LoginDialog from '../../components/user/LoginDialog.vue';

export default {
  components: {
    AppLayout,
    LoginDialog
  },
  data() {
    return {
      // 用户信息
      userInfo: {},
      
      // 应用设置
      notifications: true,
      autoSave: true,
      isPc: false,
      loginVisible: false
    };
  },
  computed: {
    isLoggedIn() {
      return !!this.userInfo && !!this.userInfo.email;
    }
  },
  onLoad() {
    // 加载保存的设置
    this.loadSettings();
    
    // 加载用户信息
    this.loadUserInfo();
    
    // 检测设备类型
    uni.getSystemInfo({
      success: (res) => {
        this.isPc = res.windowWidth >= 768;
      }
    });
    
    // 监听设备类型变化
    uni.$on('deviceTypeChange', (data) => {
      if (data) {
        this.isPc = data.isPc;
      }
    });
    
    // 监听用户信息更新
    uni.$on('userInfoUpdated', this.onUserInfoUpdated);
  },
  onUnload() {
    // 移除事件监听
    uni.$off('deviceTypeChange');
    uni.$off('userInfoUpdated', this.onUserInfoUpdated);
  },
  methods: {
    // 加载用户信息
    loadUserInfo() {
      try {
        const userInfo = uni.getStorageSync('userInfo');
        if (userInfo) {
          this.userInfo = typeof userInfo === 'string' ? JSON.parse(userInfo) : userInfo;
        }
      } catch (e) {
        console.error('解析用户信息失败:', e);
      }
    },
    
    // 用户信息更新事件处理
    onUserInfoUpdated(userInfo) {
      this.userInfo = userInfo || {};
    },
    
    // 跳转到其他页面
    navigateTo(url) {
      uni.navigateTo({
        url: url,
        fail: (err) => {
          console.error('导航失败:', err);
          uni.switchTab({
            url: url
          });
        }
      });
    },
    
    // 跳转到组织管理页面
    navigateToOrganization() {
      this.navigateTo('/pages/organization/index');
    },
    
    // 加载设置
    loadSettings() {
      try {
        // 应用设置
        const savedNotifications = uni.getStorageSync('notifications');
        if (savedNotifications !== '') {
          this.notifications = savedNotifications === 'true';
        }
        
        const savedAutoSave = uni.getStorageSync('autoSave');
        if (savedAutoSave !== '') {
          this.autoSave = savedAutoSave === 'true';
        }
      } catch (e) {
        console.error('加载设置失败:', e);
      }
    },
    
    // 保存设置
    saveSettings() {
      try {
        uni.setStorageSync('notifications', String(this.notifications));
        uni.setStorageSync('autoSave', String(this.autoSave));
      } catch (e) {
        console.error('保存设置失败:', e);
      }
    },
    
    // 切换消息通知
    onNotificationsChange(e) {
      this.notifications = e.detail.value;
      this.saveSettings();
    },
    
    // 切换自动保存
    onAutoSaveChange(e) {
      this.autoSave = e.detail.value;
      this.saveSettings();
    },
    
    // 显示用户协议
    showUserAgreement() {
      uni.showModal({
        title: '渡渡鸟用户协议',
        content: '用户协议内容...',
        showCancel: false
      });
    },
    
    // 显示隐私政策
    showPrivacyPolicy() {
      uni.showModal({
        title: '渡渡鸟隐私政策',
        content: '隐私政策内容...',
        showCancel: false
      });
    },
    
    // 确认退出登录
    confirmLogout() {
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
              this.userInfo = {};
              
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
    
    // 显示登录弹窗
    showLoginDialog() {
      this.loginVisible = true;
    },
    
    // 登录成功回调
    onLoginSuccess(userInfo) {
      this.userInfo = userInfo;
      this.loginVisible = false;
      
      uni.showToast({
        title: '登录成功',
        icon: 'success'
      });
      
      // 重新加载用户信息确保状态更新
      this.loadUserInfo();
    },
    
    // 处理登录弹窗可见性变化
    onLoginVisibleChange(visible) {
      this.loginVisible = visible;
    }
  }
};
</script>

<style>
.settings-container {
  padding: 30rpx;
  background-color: #f5f7fa;
  min-height: 100vh;
}

.section {
  background-color: #fff;
  border-radius: 16rpx;
  overflow: hidden;
  margin-bottom: 30rpx;
  box-shadow: 0 2rpx 20rpx rgba(0, 0, 0, 0.08);
}

.section-title {
  font-size: 28rpx;
  font-weight: 600;
  padding: 30rpx;
  color: #333;
  border-bottom: 2rpx solid #f0f0f0;
}

.setting-group {
  padding: 0 30rpx;
}

.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 30rpx 0;
  border-bottom: 2rpx solid #f0f0f0;
  min-height: 80rpx;
}

.setting-item:last-child {
  border-bottom: none;
}

.setting-label {
  font-size: 28rpx;
  color: #333;
  line-height: 1.5;
}

.setting-value {
  font-size: 28rpx;
  color: #666;
  display: flex;
  align-items: center;
}

.clickable {
  cursor: pointer;
}

.icon-arrow {
  font-size: 36rpx;
  color: #999;
  margin-left: 10rpx;
}

.btn-section {
  margin-top: 60rpx;
  padding: 0 30rpx;
}

.logout-btn {
  width: 100%;
  background-color: #f44336;
  color: #fff;
  border: none;
  border-radius: 16rpx;
  padding: 25rpx 0;
  font-size: 28rpx;
  line-height: 1.5;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 手机端登录入口样式 */
.mobile-login-section {
  background-color: #fff;
  border-radius: 16rpx;
  margin-bottom: 30rpx;
  padding: 30rpx;
  box-shadow: 0 2rpx 20rpx rgba(0, 0, 0, 0.08);
}

.login-prompt {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20rpx 0;
}

.login-text {
  font-size: 28rpx;
  color: #666;
  margin-bottom: 20rpx;
}

.login-btn {
  background-color: #007bff;
  color: #fff;
  font-size: 28rpx;
  padding: 15rpx 40rpx;
  border-radius: 30rpx;
  border: none;
  width: auto;
  min-width: 200rpx;
}

/* 手机端用户信息展示 */
.mobile-user-section {
  background-color: #fff;
  border-radius: 16rpx;
  margin-bottom: 30rpx;
  padding: 30rpx;
  box-shadow: 0 2rpx 20rpx rgba(0, 0, 0, 0.08);
}

.user-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20rpx 0;
}

.user-email {
  font-size: 28rpx;
  color: #333;
  font-weight: 500;
  margin-bottom: 10rpx;
}

.user-status {
  font-size: 24rpx;
  color: #28a745;
  background-color: rgba(40, 167, 69, 0.1);
  padding: 4rpx 16rpx;
  border-radius: 20rpx;
}

/* 响应式设计 */
@media screen and (min-width: 768px) {
  .settings-container {
    padding: 50rpx;
    max-width: 900rpx;
    margin: 0 auto;
  }
}
</style> 