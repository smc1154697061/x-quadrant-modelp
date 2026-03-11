<template>
  <view class="login-dialog" v-show="visible" @tap.stop>
    <view class="mask" @tap.stop="handleClose"></view>
    <view class="dialog-content" @tap.stop>
      <view class="dialog-header">
        <text class="title">登录/注册</text>
        <view class="close-btn" @tap.stop="handleClose">×</view>
      </view>
      
      <view class="dialog-body">
        <view class="input-group">
          <input 
            type="text" 
            v-model="email" 
            placeholder="请输入邮箱"
            class="input"
          />
        </view>
        
        <view class="input-group verification-group">
          <input 
            type="text" 
            v-model="code" 
            placeholder="请输入验证码"
            class="input"
          />
          <button 
            @tap.stop="sendCode" 
            :disabled="isSending"
            class="send-code-btn"
          >
            <text>{{ isSending ? `${countdown}s后重试` : '获取验证码' }}</text>
          </button>
        </view>
        
        <view class="tips-text">
          <text>* 未注册用户将自动创建账号</text>
        </view>
        
        <view class="btn-wrapper">
          <button @tap.stop="handleSubmit" class="submit-btn">
            <text>登录/注册</text>
          </button>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import api from '../../utils/api.js';

export default {
  name: 'LoginDialog',
  props: {
    visible: {
      type: Boolean,
      default: false
    }
  },
  emits: ['update:visible', 'login-success'],
  data() {
    return {
      email: '',
      code: '',
      isSending: false,
      countdown: 60
    }
  },
  methods: {
    // 关闭弹窗
    handleClose() {
      this.$emit('update:visible', false)
    },
    
    // 发送验证码
    async sendCode() {
      if (!this.email) {
        uni.showToast({
          title: '请输入邮箱',
          icon: 'none'
        })
        return
      }
      
      // 验证邮箱格式
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
      if (!emailRegex.test(this.email)) {
        uni.showToast({
          title: '请输入正确的邮箱格式',
          icon: 'none'
        })
        return
      }
      
      if (this.isSending) return
      
      try {
        this.isSending = true
        
        // 显示加载中提示
        uni.showLoading({
          title: '发送中...'
        });
        
        // 使用API服务发送请求
        const response = await api.post('/auth/send-code', { email: this.email });
        
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
        
        let errorMsg = '发送失败，请重试';
        if (error && error.message) {
          errorMsg = error.message;
          console.error('错误详情:', error.message);
        }
        
        uni.showToast({
          title: errorMsg,
          icon: 'none'
        });
        
        this.isSending = false;
      }
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
      
      if (!this.code) {
        uni.showToast({
          title: '请输入验证码',
          icon: 'none'
        });
        return;
      }
      
      // 显示加载中
      uni.showLoading({
        title: '验证中...'
      });
      
      try {
        // 使用api模块而不是this.$http
        const response = await api.post('/auth/login-register', {
          email: this.email,
          code: this.code
        });
        
        // 隐藏加载
        uni.hideLoading();
        
        if (response && (response.code === '0000' || response.code === 'SUCCESS')) {
          // 登录成功，保存用户信息
          const userData = response.data;
          
          // 设置令牌
          if (userData.token) {
            // 确保token是字符串格式
            const token = String(userData.token);
            uni.setStorageSync('token', token);
          }
          
          // 保存用户信息
          uni.setStorageSync('userInfo', JSON.stringify(userData));
          
          // 清空输入
          this.email = '';
          this.code = '';
          
          // 显示成功提示
          uni.showToast({
            title: '登录成功',
            icon: 'success'
          });
          
          // 通知父组件更新用户状态
          this.$emit('login-success', userData);
          
          // 发送全局事件
          uni.$emit('userInfoUpdated', userData);
          
          // 关闭弹窗（延时关闭，确保用户菜单状态已更新）
          setTimeout(() => {
            this.handleClose();
          }, 500);
        } else {
          // 显示错误信息
          uni.showToast({
            title: response?.message || '登录失败',
            icon: 'none'
          });
        }
      } catch (error) {
        console.error('登录请求失败:', error);
        uni.hideLoading();
        
        // 处理不同类型的错误
        let errorMsg = '登录失败，请稍后重试';
        
        if (error.response) {
          // 服务器返回了错误状态码
          const responseData = error.response?.data;
          errorMsg = responseData?.message || '服务器错误，请稍后重试';
          
          // 特殊处理数据库连接错误
          if (responseData?.code === 'DATABASE_ERROR') {
            errorMsg = '系统繁忙，请稍后再试';
          }
        } else if (error.request) {
          // 请求已发送但没有收到响应
          errorMsg = '网络连接失败，请检查网络设置';
        } else if (error.message) {
          // 其他错误
          errorMsg = error.message;
        }
        
        uni.showToast({
          title: errorMsg,
          icon: 'none',
          duration: 3000
        });
      }
    },
    
    // 倒计时
    startCountdown() {
      this.countdown = 60
      const timer = setInterval(() => {
        this.countdown--
        if (this.countdown <= 0) {
          clearInterval(timer)
          this.isSending = false
        }
      }, 1000)
    }
  }
}
</script>

<style>
.login-dialog {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 999;
}
  
.mask {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(3px);
}
  
.dialog-content {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 80%;
  max-width: 600rpx;
  background-color: #fff;
  border-radius: 20rpx;
  overflow: hidden;
  box-shadow: 0 10rpx 30rpx rgba(0, 0, 0, 0.15);
}
  
.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 30rpx;
  border-bottom: 2rpx solid #f0f0f0;
}

.title {
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
}

.close-btn {
  font-size: 50rpx;
  line-height: 40rpx;
  color: #999;
  cursor: pointer;
  padding: 0 10rpx;
}

.dialog-body {
  padding: 30rpx;
}

.input-group {
  margin-bottom: 30rpx;
}

.verification-group {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.input {
  width: 100%;
  height: 80rpx;
  font-size: 28rpx;
  color: #333;
  background-color: #f8f9fa;
  padding: 0 20rpx;
  border: 2rpx solid #ddd;
  border-radius: 8rpx;
  box-sizing: border-box;
}

.input:focus {
  border-color: var(--primary-color, #007AFF);
}

.send-code-btn {
  min-width: 180rpx;
  margin-left: 20rpx;
  height: 80rpx;
  line-height: 80rpx;
  font-size: 24rpx;
  color: #fff;
  background-color: var(--primary-color, #007AFF);
  border-radius: 8rpx;
  text-align: center;
  padding: 0 10rpx;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-wrapper {
  margin-top: 40rpx;
}

.submit-btn {
  width: 100%;
  height: 90rpx;
  color: white;
  background-color: var(--primary-color, #007AFF);
  font-size: 28rpx;
  border-radius: 8rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
  padding: 0;
}

.tips-text {
  font-size: 24rpx;
  color: #999;
  margin-top: 10rpx;
}

/* 响应式设计 */
@media screen and (max-width: 767px) {
  .dialog-content {
    width: 90%;
  }
}
</style>
