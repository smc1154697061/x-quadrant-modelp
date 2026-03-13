<template>
  <app-layout title="我的组织">
    <view class="org-container">
      <view class="section-header">
        <text class="section-title">我所属的组织</text>
        <button class="create-btn" @tap="showCreateDialog">创建组织</button>
      </view>
      
      <view v-if="loading" class="loading-state">
        <text>加载中...</text>
      </view>
      
      <view v-else-if="organizations.length === 0" class="empty-state">
        <text class="empty-text">暂无组织</text>
        <text class="empty-hint">创建一个组织来管理您的团队吧</text>
      </view>
      
      <view v-else class="org-list">
        <view 
          v-for="org in organizations" 
          :key="org.id" 
          class="org-card"
          @tap="navigateToDetail(org.id)"
        >
          <view class="org-info">
            <text class="org-name">{{ org.name }}</text>
            <text class="org-desc">{{ org.description || '暂无描述' }}</text>
          </view>
          <view class="org-meta">
            <view class="meta-item">
              <text class="meta-label">成员</text>
              <text class="meta-value">{{ org.member_count }}人</text>
            </view>
            <view class="meta-item">
              <text class="meta-label">我的角色</text>
              <text class="meta-value" :class="org.my_role">{{ org.my_role === 'admin' ? '管理员' : '成员' }}</text>
            </view>
          </view>
        </view>
      </view>
      
      <view v-if="showCreate" class="dialog-overlay" @tap="hideCreateDialog">
        <view class="dialog-content" @tap.stop>
          <text class="dialog-title">创建组织</text>
          
          <view class="form-item">
            <text class="form-label">组织名称</text>
            <input 
              type="text" 
              v-model="newOrg.name"
              placeholder="请输入组织名称"
              maxlength="50"
              class="form-input"
            />
          </view>
          
          <view class="form-item">
            <text class="form-label">组织描述</text>
            <textarea 
              v-model="newOrg.description"
              placeholder="请输入组织描述（选填）"
              maxlength="200"
              class="form-textarea"
            ></textarea>
          </view>
          
          <view class="dialog-buttons">
            <button class="btn-cancel" @tap="hideCreateDialog">取消</button>
            <button class="btn-confirm" @tap="createOrganization" :disabled="!newOrg.name || creating">
              {{ creating ? '创建中...' : '创建' }}
            </button>
          </view>
        </view>
      </view>
    </view>
  </app-layout>
</template>

<script>
import AppLayout from '../../components/layout/AppLayout.vue';
import api from '../../utils/api.js';
import { getCurrentUser } from '../../utils/auth.js';

export default {
  components: {
    AppLayout
  },
  data() {
    return {
      organizations: [],
      loading: false,
      showCreate: false,
      creating: false,
      newOrg: {
        name: '',
        description: ''
      },
      userInfo: null
    };
  },
  onLoad() {
    this.userInfo = getCurrentUser();
    this.fetchOrganizations();
  },
  onShow() {
    this.fetchOrganizations();
  },
  methods: {
    async fetchOrganizations() {
      if (!this.userInfo) {
        this.userInfo = getCurrentUser();
      }
      if (!this.userInfo) {
        return;
      }
      
      this.loading = true;
      try {
        const result = await api.get('/llm/organizations');
        if (result && (result.code === '0000' || result.code === 'SUCCESS')) {
          this.organizations = result.data || [];
        }
      } catch (error) {
        console.error('获取组织列表失败:', error);
        api.showError('获取组织列表失败');
      } finally {
        this.loading = false;
      }
    },
    
    showCreateDialog() {
      this.newOrg = { name: '', description: '' };
      this.showCreate = true;
    },
    
    hideCreateDialog() {
      this.showCreate = false;
    },
    
    async createOrganization() {
      if (!this.newOrg.name.trim()) {
        api.showError('请输入组织名称');
        return;
      }
      
      this.creating = true;
      try {
        const result = await api.post('/llm/organizations', {
          name: this.newOrg.name.trim(),
          description: this.newOrg.description.trim() || null
        });
        
        if (result && (result.code === '0000' || result.code === 'SUCCESS')) {
          api.showSuccess('创建成功');
          this.showCreate = false;
          this.fetchOrganizations();
        }
      } catch (error) {
        console.error('创建组织失败:', error);
        api.showError('创建组织失败');
      } finally {
        this.creating = false;
      }
    },
    
    navigateToDetail(orgId) {
      uni.navigateTo({
        url: `/pages/organization/detail?id=${orgId}`
      });
    }
  }
};
</script>

<style>
.org-container {
  padding: 30rpx;
  background-color: #f5f7fa;
  min-height: 100vh;
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

.create-btn {
  background-color: #007bff;
  color: #fff;
  font-size: 26rpx;
  padding: 16rpx 32rpx;
  border-radius: 30rpx;
  border: none;
}

.loading-state {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 100rpx 0;
  color: #999;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 100rpx 0;
}

.empty-text {
  font-size: 30rpx;
  color: #999;
  margin-bottom: 16rpx;
}

.empty-hint {
  font-size: 26rpx;
  color: #ccc;
}

.org-list {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.org-card {
  background-color: #fff;
  border-radius: 16rpx;
  padding: 30rpx;
  box-shadow: 0 2rpx 20rpx rgba(0, 0, 0, 0.08);
}

.org-info {
  margin-bottom: 20rpx;
}

.org-name {
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
  display: block;
  margin-bottom: 10rpx;
}

.org-desc {
  font-size: 26rpx;
  color: #999;
  display: block;
}

.org-meta {
  display: flex;
  gap: 40rpx;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 10rpx;
}

.meta-label {
  font-size: 24rpx;
  color: #999;
}

.meta-value {
  font-size: 24rpx;
  color: #333;
  font-weight: 500;
}

.meta-value.admin {
  color: #007bff;
}

.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog-content {
  width: 600rpx;
  background-color: #fff;
  border-radius: 20rpx;
  padding: 40rpx;
}

.dialog-title {
  font-size: 34rpx;
  font-weight: 600;
  color: #333;
  display: block;
  text-align: center;
  margin-bottom: 40rpx;
}

.form-item {
  margin-bottom: 30rpx;
}

.form-label {
  font-size: 28rpx;
  color: #333;
  display: block;
  margin-bottom: 16rpx;
}

.form-input {
  width: 100%;
  height: 80rpx;
  background-color: #f5f7fa;
  border-radius: 12rpx;
  padding: 0 24rpx;
  font-size: 28rpx;
  box-sizing: border-box;
}

.form-textarea {
  width: 100%;
  height: 160rpx;
  background-color: #f5f7fa;
  border-radius: 12rpx;
  padding: 20rpx 24rpx;
  font-size: 28rpx;
  box-sizing: border-box;
}

.dialog-buttons {
  display: flex;
  gap: 20rpx;
  margin-top: 40rpx;
}

.btn-cancel, .btn-confirm {
  flex: 1;
  height: 80rpx;
  border-radius: 40rpx;
  font-size: 28rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
}

.btn-cancel {
  background-color: #f5f7fa;
  color: #666;
}

.btn-confirm {
  background-color: #007bff;
  color: #fff;
}

.btn-confirm[disabled] {
  background-color: #ccc;
}
</style>
