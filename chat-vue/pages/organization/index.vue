<template>
  <app-layout title="我的组织">
    <view class="organization-container">
      <view class="org-section">
        <view class="section-header">
          <view class="section-title">我的组织</view>
          <button class="create-org-btn" @tap="showCreateOrgDialog">创建组织</button>
        </view>
        
        <view v-if="loading" class="loading">
          <text>加载中...</text>
        </view>
        
        <view v-else-if="organizations.length === 0" class="empty-state">
          <text>暂无组织</text>
        </view>
        
        <view v-else class="org-grid">
          <view v-for="org in organizations" :key="org.id" class="org-card" @tap="navigateToDetail(org)">
            <view class="org-card-content">
              <view class="org-card-header">
                <text class="org-name">{{ org.name }}</text>
                <text class="org-role-badge">{{ getRoleText(org.user_role) }}</text>
              </view>
              <text class="org-description">{{ org.description || '无描述' }}</text>
              <view class="org-meta">
                <text class="member-count">{{ org.member_count || 0 }} 名成员</text>
                <text class="created-at">创建于 {{ formatDate(org.created_at) }}</text>
              </view>
            </view>
          </view>
        </view>
      </view>
      
      <view v-if="showCreateOrg" class="dialog create-org-dialog">
        <view class="dialog-content" @tap.stop>
          <text class="dialog-title">创建组织</text>
          
          <view class="form-item">
            <text class="form-label">组织名称</text>
            <view class="input-wrapper">
              <input 
                type="text" 
                v-model="newOrg.name"
                placeholder="输入组织名称" 
                maxlength="100"
                class="basic-input"
              />
            </view>
          </view>
          
          <view class="form-item">
            <text class="form-label">组织描述</text>
            <view class="input-wrapper">
              <textarea
                v-model="newOrg.description"
                placeholder="输入组织描述(选填)" 
                class="basic-textarea"
              ></textarea>
            </view>
          </view>
          
          <view class="dialog-buttons">
            <button class="cancel-btn" @tap="cancelCreateOrg" :disabled="creating">取消</button>
            <button class="confirm-btn" @tap="confirmCreateOrg" :disabled="!newOrg.name || creating">
              <text v-if="creating">创建中...</text>
              <text v-else>创建</text>
            </button>
          </view>
        </view>
      </view>
      
      <login-dialog
        v-model:visible="loginVisible"
        @login-success="onLoginSuccess"
        @update:visible="onLoginVisibleChange"
      />
    </view>
  </app-layout>
</template>

<script>
import api from '../../utils/api.js';
import AppLayout from '../../components/layout/AppLayout.vue';
import LoginDialog from '../../components/user/LoginDialog.vue';
import { getCurrentUser } from '../../utils/auth.js';

export default {
  components: {
    AppLayout,
    LoginDialog
  },
  data() {
    return {
      organizations: [],
      loading: false,
      showCreateOrg: false,
      creating: false,
      newOrg: {
        name: '',
        description: ''
      },
      loginVisible: false,
      userInfo: null,
      isLoggedIn: false
    }
  },
  onLoad() {
    this.userInfo = getCurrentUser();
    this.isLoggedIn = !!this.userInfo;
    
    this.fetchOrganizations();
  },
  onShow() {
    this.fetchOrganizations();
  },
  methods: {
    async fetchOrganizations() {
      if (!this.isLoggedIn) {
        this.organizations = [];
        return;
      }
      
      this.loading = true;
      
      try {
        const result = await api.get('/llm/organizations', {}, true);
        
        if (result && (result.code === '0000' || result.code === 'SUCCESS')) {
          this.organizations = result.data || [];
        } else {
          this.organizations = [];
        }
      } catch (error) {
        console.error('获取组织列表失败:', error);
        this.organizations = [];
      } finally {
        this.loading = false;
      }
    },
    
    navigateToDetail(org) {
      uni.navigateTo({
        url: `/pages/organization/detail?id=${org.id}&name=${encodeURIComponent(org.name)}`
      });
    },
    
    showCreateOrgDialog() {
      if (!this.isLoggedIn) {
        uni.showModal({
          title: '提示',
          content: '创建组织需要先登录，是否前往登录？',
          success: (res) => {
            if (res.confirm) {
              this.loginVisible = true;
            }
          }
        });
        return;
      }
      
      this.newOrg = {
        name: '',
        description: ''
      };
      this.showCreateOrg = true;
    },
    
    cancelCreateOrg() {
      this.showCreateOrg = false;
    },
    
    async confirmCreateOrg() {
      if (!this.newOrg.name.trim()) {
        api.showError('请输入组织名称');
        return;
      }
      
      if (!this.isLoggedIn) {
        this.showCreateOrg = false;
        this.loginVisible = true;
        return;
      }
      
      this.creating = true;
      
      try {
        const requestData = {
          name: this.newOrg.name,
          description: this.newOrg.description || ''
        };
        
        const result = await api.post('/llm/organizations', requestData);
        
        if (result && (result.code === '0000')) {
          this.showCreateOrg = false;
          api.showSuccess('组织创建成功');
          this.fetchOrganizations();
          
          if (result.data && result.data.id) {
            setTimeout(() => {
              this.navigateToDetail(result.data);
            }, 500);
          }
        } else {
          api.showError(result?.message || '创建组织失败');
        }
      } catch (error) {
        console.error('创建组织失败:', error);
        api.showError('创建组织失败');
      } finally {
        this.creating = false;
      }
    },
    
    getRoleText(role) {
      const roleMap = {
        'owner': '所有者',
        'admin': '管理员',
        'member': '成员'
      };
      return roleMap[role] || '成员';
    },
    
    formatDate(dateStr) {
      if (!dateStr) return '';
      const date = new Date(dateStr);
      return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
    },
    
    onLoginSuccess(userInfo) {
      this.userInfo = userInfo;
      this.isLoggedIn = true;
      this.loginVisible = false;
      this.fetchOrganizations();
    },
    
    onLoginVisibleChange(visible) {
      this.loginVisible = visible;
    }
  }
};
</script>

<style>
.organization-container {
  padding: 30rpx;
  background-color: #f5f7fa;
  min-height: 100vh;
}

.org-section {
  background-color: #fff;
  border-radius: 16rpx;
  padding: 30rpx;
  box-shadow: 0 2rpx 20rpx rgba(0, 0, 0, 0.08);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30rpx;
}

.section-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
}

.create-org-btn {
  background-color: #007bff;
  color: #fff;
  border: none;
  border-radius: 8rpx;
  padding: 15rpx 25rpx;
  font-size: 26rpx;
}

.loading, .empty-state {
  text-align: center;
  padding: 100rpx 0;
  color: #666;
  font-size: 28rpx;
}

.org-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300rpx, 1fr));
  gap: 20rpx;
}

.org-card {
  background-color: #fff;
  border-radius: 12rpx;
  padding: 25rpx;
  border: 2rpx solid #f0f0f0;
  cursor: pointer;
  transition: all 0.3s;
}

.org-card:hover {
  border-color: #007bff;
  box-shadow: 0 4rpx 15rpx rgba(0, 123, 255, 0.1);
}

.org-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15rpx;
}

.org-name {
  font-size: 30rpx;
  font-weight: 600;
  color: #333;
}

.org-role-badge {
  background-color: #e3f2fd;
  color: #1976d2;
  padding: 4rpx 12rpx;
  border-radius: 20rpx;
  font-size: 22rpx;
}

.org-description {
  color: #666;
  font-size: 26rpx;
  line-height: 1.5;
  margin-bottom: 15rpx;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.org-meta {
  display: flex;
  justify-content: space-between;
  font-size: 24rpx;
  color: #999;
}

.dialog {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 999;
}

.dialog-content {
  background-color: #fff;
  border-radius: 16rpx;
  padding: 40rpx;
  width: 90%;
  max-width: 600rpx;
}

.dialog-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 30rpx;
  display: block;
}

.form-item {
  margin-bottom: 30rpx;
}

.form-label {
  font-size: 28rpx;
  color: #333;
  margin-bottom: 15rpx;
  display: block;
}

.input-wrapper {
  position: relative;
}

.basic-input {
  width: 100%;
  border: 2rpx solid #e0e0e0;
  border-radius: 8rpx;
  padding: 20rpx;
  font-size: 28rpx;
  box-sizing: border-box;
}

.basic-textarea {
  width: 100%;
  border: 2rpx solid #e0e0e0;
  border-radius: 8rpx;
  padding: 20rpx;
  font-size: 28rpx;
  min-height: 150rpx;
  box-sizing: border-box;
}

.dialog-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 20rpx;
  margin-top: 40rpx;
}

.cancel-btn {
  background-color: #f5f5f5;
  color: #333;
  border: none;
  border-radius: 8rpx;
  padding: 15rpx 30rpx;
  font-size: 28rpx;
}

.confirm-btn {
  background-color: #007bff;
  color: #fff;
  border: none;
  border-radius: 8rpx;
  padding: 15rpx 30rpx;
  font-size: 28rpx;
}

@media screen and (min-width: 768px) {
  .organization-container {
    padding: 50rpx;
    max-width: 1200rpx;
    margin: 0 auto;
  }
  
  .org-grid {
    grid-template-columns: repeat(auto-fill, minmax(350rpx, 1fr));
  }
}
</style>
