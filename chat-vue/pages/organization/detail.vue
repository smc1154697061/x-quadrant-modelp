<template>
  <app-layout title="组织详情">
    <view class="org-detail-container">
      <!-- 返回按钮 -->
      <view class="back-section">
        <view class="back-btn" @tap="goBack">
          <text class="back-icon">‹</text>
          <text class="back-text">返回组织列表</text>
        </view>
      </view>

      <!-- 加载状态 -->
      <view v-if="loading" class="loading-state">
        <text>加载中...</text>
      </view>

      <!-- 组织信息卡片 -->
      <view v-else-if="organization" class="org-info-card">
        <view class="org-info-header">
          <view class="org-avatar-large">
            <text class="org-avatar-text">{{ getOrgInitials(organization.name) }}</text>
          </view>
          <view class="org-info-main">
            <text class="org-name-large">{{ organization.name }}</text>
            <text class="org-meta">创建于 {{ formatDate(organization.created_at) }}</text>
          </view>
          <view v-if="isAdmin" class="org-actions">
            <button class="action-btn edit-btn" @tap="showEditDialog">编辑</button>
            <button class="action-btn danger-btn" @tap="confirmDissolve">解散</button>
          </view>
        </view>

        <view class="org-info-body">
          <view class="info-section">
            <text class="info-label">组织描述</text>
            <text class="info-value">{{ organization.description || '暂无描述' }}</text>
          </view>

          <view class="info-section">
            <text class="info-label">我的角色</text>
            <view class="role-badge-large" :class="`role-${organization.my_role}`">
              {{ formatRole(organization.my_role) }}
            </view>
          </view>
        </view>
      </view>

      <!-- 成员列表 -->
      <view v-if="organization" class="members-section">
        <view class="section-header">
          <text class="section-title">组织成员</text>
          <text class="member-count">{{ members.length }} 人</text>
        </view>

        <view v-if="membersLoading" class="loading-state">
          <text>加载成员中...</text>
        </view>

        <view v-else-if="members.length === 0" class="empty-state-small">
          <text>暂无成员</text>
        </view>

        <view v-else class="members-list">
          <view
            v-for="member in members"
            :key="member.id"
            class="member-item"
          >
            <view class="member-avatar">
              <image
                v-if="member.avatar"
                :src="member.avatar"
                mode="aspectFill"
                class="avatar-img"
              />
              <text v-else class="avatar-text">{{ getInitials(member.nickname || member.email) }}</text>
            </view>
            <view class="member-info">
              <text class="member-name">{{ member.nickname || member.email }}</text>
              <text class="member-email">{{ member.email }}</text>
            </view>
            <view class="member-role">
              <text class="role-tag" :class="`role-${member.role}`">{{ formatRole(member.role) }}</text>
            </view>
          </view>
        </view>
      </view>

      <!-- 编辑组织弹窗 -->
      <view v-if="showEditOrg" class="dialog-overlay" @tap="closeEditDialog">
        <view class="dialog-content" @tap.stop>
          <view class="dialog-header">
            <text class="dialog-title">编辑组织</text>
            <text class="dialog-close" @tap="closeEditDialog">×</text>
          </view>

          <view class="dialog-body">
            <view class="form-item">
              <text class="form-label">组织名称 <text class="required">*</text></text>
              <input
                type="text"
                v-model="editOrg.name"
                placeholder="请输入组织名称"
                class="form-input"
                maxlength="50"
              />
            </view>

            <view class="form-item">
              <text class="form-label">组织描述</text>
              <textarea
                v-model="editOrg.description"
                placeholder="请输入组织描述（选填）"
                class="form-textarea"
                maxlength="200"
              />
            </view>
          </view>

          <view class="dialog-footer">
            <button class="btn-cancel" @tap="closeEditDialog">取消</button>
            <button
              class="btn-confirm"
              :disabled="!editOrg.name.trim() || saving"
              @tap="confirmEditOrg"
            >
              <text v-if="saving">保存中...</text>
              <text v-else>保存</text>
            </button>
          </view>
        </view>
      </view>

      <!-- 登录弹窗 -->
      <login-dialog
        v-model:visible="loginVisible"
        @login-success="onLoginSuccess"
        @update:visible="onLoginVisibleChange"
      />
    </view>
  </app-layout>
</template>

<script>
import AppLayout from '../../components/layout/AppLayout.vue';
import LoginDialog from '../../components/user/LoginDialog.vue';
import api from '../../utils/api.js';
import { getCurrentUser } from '../../utils/auth.js';

export default {
  components: {
    AppLayout,
    LoginDialog
  },
  data() {
    return {
      orgId: null,
      organization: null,
      members: [],
      loading: false,
      membersLoading: false,
      showEditOrg: false,
      saving: false,
      editOrg: {
        name: '',
        description: ''
      },
      userInfo: null,
      loginVisible: false
    };
  },
  computed: {
    isLoggedIn() {
      return !!this.userInfo && !!this.userInfo.id;
    },
    isAdmin() {
      return this.organization && (this.organization.my_role === 'owner' || this.organization.my_role === 'admin');
    },
    isOwner() {
      return this.organization && this.organization.my_role === 'owner';
    }
  },
  onLoad(options) {
    if (options && options.id) {
      this.orgId = options.id;
      this.userInfo = getCurrentUser();
      this.fetchOrganizationDetail();
      this.fetchMembers();
    } else {
      uni.showToast({
        title: '无效的组织ID',
        icon: 'none'
      });
      setTimeout(() => {
        uni.navigateBack();
      }, 1500);
    }

    // 监听用户信息更新
    uni.$on('userInfoUpdated', this.handleUserInfoUpdated);
  },
  onUnload() {
    uni.$off('userInfoUpdated', this.handleUserInfoUpdated);
  },
  onPullDownRefresh() {
    this.fetchOrganizationDetail();
    this.fetchMembers();
    setTimeout(() => {
      uni.stopPullDownRefresh();
    }, 1000);
  },
  methods: {
    // 获取组织详情
    async fetchOrganizationDetail() {
      if (!this.orgId) return;

      this.loading = true;
      try {
        const result = await api.get(`/organizations/${this.orgId}`);
        if (result && (result.code === '0000' || result.code === 'SUCCESS')) {
          this.organization = result.data;
        } else {
          if (result?.code === 'UNAUTHORIZED') {
            this.loginVisible = true;
          } else {
            uni.showToast({
              title: result?.message || '获取组织详情失败',
              icon: 'none'
            });
          }
        }
      } catch (error) {
        console.error('获取组织详情失败:', error);
        uni.showToast({
          title: '获取组织详情失败',
          icon: 'none'
        });
      } finally {
        this.loading = false;
      }
    },

    // 获取成员列表
    async fetchMembers() {
      if (!this.orgId) return;

      this.membersLoading = true;
      try {
        const result = await api.get(`/organizations/${this.orgId}/members`);
        if (result && (result.code === '0000' || result.code === 'SUCCESS')) {
          this.members = result.data || [];
        } else {
          this.members = [];
        }
      } catch (error) {
        console.error('获取成员列表失败:', error);
        this.members = [];
      } finally {
        this.membersLoading = false;
      }
    },

    // 获取组织名称首字母
    getOrgInitials(name) {
      if (!name) return '?';
      return name.charAt(0).toUpperCase();
    },

    // 获取用户名称首字母
    getInitials(name) {
      if (!name) return '?';
      return name.charAt(0).toUpperCase();
    },

    // 格式化角色
    formatRole(role) {
      const roleMap = {
        'owner': '创建者',
        'admin': '管理员',
        'member': '成员'
      };
      return roleMap[role] || role;
    },

    // 格式化日期
    formatDate(dateStr) {
      if (!dateStr) return '-';
      const date = new Date(dateStr);
      return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
    },

    // 返回上一页
    goBack() {
      uni.navigateBack();
    },

    // 显示编辑弹窗
    showEditDialog() {
      if (!this.isAdmin) {
        api.showError('只有管理员可以编辑组织信息');
        return;
      }
      this.editOrg = {
        name: this.organization.name,
        description: this.organization.description || ''
      };
      this.showEditOrg = true;
    },

    // 关闭编辑弹窗
    closeEditDialog() {
      this.showEditOrg = false;
      this.editOrg = { name: '', description: '' };
    },

    // 确认编辑组织
    async confirmEditOrg() {
      if (!this.editOrg.name.trim()) {
        api.showError('请输入组织名称');
        return;
      }

      this.saving = true;
      try {
        const result = await api.put(`/organizations/${this.orgId}`, {
          name: this.editOrg.name.trim(),
          description: this.editOrg.description.trim()
        });

        if (result && (result.code === '0000' || result.code === 'SUCCESS')) {
          api.showSuccess('组织信息更新成功');
          this.closeEditDialog();
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

    // 确认解散组织
    confirmDissolve() {
      if (!this.isOwner) {
        api.showError('只有创建者可以解散组织');
        return;
      }

      uni.showModal({
        title: '确认解散',
        content: '解散组织将删除所有相关数据，此操作不可恢复！确定要解散吗？',
        confirmColor: '#f44336',
        success: (res) => {
          if (res.confirm) {
            this.dissolveOrganization();
          }
        }
      });
    },

    // 解散组织
    async dissolveOrganization() {
      try {
        const result = await api.delete(`/organizations/${this.orgId}`);

        if (result && (result.code === '0000' || result.code === 'SUCCESS')) {
          api.showSuccess('组织已解散');
          setTimeout(() => {
            uni.navigateBack();
          }, 1500);
        } else {
          api.showError(result?.message || '解散组织失败');
        }
      } catch (error) {
        console.error('解散组织失败:', error);
        api.showError('解散组织失败');
      }
    },

    // 处理用户信息更新
    handleUserInfoUpdated(userInfo) {
      this.userInfo = userInfo;
      if (this.isLoggedIn) {
        this.fetchOrganizationDetail();
        this.fetchMembers();
      } else {
        uni.navigateBack();
      }
    },

    // 登录成功回调
    onLoginSuccess(userInfo) {
      this.userInfo = userInfo;
      this.fetchOrganizationDetail();
      this.fetchMembers();
    },

    // 登录弹窗可见性变化
    onLoginVisibleChange(visible) {
      this.loginVisible = visible;
    }
  }
};
</script>

<style>
.org-detail-container {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

/* 返回按钮 */
.back-section {
  margin-bottom: 20px;
}

.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background-color: #f5f5f5;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.back-btn:hover {
  background-color: #e8e8e8;
}

.back-icon {
  font-size: 20px;
  color: #666;
}

.back-text {
  font-size: 14px;
  color: #666;
}

/* 加载状态 */
.loading-state {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 40px;
  color: #999;
  font-size: 14px;
}

/* 组织信息卡片 */
.org-info-card {
  background-color: white;
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  margin-bottom: 24px;
}

.org-info-header {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.org-avatar-large {
  width: 80px;
  height: 80px;
  background-color: rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.org-avatar-text {
  font-size: 36px;
  font-weight: 700;
  color: white;
}

.org-info-main {
  flex: 1;
  min-width: 0;
}

.org-name-large {
  font-size: 24px;
  font-weight: 600;
  color: white;
  margin-bottom: 8px;
  display: block;
}

.org-meta {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.8);
}

.org-actions {
  display: flex;
  gap: 12px;
}

.action-btn {
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 13px;
  border: none;
  cursor: pointer;
  transition: all 0.2s;
}

.edit-btn {
  background-color: rgba(255, 255, 255, 0.9);
  color: #667eea;
}

.edit-btn:hover {
  background-color: white;
}

.danger-btn {
  background-color: rgba(244, 67, 54, 0.9);
  color: white;
}

.danger-btn:hover {
  background-color: #f44336;
}

.org-info-body {
  padding: 24px;
}

.info-section {
  margin-bottom: 20px;
}

.info-section:last-child {
  margin-bottom: 0;
}

.info-label {
  font-size: 13px;
  color: #999;
  margin-bottom: 8px;
  display: block;
}

.info-value {
  font-size: 15px;
  color: #333;
  line-height: 1.6;
}

.role-badge-large {
  display: inline-block;
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
}

.role-badge-large.role-owner {
  background-color: #fff8e6;
  color: #f59e0b;
}

.role-badge-large.role-admin {
  background-color: #e6f4ff;
  color: #3b82f6;
}

.role-badge-large.role-member {
  background-color: #e6fff0;
  color: #10b981;
}

/* 成员列表 */
.members-section {
  background-color: white;
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #f0f0f0;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.member-count {
  font-size: 14px;
  color: #999;
}

.empty-state-small {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 40px;
  color: #999;
  font-size: 14px;
}

.members-list {
  padding: 8px 0;
}

.member-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 24px;
  border-bottom: 1px solid #f5f5f5;
  transition: background-color 0.2s;
}

.member-item:last-child {
  border-bottom: none;
}

.member-item:hover {
  background-color: #fafafa;
}

.member-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  overflow: hidden;
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-text {
  font-size: 18px;
  font-weight: 600;
  color: white;
}

.member-info {
  flex: 1;
  min-width: 0;
}

.member-name {
  font-size: 15px;
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
  display: block;
}

.member-email {
  font-size: 13px;
  color: #999;
}

.member-role {
  flex-shrink: 0;
}

.role-tag {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.role-tag.role-owner {
  background-color: #fff8e6;
  color: #f59e0b;
}

.role-tag.role-admin {
  background-color: #e6f4ff;
  color: #3b82f6;
}

.role-tag.role-member {
  background-color: #e6fff0;
  color: #10b981;
}

/* 弹窗样式 */
.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.dialog-content {
  background-color: white;
  border-radius: 16px;
  width: 90%;
  max-width: 480px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  overflow: hidden;
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #f0f0f0;
}

.dialog-title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.dialog-close {
  font-size: 24px;
  color: #999;
  cursor: pointer;
  padding: 0 4px;
}

.dialog-body {
  padding: 24px;
}

.form-item {
  margin-bottom: 20px;
}

.form-item:last-child {
  margin-bottom: 0;
}

.form-label {
  display: block;
  font-size: 14px;
  color: #333;
  margin-bottom: 8px;
  font-weight: 500;
}

.required {
  color: #f44336;
}

.form-input,
.form-textarea {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
  background-color: #fafafa;
  box-sizing: border-box;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.form-input:focus,
.form-textarea:focus {
  border-color: var(--primary-color, #007AFF);
  box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.1);
  background-color: white;
}

.form-textarea {
  min-height: 100px;
  resize: vertical;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid #f0f0f0;
  background-color: #fafafa;
}

.btn-cancel,
.btn-confirm {
  padding: 10px 24px;
  border-radius: 8px;
  font-size: 14px;
  border: none;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-cancel {
  background-color: #f0f0f0;
  color: #666;
}

.btn-cancel:hover {
  background-color: #e0e0e0;
}

.btn-confirm {
  background-color: var(--primary-color, #007AFF);
  color: white;
}

.btn-confirm:hover {
  background-color: #0056b3;
}

.btn-confirm[disabled] {
  background-color: #ccc;
  color: #666;
  cursor: not-allowed;
}

/* 响应式设计 */
@media screen and (max-width: 767px) {
  .org-detail-container {
    padding: 16px;
  }

  .org-info-header {
    flex-direction: column;
    text-align: center;
    gap: 16px;
  }

  .org-actions {
    width: 100%;
    justify-content: center;
  }

  .member-item {
    padding: 12px 16px;
  }

  .dialog-content {
    width: 95%;
  }
}
</style>
