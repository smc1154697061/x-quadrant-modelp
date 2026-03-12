<template>
  <view class="history-panel">
    <!-- 统计卡片 -->
    <view class="stats-row">
      <view class="stat-card">
        <text class="stat-value">{{ stats.total }}</text>
        <text class="stat-label">总生成</text>
      </view>
      <view class="stat-card">
        <text class="stat-value">{{ stats.completed }}</text>
        <text class="stat-label">已完成</text>
      </view>
      <view class="stat-card">
        <text class="stat-value">{{ stats.today }}</text>
        <text class="stat-label">今日</text>
      </view>
    </view>
    
    <!-- 历史记录列表 -->
    <view class="history-list">
      <view v-if="loading" class="loading">
        <text>加载中...</text>
      </view>
      
      <view v-else-if="historyList.length === 0" class="empty">
        <text class="empty-icon">📋</text>
        <text class="empty-text">暂无生成记录</text>
        <text class="empty-hint">生成文档后会显示在这里</text>
      </view>
      
      <view v-else>
        <view 
          v-for="item in historyList" 
          :key="item.id"
          class="history-item"
          @tap="viewDetail(item)"
        >
          <view class="history-icon">
            <text v-if="item.status === 'completed'">✅</text>
            <text v-else-if="item.status === 'generating'">⏳</text>
            <text v-else-if="item.status === 'failed'">❌</text>
            <text v-else>📄</text>
          </view>
          <view class="history-info">
            <text class="history-title">{{ item.template_name || '未知模板' }}</text>
            <view class="history-meta">
              <text class="history-status" :class="item.status">
                {{ getStatusText(item.status) }}
              </text>
              <text class="history-time">{{ formatTime(item.created_at) }}</text>
            </view>
          </view>
          <view class="history-arrow">›</view>
        </view>
        
        <!-- 加载更多 -->
        <view v-if="hasMore" class="load-more" @tap="loadMore">
          <text>{{ loadingMore ? '加载中...' : '加载更多' }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import api from '../../../../utils/api';

export default {
  name: 'TemplateHistoryPanel',
  data() {
    return {
      historyList: [],
      loading: false,
      loadingMore: false,
      page: 1,
      pageSize: 20,
      total: 0,
      stats: {
        total: 0,
        completed: 0,
        today: 0
      }
    };
  },
  computed: {
    hasMore() {
      return this.historyList.length < this.total;
    }
  },
  mounted() {
    this.loadHistory();
  },
  methods: {
    async loadHistory(append = false) {
      if (!append) {
        this.loading = true;
        this.page = 1;
      } else {
        this.loadingMore = true;
      }
      
      try {
        const res = await api.get('/llm/generations', {
          page: this.page,
          page_size: this.pageSize
        });
        
        if (res.code === 'SUCCESS') {
          const data = res.data || {};
          if (append) {
            this.historyList = [...this.historyList, ...(data.list || [])];
          } else {
            this.historyList = data.list || [];
          }
          this.total = data.total || 0;
          this.updateStats();
        }
      } catch (e) {
        console.error('加载历史记录失败:', e);
      } finally {
        this.loading = false;
        this.loadingMore = false;
      }
    },
    
    refresh() {
      this.loadHistory();
    },
    
    loadMore() {
      if (this.loadingMore || !this.hasMore) return;
      this.page++;
      this.loadHistory(true);
    },
    
    updateStats() {
      const today = new Date().toDateString();
      this.stats.total = this.total;
      this.stats.completed = this.historyList.filter(h => h.status === 'completed').length;
      this.stats.today = this.historyList.filter(h => {
        const itemDate = new Date(h.created_at).toDateString();
        return itemDate === today;
      }).length;
    },
    
    getStatusText(status) {
      const statusMap = {
        'pending': '等待中',
        'generating': '生成中',
        'completed': '已完成',
        'failed': '失败'
      };
      return statusMap[status] || status;
    },
    
    formatTime(time) {
      if (!time) return '';
      const date = new Date(time);
      const now = new Date();
      const diff = now - date;
      
      if (diff < 60000) return '刚刚';
      if (diff < 3600000) return Math.floor(diff / 60000) + '分钟前';
      if (diff < 86400000) return Math.floor(diff / 3600000) + '小时前';
      if (diff < 604800000) return Math.floor(diff / 86400000) + '天前';
      
      return `${date.getMonth() + 1}/${date.getDate()}`;
    },
    
    viewDetail(item) {
      if (item.status !== 'completed') {
        uni.showToast({ 
          title: item.status === 'generating' ? '正在生成中' : '生成失败，无法查看', 
          icon: 'none' 
        });
        return;
      }
      this.$emit('viewDetail', item);
    }
  }
};
</script>

<style scoped>
.history-panel {
  min-height: 100%;
}

/* 统计卡片 */
.stats-row {
  display: flex;
  gap: 16rpx;
  padding: 20rpx;
}

.stat-card {
  flex: 1;
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
  text-align: center;
}

.stat-value {
  font-size: 48rpx;
  font-weight: 600;
  color: #007bff;
  display: block;
}

.stat-label {
  font-size: 24rpx;
  color: #999;
  margin-top: 8rpx;
}

/* 历史列表 */
.history-list {
  padding: 0 20rpx 20rpx;
}

.loading, .empty {
  padding: 100rpx 0;
  text-align: center;
  background: #fff;
  border-radius: 16rpx;
}

.empty-icon {
  font-size: 80rpx;
  display: block;
  margin-bottom: 20rpx;
}

.empty-text {
  font-size: 32rpx;
  color: #333;
  display: block;
  margin-bottom: 10rpx;
}

.empty-hint {
  font-size: 26rpx;
  color: #999;
}

.history-item {
  display: flex;
  align-items: center;
  background: #fff;
  padding: 24rpx;
  border-radius: 16rpx;
  margin-bottom: 16rpx;
}

.history-icon {
  font-size: 40rpx;
  margin-right: 20rpx;
}

.history-info {
  flex: 1;
  overflow: hidden;
}

.history-title {
  font-size: 30rpx;
  font-weight: 500;
  color: #333;
  display: block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.history-meta {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-top: 8rpx;
}

.history-status {
  font-size: 24rpx;
  padding: 4rpx 12rpx;
  border-radius: 20rpx;
}

.history-status.completed {
  color: #52c41a;
  background: rgba(82, 196, 26, 0.1);
}

.history-status.generating {
  color: #faad14;
  background: rgba(250, 173, 20, 0.1);
}

.history-status.failed {
  color: #ff4d4f;
  background: rgba(255, 77, 79, 0.1);
}

.history-status.pending {
  color: #999;
  background: #f5f7fa;
}

.history-time {
  font-size: 24rpx;
  color: #999;
}

.history-arrow {
  font-size: 36rpx;
  color: #ddd;
  margin-left: 16rpx;
}

/* 加载更多 */
.load-more {
  text-align: center;
  padding: 30rpx;
  color: #007bff;
  font-size: 28rpx;
}
</style>
