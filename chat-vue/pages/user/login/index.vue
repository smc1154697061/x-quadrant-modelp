<template>
  <view class="login-page">
    <view class="login-container">
      <view class="login-header">
        <image class="logo" src="/static/images/logo.png" mode="aspectFit"></image>
        <text class="title">渡渡鸟AI助手</text>
        <text class="subtitle">使用邮箱验证码登录</text>
      </view>
      
      <view class="login-form">
        <view class="input-group">
          <text class="input-label">邮箱</text>
          <input 
            type="text" 
            v-model="email" 
            placeholder="请输入邮箱"
            class="input"
          />
        </view>
        
        <view class="input-group verification-group">
          <text class="input-label">验证码</text>
          <view class="code-input-wrapper">
            <input 
              type="text" 
              v-model="code" 
              placeholder="请输入验证码"
              class="input"
            />
            <button 
              @tap="sendCode" 
              :disabled="isSending"
              class="send-code-btn"
            >
              <text>{{ isSending ? `${countdown}s后重试` : '获取验证码' }}</text>
            </button>
          </view>
        </view>
        
        <view class="tips-text">
          <text>* 未注册用户将自动创建账号</text>
        </view>
        
        <button @tap="handleSubmit" class="submit-btn" :disabled="isLoading">
          <text v-if="isLoading">登录中...</text>
          <text v-else>登录/注册</text>
        </button>
      </view>
    </view>
  </view>
</template>

<script>
import api from '../../../utils/api.js';
import { safeSetStorage, safeGetStorage } from '../../../utils/platform-adapter.js';

export default {
  data() {
    return {
      email: '',
      code: '',
      isSending: false,
      countdown: 60,
      isLoading: false,
      timer: null,
      redirectUrl: '/pages/knowledge-base/index' // 默认跳转页面
    }
  },
  onLoad(options) {
    // 清除退出应用标记
    uni.removeStorageSync('isExitingApp');
    
    // 检查是否是从退出登录跳转过来的
    const isLoggingOut = uni.getStorageSync('isLoggingOut');
    if (isLoggingOut === 'true') {
      // 如果是从退出登录跳转过来，不做自动跳转
      // 清除标记
      uni.removeStorageSync('isLoggingOut');
      return;
    }
    
    // 获取重定向URL
    try {
      const redirectUrl = safeGetStorage('redirectUrl');
      if (redirectUrl) {
        this.redirectUrl = redirectUrl;
      }
    } catch (e) {
      console.error('获取重定向URL失败:', e);
    }
    
    // 检查是否已登录
    this.checkLoginStatus();
  },
  onUnload() {
    // 清除定时器
    if (this.timer) {
      clearInterval(this.timer);
    }
  },
  methods: {
    // 检查登录状态
    checkLoginStatus() {
      const token = uni.getStorageSync('token');
      const userInfo = uni.getStorageSync('userInfo');
      
      if (token && userInfo) {
        // 已登录则跳转到目标页面
        uni.reLaunch({
          url: this.redirectUrl
        });
      }
    },
    
    // 发送验证码
    async sendCode() {
      if (!this.email) {
        uni.showToast({
          title: '请输入邮箱',
          icon: 'none'
        });
        return;
      }
      
      // 验证邮箱格式
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(this.email)) {
        uni.showToast({
          title: '请输入正确的邮箱格式',
          icon: 'none'
        });
        return;
      }
      
      if (this.isSending) return;
      
      try {
        this.isSending = true;
        
        // 显示加载中提示
        uni.showLoading({
          title: '发送中...'
        });
        
        // 使用API服务发送请求
        const response = await api.post('/auth/send-code', { email: this.email }, false);
        
        // 隐藏加载提示
        uni.hideLoading();
        
        if (response && (response.code === '0000' || response.code === 'SUCCESS')) {
          uni.showToast({
            title: '验证码已发送',
            icon: 'success'
          });
          this.startCountdown();
        } else {
          uni.showToast({
            title: response?.message || '发送失败',
            icon: 'none'
          });
          this.isSending = false;
        }
      } catch (error) {
        // 隐藏加载提示
        uni.hideLoading();
        
        console.error('发送验证码失败:', error);
        
        uni.showToast({
          title: '发送失败，请重试',
          icon: 'none'
        });
        
        this.isSending = false;
      }
    },
    
    // 开始倒计时
    startCountdown() {
      this.countdown = 60;
      
      if (this.timer) {
        clearInterval(this.timer);
      }
      
      this.timer = setInterval(() => {
        if (this.countdown > 0) {
          this.countdown--;
        } else {
          this.isSending = false;
          clearInterval(this.timer);
        }
      }, 1000);
    },
    
    // 处理登录/注册提交
    async handleSubmit() {
      if (!this.email) {
        uni.showToast({
          title: '请输入邮箱',
          icon: 'none'
        });
        return;
      }
      
      // 测试账号特殊处理
      if (this.email === 'test@123.com') {
        this.isLoading = true;
        
        // 显示加载中
        uni.showLoading({
          title: '登录中...'
        });
        
        try {
          // 发送登录请求，无需验证验证码
          const response = await api.post('/auth/login-register', {
            email: this.email,
            code: '000000' // 任意验证码
          }, false);
          
          // 处理响应与普通登录一致
          this.handleLoginResponse(response);
        } catch (error) {
          console.error('登录请求失败:', error);
          uni.hideLoading();
          
          uni.showToast({
            title: '登录失败，请稍后重试',
            icon: 'none'
          });
          
          this.isLoading = false;
        }
        
        return;
      }
      
      if (!this.code) {
        uni.showToast({
          title: '请输入验证码',
          icon: 'none'
        });
        return;
      }
      
      this.isLoading = true;
      
      // 显示加载中
      uni.showLoading({
        title: '验证中...'
      });
      
      try {
        // 发送登录请求
        const response = await api.post('/auth/login-register', {
          email: this.email,
          code: this.code
        }, false);
        
        // 处理登录响应
        this.handleLoginResponse(response);
      } catch (error) {
        console.error('登录请求失败:', error);
        uni.hideLoading();
        
        uni.showToast({
          title: '登录失败，请稍后重试',
          icon: 'none'
        });
        
        this.isLoading = false;
      }
    },
    
    // 处理登录响应
    handleLoginResponse(response) {
      // 隐藏加载
      uni.hideLoading();
      
      if (response && (response.code === '0000' || response.code === 'SUCCESS')) {
        // 登录成功，保存用户信息
        const userData = response.data;
        
        // 设置令牌 - 确保正确存储token
        if (userData.token) {
          try {
            // 先清除旧token
            uni.removeStorageSync('token');
            uni.removeStorageSync('token_backup');
            // 设置新token，确保以字符串形式存储
            safeSetStorage('token', String(userData.token));
          } catch (err) {
            console.error('保存token失败:', err);
          }
        }
        
        // 保存用户信息
        try {
          // 先清除旧用户信息
          uni.removeStorageSync('userInfo');
          // 设置新用户信息
          const userInfoStr = JSON.stringify(userData);
          safeSetStorage('userInfo', userInfoStr);
        } catch (err) {
          console.error('保存用户信息失败:', err);
        }
        
        // 显示成功提示
        uni.showToast({
          title: '登录成功',
          icon: 'success'
        });
        
        // 发送全局事件
        uni.$emit('userInfoUpdated', userData);
        
        // 跳转到目标页面
        setTimeout(() => {
          // 获取重定向URL
          let redirectUrl = safeGetStorage('redirectUrl') || '/pages/knowledge-base/index';
          
          // 检查是否是知识库详情页，如果是，确保有有效的知识库ID
          if (redirectUrl.includes('/pages/knowledge-base/detail')) {
            // 检查URL中是否有有效的知识库ID
            const match = redirectUrl.match(/[?&]id=([^&]+)/);
            const kbId = match ? match[1] : null;
            
            // 如果没有有效的知识库ID，直接跳转到知识库列表页
            if (!kbId || kbId === 'null' || kbId === 'undefined') {
              redirectUrl = '/pages/knowledge-base/index';
            }
          }
          
          // 清除重定向URL
          uni.removeStorageSync('redirectUrl');
          
          // 判断是否是tabBar页面
          const tabBarPages = [
            '/pages/knowledge-base/index',
            '/pages/bot-modules/bot-list/index',
            '/pages/tools/index',
            '/pages/settings/index'
          ];
          
          if (tabBarPages.includes(redirectUrl)) {
            // 如果是tabBar页面，使用switchTab
            uni.switchTab({
              url: redirectUrl,
              fail: (err) => {
                console.error('跳转失败:', err);
                // 默认跳转到知识库页面
                uni.switchTab({
                  url: '/pages/knowledge-base/index'
                });
              }
            });
          } else {
            // 非tabBar页面，使用reLaunch
            uni.reLaunch({
              url: redirectUrl,
              fail: (err) => {
                console.error('跳转失败:', err);
                // 默认跳转到知识库页面
                uni.switchTab({
                  url: '/pages/knowledge-base/index'
                });
              }
            });
          }
        }, 1000);
      } else {
        // 显示错误信息
        uni.showToast({
          title: response?.message || '登录失败',
          icon: 'none'
        });
        this.isLoading = false;
      }
    }
  }
}
</script>

<style>
.login-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background-color: #f8f9fa;
  padding: 40rpx;
  box-sizing: border-box;
}

.login-container {
  width: 100%;
  max-width: 600rpx;
  background-color: #fff;
  border-radius: 20rpx;
  box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.1);
  padding: 60rpx 40rpx;
  box-sizing: border-box;
  margin: 0 auto;
}

.login-header {
  text-align: center;
  margin-bottom: 60rpx;
}

.logo {
  width: 120rpx;
  height: 120rpx;
  margin-bottom: 20rpx;
}

.title {
  font-size: 36rpx;
  font-weight: bold;
  color: #333;
  margin-bottom: 10rpx;
  display: block;
}

.subtitle {
  font-size: 28rpx;
  color: #666;
  display: block;
}

.login-form {
  width: 100%;
  box-sizing: border-box;
}

.input-group {
  margin-bottom: 30rpx;
  width: 100%;
  box-sizing: border-box;
}

.input-label {
  font-size: 28rpx;
  color: #333;
  margin-bottom: 10rpx;
  display: block;
}

.input {
  width: 100%;
  height: 80rpx;
  border: 1rpx solid #ddd;
  border-radius: 8rpx;
  padding: 0 20rpx;
  font-size: 28rpx;
  background-color: #f5f7fa;
  box-sizing: border-box;
}

.verification-group .code-input-wrapper {
  display: flex;
  align-items: center;
  width: 100%;
  box-sizing: border-box;
}

.verification-group .input {
  flex: 1;
  margin-right: 0;
}

.send-code-btn {
  width: 200rpx;
  height: 80rpx;
  background-color: var(--primary-color, #007AFF);
  color: white;
  border: none;
  border-radius: 8rpx;
  margin-left: 20rpx;
  font-size: 24rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  box-sizing: border-box;
}

.send-code-btn[disabled] {
  background-color: #cccccc;
}

.tips-text {
  font-size: 24rpx;
  color: #999;
  margin-bottom: 40rpx;
}

.submit-btn {
  width: 100%;
  height: 90rpx;
  background-color: var(--primary-color, #007AFF);
  color: white;
  border: none;
  border-radius: 45rpx;
  font-size: 32rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.submit-btn[disabled] {
  background-color: #cccccc;
}
</style>
