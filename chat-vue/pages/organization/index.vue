<template>
  <app-layout title="我的组织">
    <view class="organization-container">
      <!-- 页面头部 -->
      <view class="page-header">
        <view class="header-left">
          <text class="page-title">我的组织</text>
          <text class="page-subtitle">管理您所属的组织</text>
        </view>
        <button class="create-btn" @tap="showCreateDialog">创建组织</button>
      </view>

      <!-- 加载状态 -->
      <view v-if="loading" class="loading-state">
        <text>加载中...</text>
      </view>

      <!-- 空状态 -->
      <view v-else-if="organizations.length === 0" class="empty-state">
        <image class="empty-icon" src="/static/images/organization.png" mode="aspectFit"></image>
        <text class="empty-text">暂无组织</text>
        <text class="empty-subtext">创建一个组织开始协作</text>
        <button class="create-empty-btn" @tap="showCreateDialog">创建组织</button>
      </view>

      <!-- 组织列表 -->
      <view v-else class="org-grid">
        <view
          v-for="org in organizations"
          :key="org.id"
          class="org-card"
          @tap="navigateToDetail(org.id)"
        >
          <view class="org-card-header">
            <view class="org-avatar">
              <text class="org-avatar-text">{{ getOrgInitials(org.name) }}</text>
            </view>
            <view class="org-role-badge" :class="`role-${org.my_role}`">
              {{ formatRole(org.my_role) }}
            </view>
          </view>

          <view class="org-card-body">
            <text class="org-name">{{ org.name }}</text>
            <text class="org-description">{{ org.description || '暂无描述' }}</text>
          </view>

          <view class="org-card-footer">
            <view class="org-stat">
              <text class="stat-icon">👥</text>
              <text class="stat-text">{{ org.member_count || 0 }} 成员</text>
            </view>
            <text class="org-arrow">›</text>
          </view>
        </view>
      </view>

      <!-- 创建组织弹窗 -->
      <view v-if="showCreateOrg" class="dialog-overlay" @tap="closeCreateDialog">
        <view class="dialog-content" @tap.stop>
          <view class="dialog-header">
            <text class="dialog-title">创建组织</text>
            <text class="dialog-close" @tap="closeCreateDialog">×</text>
          </view>

          <view class="dialog-body">
            <view class="form-item">
              <text class="form-label">组织名称 <text class="required">*</text></text>
              <input
                type="text"
                v-model="newOrg.name"
                placeholder="请输入组织名称"
                class="form-input"
                maxlength="50"
              />
            </view>

            <view class="form-item">
              <text class="form-label">组织描述</text>
              <textarea
                v-model="newOrg.description"
                placeholder="请输入组织描述（选填）"
                class="form-textarea"
                maxlength="200"
              />
            </view>
          </view>

          <view class="dialog-footer">
            <button class="btn-cancel" @tap="closeCreateDialog">取消</button>
            <button
              class="btn-confirm"
              :disabled="!newOrg.name.trim() || creating"
              @tap="confirmCreateOrg"
            >
              <text v-if="creating">创建中...</text>
              <text v-else>创建</text>
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
      organizations: [],
      loading: false,
      showCreateOrg: false,
      creating: false,
      newOrg: {
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
    }
  },
  onLoad() {
    this.userInfo = getCurrentUser();
    this.fetchOrganizations();

    // 监听用户信息更新
    uni.$on('userInfoUpdated', this.handleUserInfoUpdated);
  },
  onUnload() {
    uni.$off('userInfoUpdated', this.handleUserInfoUpdated);
  },
  onPullDownRefresh() {
    this.fetchOrganizations();
    setTimeout(() => {
      uni.stopPullDownRefresh();
    }, 1000);
  },
  methods: {
    // 获取组织列表
    async fetchOrganizations() {
      if (!this.isLoggedIn) {
        this.loginVisible = true;
        return;
      }

      this.loading = true;
      try {
        const result = await api.get('/organizations');
        if (result && (result.code === '0000' || result.code === 'SUCCESS')) {
          this.organizations = result.data || [];
        } else {
          this.organizations = [];
          if (result?.code === 'UNAUTHORIZED') {
            this.loginVisible = true;
          }
        }
      } catch (error) {
        console.error('获取组织列表失败:', error);
        this.organizations = [];
      } finally {
        this.loading = false;
      }
    },

    // 获取组织名称首字母
    getOrgInitials(name) {
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

    // 跳转到组织详情
    navigateToDetail(orgId) {
      uni.navigateTo({
        url: `/pages/organization/detail?id=${orgId}`
      });
    },

    // 显示创建组织弹窗
    showCreateDialog() {
      if (!this.isLoggedIn) {
        this.loginVisible = true;
        return;
      }
      this.newOrg = { name: '', description: '' };
      this.showCreateOrg = true;
    },

    // 关闭创建组织弹窗
    closeCreateDialog() {
      this.showCreateOrg = false;
      this.newOrg = { name: '', description: '' };
    },

    // 确认创建组织
    async confirmCreateOrg() {
      if (!this.newOrg.name.trim()) {
        api.showError('请输入组织名称');
        return;
      }

      this.creating = true;
      try {
        const result = await api.post('/organizations', {
          name: this.newOrg.name.trim(),
          description: this.newOrg.description.trim()
        });

        if (result && (result.code === '0000' || result.code === 'SUCCESS')) {
          api.showSuccess('组织创建成功');
          this.closeCreateDialog();
          this.fetchOrganizations();

          // 如果返回了组织ID，跳转到详情页
          if (result.data && result.data.id) {
            setTimeout(() => {
              this.navigateToDetail(result.data.id);
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

    // 处理用户信息更新
    handleUserInfoUpdated(userInfo) {
      this.userInfo = userInfo;
      if (this.isLoggedIn) {
        this.fetchOrganizations();
      } else {
        this.organizations = [];
      }
    },

    // 登录成功回调
    onLoginSuccess(userInfo) {
      this.userInfo = userInfo;
      this.fetchOrganizations();
    },

    // 登录弹窗可见性变化
    onLoginVisibleChange(visible) {
      this.loginVisible = visible;
    }
  }
};
</script>

<style>
.organization-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header-left {
  display: flex;
  flex-direction: column;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #333;
}

.page-subtitle {
  font-size: 14px;
  color: #666;
  margin-top: 4px;
}

.create-btn {
  background-color: var(--primary-color, #007AFF);
  color: white;
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 14px;
  border: none;
}

/* 加载和空状态 */
.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

.empty-icon {
  width: 120px;
  height: 120px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-text {
  font-size: 18px;
  color: #333;
  font-weight: 500;
  margin-bottom: 8px;
}

.empty-subtext {
  font-size: 14px;
  color: #999;
  margin-bottom: 24px;
}

.create-empty-btn {
  background-color: var(--primary-color, #007AFF);
  color: white;
  padding: 12px 32px;
  border-radius: 8px;
  font-size: 14px;
  border: none;
}

/* 组织卡片网格 */
.org-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.org-card {
  background-color: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  transition: transform 0.2s, box-shadow 0.2s;
  cursor: pointer;
}

.org-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.org-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.org-avatar {
  width: 48px;
  height: 48px;
  background-color: rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.org-avatar-text {
  font-size: 24px;
  font-weight: 600;
  color: white;
}

.org-role-badge {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
  background-color: rgba(255, 255, 255, 0.9);
}

.role-owner {
  color: #f59e0b;
}

.role-admin {
  color: #3b82f6;
}

.role-member {
  color: #10b981;
}

.org-card-body {
  padding: 16px;
}

.org-name {
  font-size: 18px;
  font-weight: 600;
  color: #333;
  margin-bottom: 8px;
  display: block;
}

.org-description {
  font-size: 14px;
  color: #666;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.org-card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-top: 1px solid #f0f0f0;
}

.org-stat {
  display: flex;
  align-items: center;
  gap: 6px;
}

.stat-icon {
  font-size: 14px;
}

.stat-text {
  font-size: 13px;
  color: #666;
}

.org-arrow {
  font-size: 20px;
  color: #999;
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
  .organization-container {
    padding: 16px;
  }

  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }

  .create-btn {
    width: 100%;
  }

  .org-grid {
    grid-template-columns: 1fr;
  }

  .dialog-content {
    width: 95%;
  }
}
</style>
