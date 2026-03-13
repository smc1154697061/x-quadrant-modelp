<template>
  <app-layout title="组织详情" :show-back="true">
    <view class="org-detail-container">
      <view v-if="loading" class="loading">
        <text>加载中...</text>
      </view>
      
      <view v-else-if="!organization" class="empty-state">
        <text>组织不存在</text>
      </view>
      
      <view v-else class="org-content">
        <view class="org-info-section">
          <view class="section-header">
            <view class="section-title">组织信息</view>
            <button v-if="isAdmin" class="edit-btn" @tap="showEditOrgDialog">编辑</button>
          </view>
          
          <view class="org-info-card">
            <view class="info-item">
              <text class="info-label">组织名称</text>
              <text class="info-value">{{ organization.name }}</text>
            </view>
            <view class="info-item">
              <text class="info-label">组织描述</text>
              <text class="info-value">{{ organization.description || '无描述' }}</text>
            </view>
            <view class="info-item">
              <text class="info-label">创建时间</text>
              <text class="info-value">{{ formatDate(organization.created_at) }}</text>
            </view>
            <view class="info-item">
              <text class="info-label">我的角色</text>
              <text class="info-value role-{{ organization.user_role }}">{{ getRoleText(organization.user_role) }}</text>
            </view>
          </view>
          
          <button v-if="isAdmin" class="dissolve-btn" @tap="confirmDissolveOrg">解散组织</button>
        </view>
        
        <view class="members-section">
          <view class="section-title">成员列表 ({{ members.length }})</view>
          
          <view v-if="loadingMembers" class="loading-small">
            <text>加载成员中...</text>
          </view>
          
          <view v-else class="members-list">
            <view v-for="member in members" :key="member.user_id" class="member-item">
              <view class="member-avatar">
                <text v-if="member.avatar_url">{{ member.nickname || member.email }}</text>
                <text v-else class="avatar-text">{{ getAvatarText(member.nickname || member.email) }}</text>
              </view>
              <view class="member-info">
                <text class="member-name">{{ member.nickname || member.email }}</text>
                <text class="member-email">{{ member.email }}</text>
              </view>
              <view class="member-role">
                <text class="role-badge role-{{ member.role }}">{{ getRoleText(member.role) }}</text>
              </view>
            </view>
          </view>
        </view>
      </view>
      
      <view v-if="showEditOrg" class="dialog edit-org-dialog">
        <view class="dialog-content" @tap.stop>
          <text class="dialog-title">编辑组织</text>
          
          <view class="form-item">
            <text class="form-label">组织名称</text>
            <view class="input-wrapper">
              <input 
                type="text" 
                v-model="editOrg.name"
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
                v-model="editOrg.description"
                placeholder="输入组织描述(选填)" 
                class="basic-textarea"
              ></textarea>
            </view>
          </view>
          
          <view class="dialog-buttons">
            <button class="cancel-btn" @tap="cancelEditOrg" :disabled="saving">取消</button>
            <button class="confirm-btn" @tap="confirmEditOrg" :disabled="!editOrg.name || saving">
              <text v-if="saving">保存中...</text>
              <text v-else>保存</text>
            </button>
          </view>
        </view>
      </view>
    </view>
  </app-layout>
</template>

<script>
import api from '../../utils/api.js';
import AppLayout from '../../components/layout/AppLayout.vue';
import { getCurrentUser } from '../../utils/auth.js';

export default {
  components: {
    AppLayout
  },
  data() {
    return {
      orgId: null,
      organization: null,
      members: [],
      loading: false,
      loadingMembers: false,
      showEditOrg: false,
      saving: false,
      editOrg: {
        name: '',
        description: ''
      },
      userInfo: null
    }
  },
  onLoad(options) {
    this.orgId = options.id;
    this.userInfo = getCurrentUser();
    
    if (this.orgId) {
      this.fetchOrganizationDetail();
      this.fetchMembers();
    }
  },
  computed: {
    isAdmin() {
      return this.organization && (this.organization.user_role === 'owner' || this.organization.user_role === 'admin');
    }
  },
  methods: {
    async fetchOrganizationDetail() {
      this.loading = true;
      
      try {
        const result = await api.get(`/llm/organizations/${this.orgId}`, {}, true);
        
        if (result && (result.code === '0000' || result.code === 'SUCCESS')) {
          this.organization = result.data;
        } else {
          api.showError(result?.message || '获取组织信息失败');
        }
      } catch (error) {
        console.error('获取组织信息失败:', error);
        api.showError('获取组织信息失败');
      } finally {
        this.loading = false;
      }
    },
    
    async fetchMembers() {
      this.loadingMembers = true;
      
      try {
        const result = await api.get(`/llm/organizations/${this.orgId}/members`, {}, true);
        
        if (result && (result.code === '0000' || result.code === 'SUCCESS')) {
          this.members = result.data || [];
        }
      } catch (error) {
        console.error('获取成员列表失败:', error);
      } finally {
        this.loadingMembers = false;
      }
    },
    
    showEditOrgDialog() {
      this.editOrg = {
        name: this.organization.name,
        description: this.organization.description || ''
      };
      this.showEditOrg = true;
    },
    
    cancelEditOrg() {
      this.showEditOrg = false;
    },
    
    async confirmEditOrg() {
      if (!this.editOrg.name.trim()) {
        api.showError('请输入组织名称');
        return;
      }
      
      this.saving = true;
      
      try {
        const result = await api.put(`/llm/organizations/${this.orgId}`, {
          name: this.editOrg.name,
          description: this.editOrg.description
        });
        
        if (result && (result.code === '0000')) {
          this.showEditOrg = false;
          api.showSuccess('组织信息更新成功');
          this.fetchOrganizationDetail();
        } else {
          api.showError(result?.message || '更新组织信息失败');
        }
      } catch (error) {
        console.error('更新组织信息失败:', error);
        api.showError('更新组织信息失败');
      } finally {
        this.saving = false;
      }
    },
    
    confirmDissolveOrg() {
      uni.showModal({
        title: '确认解散',
        content: '解散组织将删除所有组织数据，此操作不可恢复！确定要解散吗？',
        success: async (res) => {
          if (res.confirm) {
            await this.dissolveOrganization();
          }
        }
      });
    },
    
    async dissolveOrganization() {
      try {
        const result = await api.delete(`/llm/organizations/${this.orgId}`);
        
        if (result && (result.code === '0000')) {
          api.showSuccess('组织已解散');
          setTimeout(() => {
            uni.navigateBack();
          }, 1000);
        } else {
          api.showError(result?.message || '解散组织失败');
        }
      } catch (error) {
        console.error('解散组织失败:', error);
        api.showError('解散组织失败');
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
    
    getAvatarText(name) {
      if (!name) return 'U';
      return name.charAt(0).toUpperCase();
    },
    
    formatDate(dateStr) {
      if (!dateStr) return '';
      const date = new Date(dateStr);
      return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
    }
  }
};
</script>

<style>
.org-detail-container {
  padding: 30rpx;
  background-color: #f5f7fa;
  min-height: 100vh;
}

.loading, .empty-state {
  text-align: center;
  padding: 100rpx 0;
  color: #666;
  font-size: 28rpx;
}

.loading-small {
  text-align: center;
  padding: 50rpx 0;
  color: #666;
  font-size: 26rpx;
}

.org-info-section, .members-section {
  background-color: #fff;
  border-radius: 16rpx;
  padding: 30rpx;
  margin-bottom: 30rpx;
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

.edit-btn {
  background-color: #007bff;
  color: #fff;
  border: none;
  border-radius: 8rpx;
  padding: 10rpx 20rpx;
  font-size: 24rpx;
}

.dissolve-btn {
  width: 100%;
  background-color: #f44336;
  color: #fff;
  border: none;
  border-radius: 8rpx;
  padding: 20rpx;
  font-size: 28rpx;
  margin-top: 30rpx;
}

.org-info-card {
  background-color: #fafafa;
  border-radius: 12rpx;
  padding: 20rpx;
}

.info-item {
  display: flex;
  padding: 20rpx 0;
  border-bottom: 2rpx solid #f0f0f0;
}

.info-item:last-child {
  border-bottom: none;
}

.info-label {
  width: 150rpx;
  color: #666;
  font-size: 28rpx;
}

.info-value {
  flex: 1;
  color: #333;
  font-size: 28rpx;
}

.role-owner {
  color: #d32f2f;
  font-weight: 600;
}

.role-admin {
  color: #f57c00;
  font-weight: 600;
}

.role-member {
  color: #1976d2;
}

.members-list {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.member-item {
  display: flex;
  align-items: center;
  padding: 20rpx;
  background-color: #fafafa;
  border-radius: 12rpx;
}

.member-avatar {
  width: 80rpx;
  height: 80rpx;
  border-radius: 50%;
  background-color: #e0e0e0;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 20rpx;
  overflow: hidden;
}

.avatar-text {
  color: #fff;
  font-size: 32rpx;
  font-weight: 600;
}

.member-info {
  flex: 1;
}

.member-name {
  font-size: 28rpx;
  color: #333;
  display: block;
  margin-bottom: 5rpx;
}

.member-email {
  font-size: 24rpx;
  color: #666;
}

.member-role {
  margin-left: 20rpx;
}

.role-badge {
  padding: 6rpx 16rpx;
  border-radius: 20rpx;
  font-size: 22rpx;
}

.role-badge.role-owner {
  background-color: #ffebee;
  color: #d32f2f;
}

.role-badge.role-admin {
  background-color: #fff3e0;
  color: #f57c00;
}

.role-badge.role-member {
  background-color: #e3f2fd;
  color: #1976d2;
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
  .org-detail-container {
    padding: 50rpx;
    max-width: 900rpx;
    margin: 0 auto;
  }
}
</style>
