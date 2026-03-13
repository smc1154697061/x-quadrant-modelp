<template>
  <app-layout :title="orgInfo.name || '组织详情'">
    <view class="detail-container">
      <view v-if="loading" class="loading-state">
        <text>加载中...</text>
      </view>
      
      <view v-else class="detail-content">
        <view class="info-section">
          <view class="info-header">
            <text class="info-title">基本信息</text>
            <button v-if="orgInfo.is_admin" class="edit-btn" @tap="showEditDialog">编辑</button>
          </view>
          
          <view class="info-item">
            <text class="info-label">组织名称</text>
            <text class="info-value">{{ orgInfo.name }}</text>
          </view>
          
          <view class="info-item">
            <text class="info-label">组织描述</text>
            <text class="info-value">{{ orgInfo.description || '暂无描述' }}</text>
          </view>
          
          <view class="info-item">
            <text class="info-label">创建时间</text>
            <text class="info-value">{{ formatDate(orgInfo.created_at) }}</text>
          </view>
        </view>
        
        <view class="member-section">
          <view class="section-header">
            <text class="section-title">成员列表 ({{ orgInfo.member_count || 0 }}人)</text>
            <button v-if="orgInfo.is_admin" class="add-btn" @tap="showAddMemberDialog">添加成员</button>
          </view>
          
          <view class="member-list">
            <view v-for="member in members" :key="member.user_id" class="member-item">
              <view class="member-avatar">
                <text class="avatar-text">{{ getAvatarText(member.name) }}</text>
              </view>
              <view class="member-info">
                <text class="member-name">{{ member.name }}</text>
                <text class="member-email">{{ member.email }}</text>
              </view>
              <view class="member-role">
                <text :class="['role-tag', member.role]">{{ member.role === 'admin' ? '管理员' : '成员' }}</text>
              </view>
              <button 
                v-if="orgInfo.is_admin && member.user_id !== currentUserId" 
                class="remove-btn"
                @tap="confirmRemoveMember(member)"
              >移除</button>
            </view>
          </view>
        </view>
        
        <view class="action-section">
          <button class="leave-btn" @tap="confirmLeave">退出组织</button>
          <button v-if="orgInfo.is_admin" class="dissolve-btn" @tap="confirmDissolve">解散组织</button>
        </view>
      </view>
      
      <view v-if="showEdit" class="dialog-overlay" @tap="hideEditDialog">
        <view class="dialog-content" @tap.stop>
          <text class="dialog-title">编辑组织</text>
          
          <view class="form-item">
            <text class="form-label">组织名称</text>
            <input 
              type="text" 
              v-model="editForm.name"
              placeholder="请输入组织名称"
              maxlength="50"
              class="form-input"
            />
          </view>
          
          <view class="form-item">
            <text class="form-label">组织描述</text>
            <textarea 
              v-model="editForm.description"
              placeholder="请输入组织描述（选填）"
              maxlength="200"
              class="form-textarea"
            ></textarea>
          </view>
          
          <view class="dialog-buttons">
            <button class="btn-cancel" @tap="hideEditDialog">取消</button>
            <button class="btn-confirm" @tap="updateOrganization" :disabled="!editForm.name || saving">
              {{ saving ? '保存中...' : '保存' }}
            </button>
          </view>
        </view>
      </view>
      
      <view v-if="showAddMember" class="dialog-overlay" @tap="hideAddMemberDialog">
        <view class="dialog-content" @tap.stop>
          <text class="dialog-title">添加成员</text>
          
          <view class="form-item">
            <text class="form-label">搜索用户</text>
            <input 
              type="text" 
              v-model="searchEmail"
              placeholder="输入邮箱搜索用户"
              class="form-input"
              @input="searchUsers"
            />
          </view>
          
          <view v-if="searchResults.length > 0" class="search-results">
            <view 
              v-for="user in searchResults" 
              :key="user.id" 
              class="search-item"
              @tap="selectUser(user)"
            >
              <text class="search-name">{{ user.name }}</text>
              <text class="search-email">{{ user.email }}</text>
            </view>
          </view>
          
          <view v-if="selectedUser" class="selected-user">
            <text class="selected-label">已选择：</text>
            <text class="selected-name">{{ selectedUser.name }} ({{ selectedUser.email }})</text>
          </view>
          
          <view class="form-item">
            <text class="form-label">角色</text>
            <view class="role-options">
              <view 
                class="role-option" 
                :class="{ active: newMemberRole === 'member' }"
                @tap="newMemberRole = 'member'"
              >
                <text>成员</text>
              </view>
              <view 
                class="role-option" 
                :class="{ active: newMemberRole === 'admin' }"
                @tap="newMemberRole = 'admin'"
              >
                <text>管理员</text>
              </view>
            </view>
          </view>
          
          <view class="dialog-buttons">
            <button class="btn-cancel" @tap="hideAddMemberDialog">取消</button>
            <button class="btn-confirm" @tap="addMember" :disabled="!selectedUser || adding">
              {{ adding ? '添加中...' : '添加' }}
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
      orgId: null,
      orgInfo: {},
      members: [],
      loading: false,
      currentUserId: null,
      
      showEdit: false,
      saving: false,
      editForm: {
        name: '',
        description: ''
      },
      
      showAddMember: false,
      adding: false,
      searchEmail: '',
      searchResults: [],
      selectedUser: null,
      newMemberRole: 'member',
      searchTimer: null
    };
  },
  onLoad(options) {
    this.orgId = parseInt(options.id);
    this.currentUserId = getCurrentUser()?.id;
    this.fetchOrganizationDetail();
  },
  onShow() {
    if (this.orgId) {
      this.fetchOrganizationDetail();
    }
  },
  methods: {
    async fetchOrganizationDetail() {
      if (!this.orgId) return;
      
      this.loading = true;
      try {
        const result = await api.get(`/llm/organizations/${this.orgId}`);
        if (result && (result.code === '0000' || result.code === 'SUCCESS')) {
          this.orgInfo = result.data || {};
          this.members = this.orgInfo.members || [];
        }
      } catch (error) {
        console.error('获取组织详情失败:', error);
        api.showError('获取组织详情失败');
      } finally {
        this.loading = false;
      }
    },
    
    formatDate(dateStr) {
      if (!dateStr) return '';
      const date = new Date(dateStr);
      return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
    },
    
    getAvatarText(name) {
      if (!name) return '?';
      return name.charAt(0).toUpperCase();
    },
    
    showEditDialog() {
      this.editForm = {
        name: this.orgInfo.name || '',
        description: this.orgInfo.description || ''
      };
      this.showEdit = true;
    },
    
    hideEditDialog() {
      this.showEdit = false;
    },
    
    async updateOrganization() {
      if (!this.editForm.name.trim()) {
        api.showError('请输入组织名称');
        return;
      }
      
      this.saving = true;
      try {
        const result = await api.put(`/llm/organizations/${this.orgId}`, {
          name: this.editForm.name.trim(),
          description: this.editForm.description.trim() || null
        });
        
        if (result && (result.code === '0000' || result.code === 'SUCCESS')) {
          api.showSuccess('更新成功');
          this.showEdit = false;
          this.fetchOrganizationDetail();
        }
      } catch (error) {
        console.error('更新组织失败:', error);
        api.showError('更新组织失败');
      } finally {
        this.saving = false;
      }
    },
    
    showAddMemberDialog() {
      this.searchEmail = '';
      this.searchResults = [];
      this.selectedUser = null;
      this.newMemberRole = 'member';
      this.showAddMember = true;
    },
    
    hideAddMemberDialog() {
      this.showAddMember = false;
    },
    
    searchUsers() {
      if (this.searchTimer) {
        clearTimeout(this.searchTimer);
      }
      
      this.searchTimer = setTimeout(async () => {
        if (!this.searchEmail || this.searchEmail.length < 2) {
          this.searchResults = [];
          return;
        }
        
        try {
          const result = await api.get('/llm/users/search', {
            email: this.searchEmail,
            limit: 5
          });
          
          if (result && (result.code === '0000' || result.code === 'SUCCESS')) {
            this.searchResults = result.data || [];
          }
        } catch (error) {
          console.error('搜索用户失败:', error);
        }
      }, 300);
    },
    
    selectUser(user) {
      this.selectedUser = user;
      this.searchResults = [];
      this.searchEmail = '';
    },
    
    async addMember() {
      if (!this.selectedUser) {
        api.showError('请选择要添加的用户');
        return;
      }
      
      this.adding = true;
      try {
        const result = await api.post(`/llm/organizations/${this.orgId}/members`, {
          user_id: this.selectedUser.id,
          role: this.newMemberRole
        });
        
        if (result && (result.code === '0000' || result.code === 'SUCCESS')) {
          api.showSuccess('添加成功');
          this.showAddMember = false;
          this.fetchOrganizationDetail();
        }
      } catch (error) {
        console.error('添加成员失败:', error);
        api.showError('添加成员失败');
      } finally {
        this.adding = false;
      }
    },
    
    confirmRemoveMember(member) {
      uni.showModal({
        title: '确认移除',
        content: `确定要将 ${member.name} 移出组织吗？`,
        success: async (res) => {
          if (res.confirm) {
            await this.removeMember(member.user_id);
          }
        }
      });
    },
    
    async removeMember(userId) {
      try {
        const result = await api.delete(`/llm/organizations/${this.orgId}/members/${userId}`);
        if (result && (result.code === '0000' || result.code === 'SUCCESS')) {
          api.showSuccess('移除成功');
          this.fetchOrganizationDetail();
        }
      } catch (error) {
        console.error('移除成员失败:', error);
        api.showError('移除成员失败');
      }
    },
    
    confirmLeave() {
      uni.showModal({
        title: '确认退出',
        content: '确定要退出该组织吗？',
        success: async (res) => {
          if (res.confirm) {
            await this.leaveOrganization();
          }
        }
      });
    },
    
    async leaveOrganization() {
      try {
        const result = await api.delete(`/llm/organizations/${this.orgId}/members`);
        if (result && (result.code === '0000' || result.code === 'SUCCESS')) {
          api.showSuccess('已退出组织');
          setTimeout(() => {
            uni.navigateBack();
          }, 1000);
        }
      } catch (error) {
        console.error('退出组织失败:', error);
        api.showError('退出组织失败');
      }
    },
    
    confirmDissolve() {
      uni.showModal({
        title: '确认解散',
        content: '解散组织将删除所有数据，此操作不可恢复！确定要解散吗？',
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
        if (result && (result.code === '0000' || result.code === 'SUCCESS')) {
          api.showSuccess('组织已解散');
          setTimeout(() => {
            uni.navigateBack();
          }, 1000);
        }
      } catch (error) {
        console.error('解散组织失败:', error);
        api.showError('解散组织失败');
      }
    }
  }
};
</script>

<style>
.detail-container {
  padding: 30rpx;
  background-color: #f5f7fa;
  min-height: 100vh;
}

.loading-state {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 100rpx 0;
  color: #999;
}

.info-section, .member-section {
  background-color: #fff;
  border-radius: 16rpx;
  padding: 30rpx;
  margin-bottom: 20rpx;
  box-shadow: 0 2rpx 20rpx rgba(0, 0, 0, 0.08);
}

.info-header, .section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20rpx;
  padding-bottom: 20rpx;
  border-bottom: 1rpx solid #f0f0f0;
}

.info-title, .section-title {
  font-size: 30rpx;
  font-weight: 600;
  color: #333;
}

.edit-btn, .add-btn {
  background-color: #007bff;
  color: #fff;
  font-size: 24rpx;
  padding: 10rpx 24rpx;
  border-radius: 20rpx;
  border: none;
}

.info-item {
  display: flex;
  padding: 16rpx 0;
}

.info-label {
  width: 160rpx;
  font-size: 28rpx;
  color: #999;
  flex-shrink: 0;
}

.info-value {
  flex: 1;
  font-size: 28rpx;
  color: #333;
}

.member-list {
  display: flex;
  flex-direction: column;
}

.member-item {
  display: flex;
  align-items: center;
  padding: 20rpx 0;
  border-bottom: 1rpx solid #f5f7fa;
}

.member-item:last-child {
  border-bottom: none;
}

.member-avatar {
  width: 80rpx;
  height: 80rpx;
  border-radius: 50%;
  background-color: #007bff;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 20rpx;
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
  margin-bottom: 6rpx;
}

.member-email {
  font-size: 24rpx;
  color: #999;
}

.member-role {
  margin-right: 20rpx;
}

.role-tag {
  font-size: 22rpx;
  padding: 6rpx 16rpx;
  border-radius: 20rpx;
}

.role-tag.admin {
  background-color: rgba(0, 123, 255, 0.1);
  color: #007bff;
}

.role-tag.member {
  background-color: rgba(108, 117, 125, 0.1);
  color: #6c757d;
}

.remove-btn {
  background-color: transparent;
  color: #dc3545;
  font-size: 24rpx;
  padding: 10rpx 20rpx;
  border: 1rpx solid #dc3545;
  border-radius: 20rpx;
}

.action-section {
  margin-top: 40rpx;
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.leave-btn, .dissolve-btn {
  width: 100%;
  height: 88rpx;
  border-radius: 44rpx;
  font-size: 28rpx;
  border: none;
}

.leave-btn {
  background-color: #fff;
  color: #666;
  border: 1rpx solid #ddd;
}

.dissolve-btn {
  background-color: #fff;
  color: #dc3545;
  border: 1rpx solid #dc3545;
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
  max-height: 80vh;
  background-color: #fff;
  border-radius: 20rpx;
  padding: 40rpx;
  overflow-y: auto;
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

.search-results {
  max-height: 300rpx;
  overflow-y: auto;
  background-color: #f5f7fa;
  border-radius: 12rpx;
  margin-bottom: 20rpx;
}

.search-item {
  padding: 20rpx 24rpx;
  border-bottom: 1rpx solid #eee;
}

.search-item:last-child {
  border-bottom: none;
}

.search-name {
  font-size: 28rpx;
  color: #333;
  display: block;
  margin-bottom: 6rpx;
}

.search-email {
  font-size: 24rpx;
  color: #999;
}

.selected-user {
  background-color: rgba(0, 123, 255, 0.1);
  padding: 16rpx 24rpx;
  border-radius: 12rpx;
  margin-bottom: 20rpx;
}

.selected-label {
  font-size: 24rpx;
  color: #007bff;
}

.selected-name {
  font-size: 26rpx;
  color: #333;
}

.role-options {
  display: flex;
  gap: 20rpx;
}

.role-option {
  flex: 1;
  height: 80rpx;
  background-color: #f5f7fa;
  border-radius: 12rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28rpx;
  color: #666;
}

.role-option.active {
  background-color: #007bff;
  color: #fff;
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
