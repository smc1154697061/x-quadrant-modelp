<template>
  <app-layout title="实用工具">
    <view class="tools-container">
      <!-- 工具卡片列表 -->
      <view class="tools-grid" :class="{ 'tools-grid-pc': isPc }">
        <!-- 内容提取工具 -->
        <view class="tool-card" @tap="navigateToTool('extraction')">
          <view class="tool-icon">📄</view>
          <view class="tool-info">
            <text class="tool-name">内容提取</text>
            <text class="tool-desc">智能提取文件内容，生成结构化数据</text>
          </view>
          <view class="tool-arrow">›</view>
        </view>
        
        <!-- 占位卡片 - 未来功能 -->
        <view class="tool-card disabled">
          <view class="tool-icon">🔄</view>
          <view class="tool-info">
            <text class="tool-name">JSON转换</text>
            <text class="tool-desc">敬请期待</text>
          </view>
        </view>
        
        <view class="tool-card disabled">
          <view class="tool-icon">📅</view>
          <view class="tool-info">
            <text class="tool-name">日期转换</text>
            <text class="tool-desc">敬请期待</text>
          </view>
        </view>
        
        <view class="tool-card disabled">
          <view class="tool-icon">🔢</view>
          <view class="tool-info">
            <text class="tool-name">进制转换</text>
            <text class="tool-desc">敬请期待</text>
          </view>
        </view>
      </view>
    </view>
  </app-layout>
</template>

<script>
import AppLayout from '../../components/layout/AppLayout.vue';

export default {
  components: {
    AppLayout
  },
  data() {
    return {
      isPc: false
    };
  },
  onLoad() {
    this.checkDeviceType();
  },
  methods: {
    checkDeviceType() {
      uni.getSystemInfo({
        success: (res) => {
          this.isPc = res.windowWidth >= 768;
        }
      });
    },
    
    navigateToTool(toolName) {
      uni.navigateTo({
        url: `/pages/tools/${toolName}/index`
      });
    }
  }
}
</script>

<style scoped>
.tools-container {
  min-height: 100vh;
  background-color: #f5f7fa;
  padding: 20rpx;
}

.tools-grid {
  display: grid;
  grid-template-columns: repeat(1, 1fr);
  gap: 20rpx;
  max-width: 1200rpx;
  margin: 0 auto;
}

.tools-grid-pc {
  grid-template-columns: repeat(2, 1fr);
}

.tool-card {
  background: #fff;
  border-radius: 16rpx;
  padding: 30rpx;
  display: flex;
  align-items: center;
  gap: 20rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
}

.tool-card:active {
  transform: scale(0.98);
  box-shadow: 0 1rpx 8rpx rgba(0, 0, 0, 0.12);
}

.tool-card.disabled {
  opacity: 0.5;
  pointer-events: none;
}

.tool-icon {
  font-size: 60rpx;
  width: 80rpx;
  height: 80rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16rpx;
  flex-shrink: 0;
}

.tool-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.tool-name {
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
}

.tool-desc {
  font-size: 24rpx;
  color: #999;
  line-height: 1.4;
}

.tool-arrow {
  font-size: 48rpx;
  color: #ddd;
  font-weight: 300;
}

/* PC端优化 */
@media screen and (min-width: 768px) {
  .tools-container {
    padding: 40rpx;
  }
  
  .tool-card:hover {
    transform: translateY(-4rpx);
    box-shadow: 0 8rpx 24rpx rgba(0, 0, 0, 0.12);
  }
  
  .tool-card:hover .tool-arrow {
    color: var(--primary-color);
  }
}
</style>

