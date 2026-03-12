<template>
  <app-layout title="生成历史">
    <view class="history-container">
      <!-- 统计卡片 -->
      <view class="stats-card">
        <view class="stat-item">
          <text class="stat-number">{{ totalCount }}</text>
          <text class="stat-label">总生成数</text>
        </view>
        <view class="stat-divider"></view>
        <view class="stat-item">
          <text class="stat-number">{{ completedCount }}</text>
          <text class="stat-label">已完成</text>
        </view>
        <view class="stat-divider"></view>
        <view class="stat-item">
          <text class="stat-number">{{ todayCount }}</text>
          <text class="stat-label">今日生成</text>
        </view>
      </view>
      
      <!-- 历史列表 -->
      <scroll-view class="history-list" scroll-y @scrolltolower="loadMore" refresher-enabled :refresher-triggered="refreshing" @refresherrefresh="onRefresh">
        <view v-if="historyList.length === 0 && !loading" class="empty-state">
          <text class="empty-icon">[列表]</text>
          <text class="empty-text">暂无生成记录</text>
          <text class="empty-subtext">快去使用模板生成文档吧</text>
          <view class="go-generate-btn" @tap="goToGenerate">
            <text>去生成</text>
          </view>
        </view>
        
        <view v-else class="history-items">
          <view 
            v-for="item in historyList" 
            :key="item.id"
            class="history-item"
            @tap="viewDetail(item)"
          >
            <view class="item-header">
              <view class="template-info">
                <view class="file-icon" :class="item.output_file_type || 'default'">
                  <text v-if="item.output_file_type === 'word' || (item.template_name && item.template_name.includes('doc'))">W</text>
                  <text v-else-if="item.output_file_type === 'pdf' || (item.template_name && item.template_name.includes('pdf'))">P</text>
                  <text v-else>文</text>
                </view>
                <view class="info-text">
                  <text class="template-name">{{ item.template_name }}</text>
                  <text class="generate-time">{{ formatDate(item.created_at) }}</text>
                </view>
              </view>
              <view class="status-badge" :class="item.status">
                <text>{{ getStatusText(item.status) }}</text>
              </view>
            </view>
            
            <view class="item-preview">
              <text class="preview-text">{{ truncateContent(item.user_input, 50) }}</text>
            </view>
            
            <view class="item-actions">
              <view class="action-btn view" @tap.stop="viewDetail(item)">
                <text>查看</text>
              </view>
              <view v-if="item.status === 'completed'" class="action-btn download" @tap.stop="downloadItem(item)">
                <text>下载</text>
              </view>
            </view>
          </view>
        </view>
        
        <!-- 加载更多 -->
        <view v-if="loading && historyList.length > 0" class="loading-more">
          <text>加载中...</text>
        </view>
        
        <view v-if="!hasMore && historyList.length > 0" class="no-more">
          <text>没有更多了</text>
        </view>
      </scroll-view>
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
      historyList: [],
      loading: false,
      refreshing: false,
      page: 1,
      pageSize: 20,
      total: 0,
      hasMore: true
    };
  },
  computed: {
    totalCount() {
      return this.total;
    },
    completedCount() {
      return this.historyList.filter(item => item.status === 'completed').length;
    },
    todayCount() {
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      return this.historyList.filter(item => {
        const itemDate = new Date(item.created_at);
        return itemDate >= today;
      }).length;
    }
  },
  onLoad() {
    this.loadHistory();
  },
  onShow() {
    // 刷新数据
    this.page = 1;
    this.loadHistory();
  },
  methods: {
    // 加载历史记录
    async loadHistory() {
      if (this.loading || (!this.hasMore && this.page > 1)) return;
      
      this.loading = true;
      
      try {
        const res = await api.get('/llm/generations', {
          page: this.page,
          page_size: this.pageSize
        });
        
        if (res.code === 'SUCCESS') {
          const { list, total } = res.data;
          
          if (this.page === 1) {
            this.historyList = list;
          } else {
            this.historyList = [...this.historyList, ...list];
          }
          
          this.total = total;
          this.hasMore = this.historyList.length < total;
        }
      } catch (e) {
        console.error('加载历史记录失败:', e);
      } finally {
        this.loading = false;
        this.refreshing = false;
      }
    },
    
    // 下拉刷新
    onRefresh() {
      this.refreshing = true;
      this.page = 1;
      this.hasMore = true;
      this.loadHistory();
    },
    
    // 加载更多
    loadMore() {
      if (!this.hasMore || this.loading) return;
      this.page++;
      this.loadHistory();
    },
    
    // 格式化日期
    formatDate(dateStr) {
      if (!dateStr) return '';
      const date = new Date(dateStr);
      const now = new Date();
      const diff = now - date;
      
      // 小于1小时显示"X分钟前"
      if (diff < 3600000) {
        const minutes = Math.floor(diff / 60000);
        return minutes < 1 ? '刚刚' : `${minutes}分钟前`;
      }
      
      // 小于24小时显示"X小时前"
      if (diff < 86400000) {
        const hours = Math.floor(diff / 3600000);
        return `${hours}小时前`;
      }
      
      // 否则显示日期
      return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
    },
    
    // 获取状态文本
    getStatusText(status) {
      const statusMap = {
        'pending': '等待中',
        'generating': '生成中',
        'completed': '已完成',
        'failed': '失败'
      };
      return statusMap[status] || status;
    },
    
    // 截断内容
    truncateContent(content, length) {
      if (!content) return '';
      return content.length > length ? content.substring(0, length) + '...' : content;
    },
    
    // 查看详情
    viewDetail(item) {
      uni.navigateTo({
        url: `/pages/tools/template-result/index?generationId=${item.id}`
      });
    },
    
    // 下载
    downloadItem(item) {
      uni.showModal({
        title: '下载文档',
        content: '文档内容已生成，您可以复制内容后手动保存',
        confirmText: '复制内容',
        success: (res) => {
          if (res.confirm && item.generated_content) {
            uni.setClipboardData({
              data: item.generated_content,
              success: () => {
                uni.showToast({ title: '已复制到剪贴板', icon: 'success' });
              }
            });
          }
        }
      });
    },
    
    // 去生成
    goToGenerate() {
      uni.navigateTo({
        url: '/pages/tools/template-generate/index'
      });
    }
  }
};
</script>

<style scoped>
.history-container {
  min-height: 100vh;
  background-color: #f5f7fa;
  padding: 20rpx;
}

/* 统计卡片 */
.stats-card {
  display: flex;
  justify-content: space-around;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16rpx;
  padding: 40rpx 20rpx;
  margin-bottom: 20rpx;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8rpx;
}

.stat-number {
  font-size: 48rpx;
  font-weight: 700;
  color: #fff;
}

.stat-label {
  font-size: 26rpx;
  color: rgba(255, 255, 255, 0.8);
}

.stat-divider {
  width: 2rpx;
  height: 60rpx;
  background: rgba(255, 255, 255, 0.3);
}

/* 历史列表 */
.history-list {
  height: calc(100vh - 280rpx);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 120rpx 40rpx;
}

.empty-icon {
  font-size: 120rpx;
  margin-bottom: 20rpx;
}

.empty-text {
  font-size: 32rpx;
  color: #333;
  margin-bottom: 10rpx;
}

.empty-subtext {
  font-size: 26rpx;
  color: #999;
  margin-bottom: 40rpx;
}

.go-generate-btn {
  padding: 24rpx 80rpx;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12rpx;
}

.go-generate-btn text {
  font-size: 30rpx;
  color: #fff;
  font-weight: 500;
}

/* 历史项 */
.history-items {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.history-item {
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.08);
}

.item-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16rpx;
}

.template-info {
  display: flex;
  align-items: center;
  gap: 16rpx;
  flex: 1;
  min-width: 0;
}

.file-icon {
  font-size: 48rpx;
  width: 72rpx;
  height: 72rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12rpx;
  flex-shrink: 0;
}

.info-text {
  flex: 1;
  min-width: 0;
}

.template-name {
  font-size: 30rpx;
  font-weight: 500;
  color: #333;
  display: block;
  margin-bottom: 8rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.generate-time {
  font-size: 24rpx;
  color: #999;
}

.status-badge {
  padding: 6rpx 16rpx;
  border-radius: 6rpx;
  font-size: 22rpx;
  flex-shrink: 0;
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

.status-badge.pending {
  background: #f6ffed;
  color: #52c41a;
}

.item-preview {
  background: #f8f9fa;
  border-radius: 8rpx;
  padding: 16rpx;
  margin-bottom: 16rpx;
}

.preview-text {
  font-size: 26rpx;
  color: #666;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.item-actions {
  display: flex;
  gap: 16rpx;
}

.action-btn {
  flex: 1;
  padding: 16rpx 0;
  border-radius: 8rpx;
  text-align: center;
  font-size: 26rpx;
}

.action-btn.view {
  background: #e6f7ff;
  color: #007bff;
}

.action-btn.download {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
}

.loading-more,
.no-more {
  text-align: center;
  padding: 30rpx;
  color: #999;
  font-size: 26rpx;
}
</style>
