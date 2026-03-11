<template>
  <view class="container">
    <view class="header">
      <view class="back-btn" @click="goBack">
        <text class="iconfont icon-back"></text>
      </view>
      <view class="title">机器人详情</view>
      <view class="action-btn" v-if="isOwner" @click="showMenu">
        <text class="iconfont icon-more"></text>
      </view>
    </view>
    
    <view class="bot-card" v-if="botInfo.id">
      <view class="bot-header">
        <view class="bot-avatar">
          <text class="iconfont icon-robot"></text>
        </view>
        <view class="bot-info">
          <view class="bot-name">{{ botInfo.name }}</view>
          <view class="bot-meta">
            <text class="bot-model">{{ botInfo.model_name || '默认模型' }}</text>
            <text class="bot-status" :class="{ 'public': botInfo.is_public }">
              {{ botInfo.is_public ? '公开' : '私有' }}
            </text>
          </view>
        </view>
      </view>
      
      <view class="bot-description">
        <text>{{ botInfo.description || '暂无描述' }}</text>
      </view>
      
      <view class="bot-section">
        <view class="section-title">系统提示词</view>
        <view class="section-content">
          {{ botInfo.system_prompt || '暂无系统提示词' }}
        </view>
      </view>
      
      <view class="bot-section" v-if="botInfo.kb_ids && botInfo.kb_ids.length > 0">
        <view class="section-title">关联知识库</view>
        <view class="kb-list">
          <view class="kb-item" v-for="kb in knowledgeBases" :key="kb.id">
            <text class="iconfont icon-database"></text>
            <text class="kb-name">{{ kb.name }}</text>
          </view>
        </view>
      </view>
      
      <view class="bot-actions">
        <button class="action-btn primary" @click="createConversation">开始对话</button>
        <button class="action-btn" v-if="isOwner" @click="editBot">编辑机器人</button>
      </view>
    </view>
    
    <view class="loading-container" v-else>
      <uni-load-more status="loading"></uni-load-more>
    </view>
  </view>
</template>

<script>
import api from '@/utils/api.js';

export default {
  data() {
    return {
      botId: null,
      botInfo: {},
      isOwner: false,
      knowledgeBases: [],
      conversationId: null
    }
  },
  onLoad(options) {
    this.botId = options.botId;
    this.loadBotInfo();
  },
  methods: {
    // 加载机器人信息
    async loadBotInfo() {
      try {
        const response = await api.get(`/llm/bots/${this.botId}`);
        if (response.code === 'SUCCESS') {
          this.botInfo = response.data || {};
          
          // 检查是否为创建者
          const userInfo = getApp().globalData.userInfo || {};
          this.isOwner = userInfo.id === this.botInfo.created_by;
          
          // 加载知识库信息
          if (this.botInfo.kb_ids && this.botInfo.kb_ids.length > 0) {
            this.loadKnowledgeBases();
          }
        } else {
          uni.showToast({
            title: '获取机器人信息失败',
            icon: 'none'
          });
        }
      } catch (error) {
        console.error('加载机器人信息出错:', error);
        uni.showToast({
          title: '加载机器人信息失败',
          icon: 'none'
        });
      }
    },
    
    // 加载知识库信息
    async loadKnowledgeBases() {
      try {
        // 这里假设有一个获取知识库列表的API
        const response = await api.get('/llm/knowledge-bases');
        if (response.code === 'SUCCESS') {
          const allKbs = response.data.knowledge_bases || [];
          
          // 筛选出关联的知识库
          this.knowledgeBases = allKbs.filter(kb => 
            this.botInfo.kb_ids.includes(kb.id)
          );
        }
      } catch (error) {
        console.error('加载知识库信息失败:', error);
      }
    },
    
    // 开始对话 - 修改为直接跳转到聊天页面，不创建对话
    createConversation() {
      // 检查botId是否有效
      if (!this.botId) {
        uni.showToast({
          title: '机器人信息无效',
          icon: 'none'
        });
        return;
      }
      
      // 显示加载提示
      uni.showLoading({
        title: '准备中...',
        mask: true  // 显示遮罩层防止用户重复点击
      });
      
      // 设置超时
      const navigationTimeout = setTimeout(() => {
        uni.hideLoading();
        uni.showModal({
          title: '导航超时',
          content: '页面加载时间过长，是否重试？',
          confirmText: '重试',
          cancelText: '取消',
          success: (res) => {
            if (res.confirm) {
              this.createConversation(); // 重试
            }
          }
        });
      }, 5000); // 5秒超时
      
      // 直接跳转到聊天页面，只带上botId参数
      uni.navigateTo({
        url: `/pages/chat-modules/chat/index?botId=${this.botId}`,
        success: () => {
          clearTimeout(navigationTimeout); // 清除超时
          uni.hideLoading();
        },
        fail: (error) => {
          clearTimeout(navigationTimeout); // 清除超时
          console.error('跳转失败:', error);
          uni.hideLoading();
          
          // 显示更友好的错误信息，并提供重试选项
          uni.showModal({
            title: '无法打开聊天',
            content: '跳转到聊天页面失败，是否重试？',
            confirmText: '重试',
            cancelText: '取消',
            success: (res) => {
              if (res.confirm) {
                // 用户点击重试
                setTimeout(() => {
                  this.createConversation();
                }, 500); // 延迟半秒再重试
              }
            }
          });
        }
      });
    },
    
    // 编辑机器人
    editBot() {
      uni.navigateTo({
        url: `/pages/bot-modules/edit-bot/index?botId=${this.botId}`
      });
    },
    
    // 显示菜单
    showMenu() {
      uni.showActionSheet({
        itemList: ['编辑机器人', '删除机器人'],
        success: (res) => {
          if (res.tapIndex === 0) {
            this.editBot();
          } else if (res.tapIndex === 1) {
            this.confirmDelete();
          }
        }
      });
    },
    
    // 确认删除
    confirmDelete() {
      uni.showModal({
        title: '确认删除',
        content: '确定要删除此机器人吗？删除后无法恢复。',
        success: async (res) => {
          if (res.confirm) {
            await this.deleteBot();
          }
        }
      });
    },
    
    // 删除机器人
    async deleteBot() {
      try {
        const response = await api.delete(`/llm/bots/${this.botId}`);
        
        if (response.code === 'SUCCESS') {
          uni.showToast({
            title: '删除成功',
            icon: 'success'
          });
          
          // 返回上一页
          setTimeout(() => {
            uni.navigateBack();
          }, 1500);
        } else {
          uni.showToast({
            title: response.message || '删除失败',
            icon: 'none'
          });
        }
      } catch (error) {
        console.error('删除机器人失败:', error);
        uni.showToast({
          title: '删除失败',
          icon: 'none'
        });
      }
    },
    
    // 返回上一页
    goBack() {
      uni.navigateBack();
    }
  }
}
</script>

<style lang="scss">
.container {
  padding: 20rpx;
  min-height: 100vh;
  background-color: #f5f5f5;
}

.header {
  display: flex;
  align-items: center;
  padding: 20rpx 0;
  margin-bottom: 30rpx;
  
  .back-btn, .action-btn {
    width: 80rpx;
    height: 80rpx;
    display: flex;
    justify-content: center;
    align-items: center;
    
    .iconfont {
      font-size: 40rpx;
      color: #333;
    }
  }
  
  .title {
    flex: 1;
    font-size: 36rpx;
    font-weight: bold;
    color: #333;
    text-align: center;
  }
}

.bot-card {
  background-color: #fff;
  border-radius: 12rpx;
  padding: 30rpx;
  box-shadow: 0 2rpx 10rpx rgba(0, 0, 0, 0.05);
  
  .bot-header {
    display: flex;
    align-items: center;
    margin-bottom: 30rpx;
    
    .bot-avatar {
      width: 120rpx;
      height: 120rpx;
      background-color: #ecf5ff;
      border-radius: 60rpx;
      display: flex;
      justify-content: center;
      align-items: center;
      margin-right: 20rpx;
      
      .iconfont {
        font-size: 60rpx;
        color: #007AFF;
      }
    }
    
    .bot-info {
      flex: 1;
      
      .bot-name {
        font-size: 36rpx;
        font-weight: bold;
        color: #333;
        margin-bottom: 10rpx;
      }
      
      .bot-meta {
        display: flex;
        align-items: center;
        
        .bot-model, .bot-status {
          font-size: 24rpx;
          padding: 6rpx 12rpx;
          border-radius: 6rpx;
          margin-right: 10rpx;
        }
        
        .bot-model {
          background-color: #f0f0f0;
          color: #666;
        }
        
        .bot-status {
          background-color: #f9f0ff;
          color: #722ed1;
          
          &.public {
            background-color: #e6f7ff;
            color: #1890ff;
          }
        }
      }
    }
  }
  
  .bot-description {
    padding: 20rpx 0;
    border-top: 1rpx solid #f0f0f0;
    border-bottom: 1rpx solid #f0f0f0;
    margin-bottom: 30rpx;
    
    text {
      font-size: 28rpx;
      color: #666;
      line-height: 1.6;
    }
  }
  
  .bot-section {
    margin-bottom: 30rpx;
    
    .section-title {
      font-size: 30rpx;
      font-weight: bold;
      color: #333;
      margin-bottom: 15rpx;
    }
    
    .section-content {
      font-size: 28rpx;
      color: #666;
      line-height: 1.6;
      background-color: #f9f9f9;
      padding: 20rpx;
      border-radius: 8rpx;
    }
    
    .kb-list {
      display: flex;
      flex-wrap: wrap;
      
      .kb-item {
        display: flex;
        align-items: center;
        background-color: #f5f5f5;
        padding: 10rpx 20rpx;
        border-radius: 8rpx;
        margin-right: 15rpx;
        margin-bottom: 15rpx;
        
        .iconfont {
          font-size: 28rpx;
          color: #1890ff;
          margin-right: 10rpx;
        }
        
        .kb-name {
          font-size: 26rpx;
          color: #666;
        }
      }
    }
  }
  
  .bot-actions {
    display: flex;
    justify-content: center;
    margin-top: 40rpx;
    
    .action-btn {
      width: 280rpx;
      height: 80rpx;
      line-height: 80rpx;
      text-align: center;
      border-radius: 40rpx;
      font-size: 28rpx;
      margin: 0 15rpx;
      
      &.primary {
        background-color: #007AFF;
        color: #fff;
      }
      
      &:not(.primary) {
        background-color: #f5f5f5;
        color: #666;
      }
    }
  }
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 400rpx;
}
</style>