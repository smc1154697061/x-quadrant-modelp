<template>
  <app-layout title="个人中心">
    <view class="profile-container">
      <!-- 用户基本信息 -->
      <view class="user-card">
        <view class="user-top">
          <view class="user-avatar-large">
            <image :src="userInfo.avatar || '/static/images/user.png'" class="avatar-img-large"></image>
          </view>
          <view class="user-info">
            <text class="user-name-large">{{ displayName }}</text>
            <text v-if="userInfo.phone" class="user-phone">{{ formatPhone(userInfo.phone) }}</text>
          </view>
          
          <!-- 登录入口 - 未登录时显示 -->
          <view v-if="!isLoggedIn" class="login-entry" @tap="showLoginDialog">
            <text class="login-entry-text">登录/注册</text>
          </view>
        </view>
        
        <!-- 编辑资料按钮 - 已登录时显示 -->
        <button v-if="isLoggedIn" class="edit-btn" @tap="editUserInfo">编辑资料</button>
      </view>
      
      <!-- 个人信息表单（编辑模式） -->
      <view v-if="isEditing" class="edit-form">
        <view class="form-group">
          <text class="form-label">邮箱</text>
          <input class="form-input" v-model="editInfo.email" type="email" placeholder="请输入邮箱" disabled />
        </view>
        
        <view class="form-group">
          <text class="form-label">手机号</text>
          <input class="form-input" v-model="editInfo.phone" type="number" maxlength="11" placeholder="请输入手机号" />
        </view>
        
        <view class="form-actions">
          <button class="cancel-btn" @tap="cancelEdit">取消</button>
          <button class="save-btn" @tap="saveUserInfo">保存</button>
        </view>
      </view>
      
      <!-- 登录弹窗组件 -->
      <login-dialog
        v-model:visible="loginVisible"
        @login-success="onLoginSuccess"
        @update:visible="onLoginVisibleChange"
      />
      
      <!-- 退出登录按钮 -->
      <view class="logout-section" v-if="isLoggedIn">
        <button class="logout-btn" @tap="logout">退出登录</button>
      </view>
    </view>
  </app-layout>
</template>

<script>
import AppLayout from '../../components/layout/AppLayout.vue';
import LoginDialog from '../../components/user/LoginDialog.vue';
import api from '../../utils/api.js';
import { getPlatformType } from '../../utils/platform-adapter.js';

export default {
  components: {
    AppLayout,
    LoginDialog
  },
  data() {
    return {
      userInfo: null,
      editInfo: {
        email: '',
        phone: ''
      },
      isEditing: false,
      loginVisible: false,
      loading: false,
      isPc: false,
      showLoginDialog: false
    };
  },
  computed: {
    isLoggedIn() {
      return !!this.userInfo && !!this.userInfo.id;
    },
    displayName() {
      if (!this.userInfo) return '未登录';
      return this.userInfo.name || this.userInfo.email || '未知用户';
    },
    email() {
      return this.userInfo?.email || '未绑定邮箱';
    }
  },
  created() {
    this.checkLoginStatus();
  },
  onLoad() {
    this.checkLoginStatus();
    this.checkDeviceType();
  },
  onShow() {
    this.checkLoginStatus();
  },
  methods: {
    // 检查登录状态
    checkLoginStatus() {
      const token = uni.getStorageSync('token');
      const userInfoStr = uni.getStorageSync('userInfo');
      
      if (!token || !userInfoStr) {
        uni.reLaunch({
          url: '/pages/user/login/index'
        });
        return;
      }
      
      try {
        const userInfo = typeof userInfoStr === 'string' ? JSON.parse(userInfoStr) : userInfoStr;
        this.userInfo = userInfo;
      } catch (e) {
        console.error('解析用户信息失败:', e);
        this.userInfo = null;
        
        // 解析失败也跳转到登录页
        uni.reLaunch({
          url: '/pages/user/login/index'
        });
      }
    },
    
    // 检测设备类型
    checkDeviceType() {
      uni.getSystemInfo({
        success: (res) => {
          this.isPc = res.windowWidth >= 768;
        }
      });
    },
    
    // 退出登录
    logout() {
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
    
    // 格式化手机号
    formatPhone(phone) {
      if (!phone) return '';
      
      // 显示格式：前3位 + **** + 后4位
      if (phone.length === 11) {
        return phone.substring(0, 3) + '****' + phone.substring(7);
      }
      
      return phone;
    },
    
    // 编辑用户信息
    editUserInfo() {
      if (!this.isLoggedIn) {
        uni.showToast({
          title: '请先登录',
          icon: 'none'
        });
        return;
      }
      
      this.editInfo = { ...this.userInfo };
      this.isEditing = true;
    },
    
    // 取消编辑
    cancelEdit() {
      this.isEditing = false;
    },
    
    // 保存用户信息
    async saveUserInfo() {
      // 验证手机号格式
      if (this.editInfo.phone && !this.validatePhone(this.editInfo.phone)) {
        uni.showToast({
          title: '手机号格式不正确',
          icon: 'none'
        });
        return;
      }
      
      // 显示加载提示
      uni.showLoading({
        title: '保存中...'
      });
      
      try {
        // 发送到后端API保存信息
        const userId = this.userInfo.id;
        if (!userId) {
          throw new Error('用户ID不存在');
        }
        
        // 准备要更新的数据
        const updateData = {
          phone: this.editInfo.phone
        };
        
        // 调用后端API更新用户信息
        const response = await api.put(`/users/${userId}`, updateData);
        
        // 隐藏加载提示
        uni.hideLoading();
        
        // 检查响应状态
        if (response && response.code === '0000') {
          // 成功更新后端数据，更新本地存储
          this.userInfo = { ...this.userInfo, ...updateData };
          
          // 保存到本地存储
          uni.setStorageSync('userInfo', JSON.stringify(this.userInfo));
          
          // 发送用户信息更新事件
          uni.$emit('userInfoUpdated', this.userInfo);
          
          // 显示成功提示
          uni.showToast({
            title: '保存成功',
            icon: 'success'
          });
          
          this.isEditing = false;
        } else {
          // 显示错误信息
          uni.showToast({
            title: response?.message || '保存失败',
            icon: 'none'
          });
        }
      } catch (error) {
        // 隐藏加载提示
        uni.hideLoading();
        
        console.error('保存用户信息失败:', error);
        uni.showToast({
          title: '保存失败，请稍后重试',
          icon: 'none'
        });
      }
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
    },
    
    // 处理登录弹窗可见性变化
    onLoginVisibleChange(visible) {
      this.loginVisible = visible;
    },
    
    // 验证手机号
    validatePhone(phone) {
      // 简单的中国大陆手机号验证规则
      const phoneRegex = /^1[3-9]\d{9}$/;
      return phoneRegex.test(phone);
    }
  }
};
</script>

<style>
.profile-container {
  padding: 30rpx;
  background-color: #f5f7fa;
  min-height: 100vh;
}

.user-card {
  background-color: #fff;
  border-radius: 16rpx;
  padding: 30rpx;
  margin-bottom: 30rpx;
  box-shadow: 0 2rpx 20rpx rgba(0, 0, 0, 0.08);
}

.user-top {
  display: flex;
  align-items: center;
  margin-bottom: 30rpx;
  min-height: 140rpx;
}

.user-avatar-large {
  width: 120rpx;
  height: 120rpx;
  border-radius: 50%;
  overflow: hidden;
  border: 2rpx solid #eee;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.1);
}

.avatar-img-large {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.user-info {
  margin-left: 30rpx;
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.user-name-large {
  font-size: 34rpx;
  font-weight: 600;
  color: #333;
  display: block;
  margin-bottom: 8rpx;
  line-height: 1.5;
}

.user-email {
  font-size: 26rpx;
  color: #999;
  display: block;
  line-height: 1.5;
  margin-bottom: 4rpx;
}

.user-phone {
  font-size: 26rpx;
  color: #999;
  display: block;
  line-height: 1.5;
}

.login-entry {
  padding: 12rpx 24rpx;
  background-color: var(--primary-color, #007bff);
  border-radius: 30rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-left: 15rpx;
  height: 60rpx;
}

.login-entry-text {
  color: #fff;
  font-size: 26rpx;
  line-height: 1.5;
}

.edit-btn {
  width: 100%;
  background-color: #f5f5f5;
  color: #333;
  font-size: 28rpx;
  padding: 16rpx 0;
  border-radius: 8rpx;
  border: none;
  line-height: 1.5;
  display: flex;
  align-items: center;
  justify-content: center;
}

.edit-form {
  background-color: #fff;
  border-radius: 16rpx;
  padding: 30rpx;
  margin-bottom: 30rpx;
  box-shadow: 0 2rpx 20rpx rgba(0, 0, 0, 0.08);
}

.form-group {
  margin-bottom: 30rpx;
}

.form-label {
  font-size: 28rpx;
  color: #666;
  margin-bottom: 10rpx;
  display: block;
}

.form-input {
  width: 100%;
  height: 80rpx;
  border: 2rpx solid #ddd;
  border-radius: 10rpx;
  padding: 0 20rpx;
  font-size: 28rpx;
  background-color: #f9f9f9;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 20rpx;
  margin-top: 40rpx;
}

.cancel-btn, .save-btn {
  font-size: 28rpx;
  padding: 12rpx 30rpx;
  border-radius: 8rpx;
  line-height: 1.5;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 70rpx;
}

.cancel-btn {
  background-color: #f0f0f0;
  color: #666;
  border: 2rpx solid #ddd;
}

.save-btn {
  background-color: var(--primary-color, #007bff);
  color: #fff;
  border: none;
}

.logout-section {
  margin-top: 60rpx;
  padding: 0 30rpx;
}

.logout-btn {
  width: 100%;
  background-color: #f44336;
  color: #fff;
  font-size: 28rpx;
  padding: 20rpx 0;
  border-radius: 8rpx;
  text-align: center;
  border: none;
  line-height: 1.5;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 响应式设计 */
@media screen and (min-width: 768px) {
  .profile-container {
    padding: 50rpx;
    max-width: 900rpx;
    margin: 0 auto;
  }
  
  .user-card, .edit-form {
    padding: 40rpx;
  }
}
</style> 