<template>
  <app-layout title="生成结果">
    <view class="result-container">
      <!-- 加载中 -->
      <view v-if="loading" class="loading-state">
        <view class="loading-spinner"></view>
        <text class="loading-text">正在加载...</text>
      </view>
      
      <!-- 结果展示 -->
      <view v-else-if="generation" class="result-content">
        <!-- 头部信息 -->
        <view class="result-header">
          <view class="header-info">
            <text class="result-title">生成成功</text>
            <text class="result-meta">{{ formatDate(generation.created_at) }}</text>
          </view>
          <view class="status-badge" :class="generation.status">
            <text>{{ statusText }}</text>
          </view>
        </view>
        
        <!-- 模板信息 -->
        <view class="template-info-card">
          <view class="info-row">
            <text class="info-label">使用模板</text>
            <text class="info-value">{{ generation.template_name }}</text>
          </view>
          <view class="info-row">
            <text class="info-label">模板标签</text>
            <text class="info-value">{{ generation.template_tags || '无' }}</text>
          </view>
        </view>
        
        <!-- 生成的内容 -->
        <view class="content-section">
          <view class="section-header">
            <text class="section-title">生成内容</text>
            <view class="copy-btn" @tap="copyContent">
              <text class="copy-icon">[复制]</text>
              <text>复制</text>
            </view>
          </view>
          
          <view class="content-box">
            <text class="content-text">{{ generation.generated_content }}</text>
          </view>
        </view>
        
        <!-- 操作按钮 -->
        <view class="action-section">
          <view class="action-btn secondary" @tap="regenerate">
            <text class="btn-icon">[刷新]</text>
            <text class="btn-text">重新生成</text>
          </view>
          <view class="action-btn primary" @tap="downloadDocument">
            <text class="btn-icon">[下载]</text>
            <text class="btn-text">下载文档</text>
          </view>
        </view>
      </view>
      
      <!-- 错误状态 -->
      <view v-else class="error-state">
        <text class="error-icon">[警告]</text>
        <text class="error-text">加载失败</text>
        <text class="error-subtext">请检查网络连接后重试</text>
        <view class="retry-btn" @tap="loadGeneration">
          <text>重新加载</text>
        </view>
      </view>
      
      <!-- 下载选项弹窗 -->
      <uni-popup ref="downloadPopup" type="center">
        <view class="download-modal">
          <view class="modal-header">
            <text class="modal-title">选择下载格式</text>
            <text class="modal-close" @tap="closeDownloadModal">×</text>
          </view>
          
          <view class="modal-body">
            <view class="format-option" @tap="downloadAs('word')">
              <view class="format-icon word">W</view>
              <view class="format-info">
                <text class="format-name">Word 文档</text>
                <text class="format-desc">.docx 格式，可编辑</text>
              </view>
            </view>

            <view class="format-option" @tap="downloadAs('pdf')">
              <view class="format-icon pdf">P</view>
              <view class="format-info">
                <text class="format-name">PDF 文档</text>
                <text class="format-desc">.pdf 格式，适合打印</text>
              </view>
            </view>
          </view>
        </view>
      </uni-popup>
    </view>
  </app-layout>
</template>

<script>
import AppLayout from '../../../components/layout/AppLayout.vue';
import api from '../../../utils/api.js';

export default {
  components: {
    AppLayout
  },
  data() {
    return {
      generationId: null,
      generation: null,
      loading: true
    };
  },
  computed: {
    statusText() {
      const statusMap = {
        'pending': '等待中',
        'generating': '生成中',
        'completed': '已完成',
        'failed': '失败'
      };
      return statusMap[this.generation?.status] || this.generation?.status;
    }
  },
  onLoad(options) {
    if (options.generationId) {
      this.generationId = options.generationId;
      this.loadGeneration();
    } else {
      this.loading = false;
      uni.showToast({ title: '参数错误', icon: 'none' });
    }
  },
  methods: {
    // 加载生成记录
    async loadGeneration() {
      this.loading = true;
      
      try {
        const res = await api.get(`/llm/generations/${this.generationId}`);
        if (res.code === 'SUCCESS') {
          this.generation = res.data;
        } else {
          uni.showToast({ title: res.message || '加载失败', icon: 'none' });
        }
      } catch (e) {
        console.error('加载生成记录失败:', e);
        uni.showToast({ title: '加载失败', icon: 'none' });
      } finally {
        this.loading = false;
      }
    },
    
    // 格式化日期
    formatDate(dateStr) {
      if (!dateStr) return '';
      const date = new Date(dateStr);
      return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
    },
    
    // 复制内容
    copyContent() {
      if (!this.generation?.generated_content) return;
      
      uni.setClipboardData({
        data: this.generation.generated_content,
        success: () => {
          uni.showToast({ title: '已复制到剪贴板', icon: 'success' });
        }
      });
    },
    
    // 重新生成
    regenerate() {
      uni.navigateBack();
    },
    
    // 显示下载选项
    downloadDocument() {
      this.$refs.downloadPopup.open();
    },
    
    // 关闭下载弹窗
    closeDownloadModal() {
      this.$refs.downloadPopup.close();
    },
    
    // 下载文档
    async downloadAs(format) {
      this.closeDownloadModal();
      
      uni.showLoading({ title: '准备下载...' });
      
      try {
        // 这里需要后端支持生成并返回文件
        // 暂时使用复制内容的方式
        uni.hideLoading();
        
        uni.showModal({
          title: '提示',
          content: '文档内容已生成，您可以复制内容后手动保存为文档。',
          showCancel: false,
          confirmText: '复制内容',
          success: (res) => {
            if (res.confirm) {
              this.copyContent();
            }
          }
        });
      } catch (e) {
        console.error('下载失败:', e);
        uni.hideLoading();
        uni.showToast({ title: '下载失败', icon: 'none' });
      }
    }
  }
};
</script>

<style scoped>
.result-container {
  min-height: 100vh;
  background-color: #f5f7fa;
  padding: 20rpx;
  padding-bottom: 140rpx;
}

/* 加载状态 */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 200rpx 40rpx;
}

.loading-spinner {
  width: 60rpx;
  height: 60rpx;
  border: 4rpx solid #f0f0f0;
  border-top-color: #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 20rpx;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.loading-text {
  font-size: 28rpx;
  color: #999;
}

/* 结果头部 */
.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
  margin-bottom: 20rpx;
}

.header-info {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.result-title {
  font-size: 36rpx;
  font-weight: 600;
  color: #333;
}

.result-meta {
  font-size: 24rpx;
  color: #999;
}

.status-badge {
  padding: 8rpx 20rpx;
  border-radius: 8rpx;
  font-size: 24rpx;
}

.status-badge.completed {
  background: #e6f7ff;
  color: #007bff;
}

.status-badge.failed {
  background: #fff1f0;
  color: #ff4d4f;
}

.status-badge.generating {
  background: #fff7e6;
  color: #fa8c16;
}

/* 模板信息卡片 */
.template-info-card {
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
  margin-bottom: 20rpx;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16rpx 0;
  border-bottom: 2rpx solid #f0f0f0;
}

.info-row:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.info-label {
  font-size: 28rpx;
  color: #666;
}

.info-value {
  font-size: 28rpx;
  color: #333;
  font-weight: 500;
}

/* 内容区域 */
.content-section {
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
  margin-bottom: 20rpx;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20rpx;
}

.section-title {
  font-size: 30rpx;
  font-weight: 600;
  color: #333;
}

.copy-btn {
  display: flex;
  align-items: center;
  gap: 8rpx;
  padding: 12rpx 20rpx;
  background: #f5f7fa;
  border-radius: 8rpx;
}

.copy-btn text {
  font-size: 26rpx;
  color: #666;
}

.copy-icon {
  font-size: 28rpx;
}

.content-box {
  background: #f8f9fa;
  border-radius: 12rpx;
  padding: 24rpx;
  max-height: 600rpx;
  overflow-y: auto;
}

.content-text {
  font-size: 28rpx;
  color: #333;
  line-height: 1.8;
  white-space: pre-wrap;
  word-break: break-all;
}

/* 操作按钮 */
.action-section {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  gap: 20rpx;
  padding: 20rpx 40rpx 40rpx;
  background: #fff;
  box-shadow: 0 -4rpx 20rpx rgba(0, 0, 0, 0.08);
}

.action-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12rpx;
  padding: 24rpx 0;
  border-radius: 12rpx;
}

.action-btn.secondary {
  background: #f5f7fa;
}

.action-btn.secondary .btn-text {
  color: #666;
}

.action-btn.primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.action-btn.primary .btn-text {
  color: #fff;
}

.btn-icon {
  font-size: 32rpx;
}

.btn-text {
  font-size: 30rpx;
  font-weight: 500;
}

/* 错误状态 */
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 200rpx 40rpx;
}

.error-icon {
  font-size: 100rpx;
  margin-bottom: 20rpx;
}

.error-text {
  font-size: 32rpx;
  color: #333;
  margin-bottom: 10rpx;
}

.error-subtext {
  font-size: 26rpx;
  color: #999;
  margin-bottom: 40rpx;
}

.retry-btn {
  padding: 20rpx 60rpx;
  background: #007bff;
  border-radius: 12rpx;
}

.retry-btn text {
  font-size: 28rpx;
  color: #fff;
}

/* 下载弹窗 */
.download-modal {
  background: #fff;
  border-radius: 20rpx;
  width: 600rpx;
  max-width: 90vw;
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 30rpx;
  border-bottom: 2rpx solid #f0f0f0;
}

.modal-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
}

.modal-close {
  font-size: 40rpx;
  color: #999;
  padding: 0 10rpx;
}

.modal-body {
  padding: 20rpx;
}

.format-option {
  display: flex;
  align-items: center;
  gap: 20rpx;
  padding: 24rpx;
  border-radius: 12rpx;
  margin-bottom: 16rpx;
  background: #f8f9fa;
}

.format-option:last-child {
  margin-bottom: 0;
}

.format-icon {
  font-size: 60rpx;
  width: 80rpx;
  height: 80rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
  border-radius: 12rpx;
  flex-shrink: 0;
}

.format-info {
  flex: 1;
}

.format-name {
  font-size: 30rpx;
  font-weight: 500;
  color: #333;
  display: block;
  margin-bottom: 8rpx;
}

.format-desc {
  font-size: 24rpx;
  color: #999;
}
</style>
