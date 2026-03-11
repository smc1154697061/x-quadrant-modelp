<template>
  <app-layout title="智能对话">
    <view class="chat-container">
      <!-- 登录用户显示左侧对话列表 -->
      <view class="sidebar" v-if="isPc && isLoggedIn">
        <view class="sidebar-header">
          <text class="sidebar-title">我的对话</text>
          <button class="new-chat-btn" @tap="showBotSelector">新建对话</button>
        </view>
        
        <scroll-view scroll-y="true" class="conversation-list">
          <view v-if="loadingConversations" class="loading-state">
            <text>加载中...</text>
          </view>
          
          <view v-else-if="conversations.length === 0" class="empty-state">
            <text class="empty-text">暂无对话</text>
            <text class="empty-text">点击"新建对话"开始</text>
          </view>
          
          <view v-else class="conversation-items">
            <view 
              v-for="(conversation, index) in conversations" 
              :key="conversation.id"
              class="conversation-item"
              :class="{'active': selectedConversationId === conversation.id}"
              @tap="selectConversation(conversation.id)"
            >
              <view class="conversation-info">
                <text class="conversation-name">{{ getConversationTitle(conversation) }}</text>
                <text class="conversation-time">{{ formatTime(conversation.created_at) }}</text>
              </view>
              <button class="delete-btn" @tap.stop="confirmDelete(conversation.id)">删除</button>
            </view>
          </view>
        </scroll-view>
      </view>
      
      <!-- 主要内容区域 -->
      <view class="main-content" :class="{'full-width': !isPc}">
        <!-- 聊天界面 -->
        <view v-if="selectedConversationId" class="chat-interface">
          <!-- 使用选择的对话ID -->
          <web-view :src="`/pages/chat-modules/chat/index?id=${selectedConversationId}`"></web-view>
        </view>
        
        <!-- 欢迎界面 -->
        <view v-else class="welcome-screen">
          <view class="welcome-content">
            <text class="welcome-title">欢迎使用智能对话</text>
            <text class="welcome-subtitle">请选择或创建一个对话开始</text>
            <button class="welcome-btn" @tap="showBotSelector">创建新对话</button>
          </view>
        </view>
      </view>
    </view>
    
    <!-- 机器人选择器，对所有用户显示 -->
    <view v-if="showBotSelectorDialog" class="bot-selector">
      <view class="selector-header">
        <text class="selector-title">选择对话机器人</text>
        <button class="close-selector" @tap="closeBotSelector">关闭</button>
      </view>
      
      <scroll-view scroll-y="true" class="bot-list">
        <view v-if="loadingBots" class="loading-state">
          <text>加载中...</text>
        </view>
        
        <view v-else>
          <!-- 创建机器人按钮 -->
          <view class="create-bot-section">
            <button class="create-bot-btn" @tap="showCreateBotForm">创建新机器人</button>
          </view>
          
          <view v-if="bots.length === 0" class="empty-state">
            <text class="empty-text">暂无可用机器人</text>
            <text class="empty-text">点击上方按钮创建机器人</text>
          </view>
          
          <view v-else class="bot-items">
            <view 
              v-for="(bot, index) in bots" 
              :key="bot.id"
              class="bot-item"
              @tap="createConversation(bot.id)"
            >
              <view class="bot-info">
                <text class="bot-name">{{ bot.name }}</text>
                <text class="bot-desc">{{ bot.description || '无描述' }}</text>
                <view v-if="bot.kb_names && bot.kb_names.length > 0" class="bot-kb">
                  <text class="kb-label">关联知识库:</text>
                  <text class="kb-names">{{ bot.kb_names.join(', ') }}</text>
                </view>
              </view>
              <view class="bot-actions">
                <button class="start-chat-btn">开始对话</button>
                <button class="edit-bot-btn" @tap.stop="editBot(bot)">编辑</button>
              </view>
            </view>
          </view>
        </view>
      </scroll-view>
    </view>
    
    <!-- 登录弹窗 -->
    <login-dialog v-model:visible="loginVisible" @login-success="onLoginSuccess"></login-dialog>
  </app-layout>
</template>

<script>
import api from '../../../utils/api.js';
import AppLayout from '../../../components/layout/AppLayout.vue';

export default {
  components: {
    AppLayout
  },
  data() {
    return {
      isPc: false,
      loadingBots: false,
      loadingConversations: false,
      bots: [],
      conversations: [],
      selectedConversationId: null,
      showingBotSelector: false,
      showingConversationList: false,
      isLoggedIn: false,
      showBotDialog: false,
      showBotSelectorDialog: false,
      isEditing: false,
      selectedBotId: null,
      botForm: {
        name: '',
        description: '',
        system_prompt: '',
        model_name: 'gpt-3.5-turbo',
        kb_ids: [],
        kb_names: [],
        is_public: false
      },
      modelOptions: ['gpt-3.5-turbo', 'gpt-4', 'claude-3-sonnet', 'gemini-pro'],
      selectedModelIndex: 0,
      loadingKnowledgeBases: false,
      knowledgeBases: [],
      botId: null,
      loginVisible: false,
      lastUserQuestions: {}
    }
  },
  onLoad(options) {
    this.botId = options.botId; // 接收机器人ID参数
    
    // 清除本地缓存
    this.clearConversationCache();
    
    // 获取对话列表
    this.fetchConversations();
    
    // 检测设备类型
    this.checkDeviceType();
    
    // 检查登录状态
    this.checkLoginStatus();
    
    // 加载机器人和对话列表
    this.fetchBots();
    
    // 监听设备类型变化
    uni.$on('deviceTypeChange', this.handleDeviceTypeChange);
    
    // 监听登录状态变化
    uni.$on('loginStatusChange', this.checkLoginStatus);
  },
  onShow() {
    // 每次显示页面时刷新列表
    this.clearConversationCache();
    this.fetchBots();
    this.fetchConversations();
  },
  onPullDownRefresh() {
    // 下拉刷新
    this.fetchBots();
    this.fetchConversations();
    setTimeout(() => {
      uni.stopPullDownRefresh();
    }, 1000);
  },
  onUnload() {
    // 移除事件监听
    uni.$off('deviceTypeChange', this.handleDeviceTypeChange);
    uni.$off('loginStatusChange', this.checkLoginStatus);
  },
  methods: {
    // 清除对话列表缓存
    clearConversationCache() {
      // 清空对话列表
      this.conversations = [];
      // 清空缓存的对话标题
      this.lastUserQuestions = {};
      // 清空选中的对话ID
      this.selectedConversationId = null;
    },
    // 检查登录状态
    checkLoginStatus() {
      try {
        const token = uni.getStorageSync('token');
        const userInfo = uni.getStorageSync('userInfo');
        this.isLoggedIn = !!token && !!userInfo;
      } catch (e) {
        this.isLoggedIn = false;
      }
    },
    
    // 获取机器人列表
    async fetchBots() {
      this.loadingBots = true;
      
      try {
        const response = await api.get('/llm/bots');
        
        if (response && (response.code === 'SUCCESS' || response.code === '0000')) {
          this.bots = response.data.bots || [];
        } else {
          console.error('获取机器人列表失败:', response?.message || '未知错误');
          uni.showToast({
            title: '获取机器人列表失败',
            icon: 'none'
          });
        }
      } catch (error) {
        console.error('获取机器人列表失败:', error);
        uni.showToast({
          title: '获取机器人列表失败',
          icon: 'none'
        });
      } finally {
        this.loadingBots = false;
      }
    },
    
    // 获取知识库列表
    async fetchKnowledgeBases() {
      this.loadingKnowledgeBases = true;
      
      try {
        const response = await api.get('/llm/knowledge-bases');
        
        if (response && (response.code === 'SUCCESS' || response.code === '0000')) {
          this.knowledgeBases = response.data || [];
        } else {
          console.error('获取知识库列表失败:', response?.message || '未知错误');
          uni.showToast({
            title: '获取知识库列表失败',
            icon: 'none'
          });
        }
      } catch (error) {
        console.error('获取知识库列表失败:', error);
        uni.showToast({
          title: '获取知识库列表失败',
          icon: 'none'
        });
      } finally {
        this.loadingKnowledgeBases = false;
      }
    },
    
    // 获取对话列表
    async fetchConversations() {
      this.loadingConversations = true;
      
      try {
        let url = '/llm/conversations';
        
        // 如果有机器人ID，则按机器人过滤对话
        if (this.botId) {
          url += `?bot_id=${this.botId}`;
        }
        
        const response = await api.get(url);
        
        // 确保conversations始终是一个数组
        this.conversations = [];
        
        if (response && (response.code === 'SUCCESS' || response.code === '0000')) {
          if (response.data && response.data.conversations && response.data.conversations.length > 0) {
            this.conversations = response.data.conversations;
            
            // 获取每个对话的最后一条用户消息作为标题
            for (const conversation of this.conversations) {
              this.getLastUserMessage(conversation.id);
            }
          }
        } else {
          console.error('获取对话列表失败:', response?.message || '未知错误');
        }
      } catch (error) {
        console.error('获取对话列表异常:', error);
        this.conversations = [];
      } finally {
        this.loadingConversations = false;
      }
    },
    
    // 获取对话的最后一条用户消息
    async getLastUserMessage(conversationId) {
      try {
        const response = await api.get(`/llm/conversations/${conversationId}`);
        
        if (response && response.code === 'SUCCESS' && response.data.messages) {
          const userMessages = response.data.messages.filter(msg => msg.role === 'user');
          if (userMessages.length > 0) {
            // 获取最后一条用户消息
            const lastQuestion = userMessages[userMessages.length - 1].content;
            // 保存到缓存
            this.lastUserQuestions[conversationId] = lastQuestion;
            // 确保响应式更新
            this.$forceUpdate();
          }
        }
      } catch (error) {
        console.error(`获取对话${conversationId}最后一条消息失败:`, error);
      }
    },
    
    // 获取对话标题
    getConversationTitle(conversation) {
      // 首先尝试从缓存获取最后一个用户问题
      const lastQuestion = this.lastUserQuestions[conversation.id];
      if (lastQuestion) {
        // 截取前20个字符作为标题
        return lastQuestion.length > 20 ? lastQuestion.substring(0, 20) + '...' : lastQuestion;
      }
      
      // 如果有机器人名称，使用机器人名称
      if (conversation.bot_name) {
        return `与${conversation.bot_name}的对话`;
      }
      
      // 默认显示未命名
      return '未命名对话';
    },
    
    // 创建新对话
    async createConversation(botId) {
      try {
        let conversationId;
        
        if (this.isLoggedIn) {
          // 已登录用户创建持久化对话
          const response = await api.post('/llm/conversations', { bot_id: botId });
          
          if (response && (response.code === 'SUCCESS' || response.code === '0000')) {
            conversationId = response.data.id;
            
            // 刷新对话列表
            this.fetchConversations();
          } else {
            uni.showToast({
              title: response?.message || '创建对话失败',
              icon: 'none'
            });
            return;
          }
        } else {
          // 游客模式，使用临时会话ID
          const response = await api.post('/llm/conversations', { bot_id: botId });
          
          if (response && (response.code === 'SUCCESS' || response.code === '0000')) {
            conversationId = response.data.session_id;
          } else {
            uni.showToast({
              title: response?.message || '创建对话失败',
              icon: 'none'
            });
            return;
          }
        }
        
        // 关闭机器人选择器
        this.closeBotSelector();
        
        // 选择新创建的对话
        if (this.isPc) {
          this.selectedConversationId = conversationId;
        } else {
          // 在移动端直接导航到聊天页面
          uni.navigateTo({
            url: `/pages/chat-modules/chat/index?id=${conversationId}`
          });
        }
      } catch (error) {
        console.error('创建对话失败:', error);
        uni.showToast({
          title: '创建对话失败',
          icon: 'none'
        });
      }
    },
    
    // 选择对话
    selectConversation(conversationId) {
      this.selectedConversationId = conversationId;
      
      // 在移动端选择对话后关闭列表
      if (!this.isPc) {
        this.hideConversationList();
        
        // 导航到聊天页面
        uni.navigateTo({
          url: `/pages/chat-modules/chat/index?id=${conversationId}`
        });
      }
    },
    
    // 确认删除对话
    confirmDelete(conversationId) {
      // 直接删除，不显示确认弹窗
      this.deleteConversation(conversationId);
    },
    
    // 删除对话
    async deleteConversation(conversationId) {
      try {
        uni.showLoading({
          title: '删除中...'
        });
        
        const response = await api.delete(`/llm/conversations/${conversationId}`);
        
        uni.hideLoading();
        
        if (response && (response.code === 'SUCCESS' || response.code === '0000')) {
          uni.showToast({
            title: '删除成功',
            icon: 'success'
          });
          
          // 刷新列表
          this.fetchConversations();
          
          // 如果删除的是当前选中的对话，清除选择并关闭webview
          if (this.selectedConversationId === conversationId) {
            this.selectedConversationId = null;
            
            // 如果在移动端，可能需要返回上一页
            if (!this.isPc) {
              setTimeout(() => {
                uni.navigateBack();
              }, 500);
            }
          }
        } else {
          uni.showToast({
            title: response?.message || '删除失败',
            icon: 'none'
          });
        }
      } catch (error) {
        uni.hideLoading();
        console.error('删除对话失败:', error);
        uni.showToast({
          title: '删除失败',
          icon: 'none'
        });
      }
    },
    
    // 显示机器人选择器
    showBotSelector() {
      this.showBotSelectorDialog = true;
    },
    
    // 关闭机器人选择器
    closeBotSelector() {
      this.showBotSelectorDialog = false;
    },
    
    // 显示对话列表（移动端）
    showConversationList() {
      this.showingConversationList = true;
    },
    
    // 隐藏对话列表（移动端）
    hideConversationList() {
      this.showingConversationList = false;
    },
    
    // 格式化时间显示
    formatTime(timestamp) {
      const date = new Date(timestamp);
      const now = new Date();
      const diff = now - date;
      
      // 一小时内
      if (diff < 3600000) {
        const minutes = Math.floor(diff / 60000);
        return `${minutes}分钟前`;
      }
      
      // 一天内
      if (diff < 86400000) {
        const hours = Math.floor(diff / 3600000);
        return `${hours}小时前`;
      }
      
      // 更早
      return `${date.getMonth() + 1}月${date.getDate()}日`;
    },
    
    // 检测设备类型
    checkDeviceType() {
      uni.getSystemInfo({
        success: (res) => {
          this.isPc = res.windowWidth >= 768;
        }
      });
    },
    
    // 处理设备类型变化
    handleDeviceTypeChange(data) {
      if (data) {
        this.isPc = data.isPc;
      }
    },
    
    // 显示创建机器人表单
    showCreateBotForm() {
      this.isEditing = false;
      this.botForm = {
        name: '',
        description: '',
        system_prompt: '',
        model_name: this.modelOptions[0],
        kb_ids: [],
        kb_names: [],
        is_public: false
      };
      this.selectedModelIndex = 0;
      
      // 获取知识库列表
      this.fetchKnowledgeBases();
      
      this.showBotDialog = true;
    },
    
    // 编辑机器人
    editBot(bot) {
      // 阻止事件冒泡，避免同时触发创建对话
      event.stopPropagation();
      
      this.isEditing = true;
      this.selectedBotId = bot.id;
      
      // 设置表单数据
      this.botForm = {
        name: bot.name,
        description: bot.description || '',
        system_prompt: bot.system_prompt || '',
        model_name: bot.model_name || this.modelOptions[0],
        kb_ids: bot.kb_ids || [],
        kb_names: bot.kb_names || [],
        is_public: bot.is_public || false
      };
      
      // 设置选中的模型
      const modelIndex = this.modelOptions.findIndex(m => m === bot.model_name);
      this.selectedModelIndex = modelIndex !== -1 ? modelIndex : 0;
      
      // 获取知识库列表
      this.fetchKnowledgeBases();
      
      this.showBotDialog = true;
    },
    
    // 取消创建机器人
    cancelBotDialog() {
      this.showBotDialog = false;
    },
    
    // 保存机器人
    async saveBotDialog() {
      if (!this.botForm.name.trim()) {
        uni.showToast({
          title: '请输入机器人名称',
          icon: 'none'
        });
        return;
      }
      
      try {
        const botData = {
          name: this.botForm.name,
          description: this.botForm.description,
          system_prompt: this.botForm.system_prompt,
          model_name: this.botForm.model_name,
          is_public: this.botForm.is_public,
          kb_ids: this.botForm.kb_ids
        };
        
        let response;
        
        if (this.isEditing) {
          // 更新机器人
          response = await api.put(`/llm/bots/${this.selectedBotId}`, botData);
        } else {
          // 创建新机器人
          response = await api.post('/llm/bots', botData);
        }
        
        if (response && (response.code === 'SUCCESS' || response.code === '0000')) {
          uni.showToast({
            title: this.isEditing ? '更新成功' : '创建成功',
            icon: 'success'
          });
          
          this.showBotDialog = false;
          this.fetchBots();  // 刷新列表
        } else {
          uni.showToast({
            title: response?.message || '操作失败',
            icon: 'none'
          });
        }
      } catch (error) {
        console.error('保存机器人失败:', error);
        uni.showToast({
          title: '操作失败',
          icon: 'none'
        });
      }
    },
    
    // 切换知识库
    toggleKnowledgeBase(kbId, kbName) {
      const index = this.botForm.kb_ids.indexOf(kbId);
      
      if (index === -1) {
        // 添加知识库
        this.botForm.kb_ids.push(kbId);
        this.botForm.kb_names.push(kbName);
      } else {
        // 移除知识库
        this.botForm.kb_ids.splice(index, 1);
        this.botForm.kb_names.splice(index, 1);
      }
    },
    
    // 选择模型
    onModelChange(e) {
      this.selectedModelIndex = e.detail.value;
      this.botForm.model_name = this.modelOptions[this.selectedModelIndex];
    },
    
    // 显示登录弹窗
    showLoginDialog() {
      this.loginVisible = true;
    },
    
    // 登录成功后的处理
    onLoginSuccess() {
      this.checkLoginStatus();
      this.fetchConversations();
    }
  }
}
</script>

<style>
.chat-container {
  height: 100%;
  display: flex;
  width: 100%;
  box-sizing: border-box;
  background-color: #f5f7fa;
}

/* 左侧边栏样式 */
.sidebar {
  width: 300rpx;
  height: 100%;
  background-color: #fff;
  border-right: 1px solid #e0e0e0;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 20rpx;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  flex-direction: column;
}

.sidebar-title {
  font-size: 28rpx;
  font-weight: bold;
  color: #333;
  margin-bottom: 15rpx;
}

.new-chat-btn {
  background-color: var(--primary-color);
  color: white;
  font-size: 24rpx;
  border-radius: 30rpx;
  height: 60rpx;
  line-height: 60rpx;
  border: none;
}

.conversation-list {
  flex: 1;
  overflow-y: auto;
}

.conversation-items {
  padding: 10rpx 0;
}

.conversation-item {
  padding: 20rpx;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
}

.conversation-item.active {
  background-color: #e6f7ff;
  border-right: 3px solid var(--primary-color);
}

.conversation-info {
  flex: 1;
  overflow: hidden;
}

.conversation-name {
  font-size: 24rpx;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 5rpx;
}

.conversation-time {
  font-size: 20rpx;
  color: #999;
}

.delete-btn {
  font-size: 20rpx;
  color: #ff4d4f;
  background: none;
  border: none;
  padding: 0;
  margin: 0;
  line-height: normal;
}

/* 主内容区域样式 */
.main-content {
  flex: 1;
  height: 100%;
  display: flex;
  flex-direction: column;
  position: relative;
}

/* 移动端顶部操作栏 */
.mobile-header {
  display: flex;
  justify-content: space-between;
  padding: 20rpx;
  background-color: #fff;
  border-bottom: 1px solid #e0e0e0;
}

.mobile-new-chat, .mobile-show-chats {
  font-size: 24rpx;
  background-color: var(--primary-color);
  color: white;
  border-radius: 30rpx;
  height: 60rpx;
  line-height: 60rpx;
  padding: 0 30rpx;
  border: none;
}

/* 机器人选择器样式 */
.bot-selector {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #fff;
  z-index: 100;
  display: flex;
  flex-direction: column;
}

.selector-header {
  padding: 20rpx;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.selector-title {
  font-size: 28rpx;
  font-weight: bold;
  color: #333;
}

.close-selector {
  font-size: 24rpx;
  color: #999;
  background: none;
  border: none;
}

.bot-list {
  flex: 1;
  padding: 20rpx;
  overflow-y: auto;
}

.bot-items {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.bot-item {
  background-color: #fff;
  border-radius: 10rpx;
  padding: 20rpx;
  box-shadow: 0 2rpx 10rpx rgba(0, 0, 0, 0.05);
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
}

.bot-info {
  flex: 1;
}

.bot-name {
  font-size: 28rpx;
  font-weight: bold;
  color: #333;
  margin-bottom: 10rpx;
}

.bot-desc {
  font-size: 24rpx;
  color: #666;
  margin-bottom: 10rpx;
}

.bot-kb {
  display: flex;
  font-size: 22rpx;
  color: #999;
}

.kb-label {
  margin-right: 10rpx;
}

.bot-actions {
  display: flex;
  flex-direction: column;
  gap: 10rpx;
  min-width: 120rpx;
}

.start-chat-btn {
  font-size: 24rpx;
  background-color: var(--primary-color);
  color: white;
  border-radius: 30rpx;
  height: 60rpx;
  line-height: 60rpx;
  padding: 0 20rpx;
  border: none;
  text-align: center;
}

.edit-bot-btn {
  font-size: 24rpx;
  background-color: #f0f0f0;
  color: #333;
  border-radius: 30rpx;
  height: 60rpx;
  line-height: 60rpx;
  padding: 0 20rpx;
  border: none;
  text-align: center;
}

/* 移动端对话列表弹窗 */
.mobile-conversation-list {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #fff;
  z-index: 100;
  display: flex;
  flex-direction: column;
}

.mobile-list-header {
  padding: 20rpx;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.mobile-list-title {
  font-size: 28rpx;
  font-weight: bold;
  color: #333;
}

.close-list {
  font-size: 24rpx;
  color: #999;
  background: none;
  border: none;
}

.mobile-conversations {
  flex: 1;
  padding: 20rpx;
  overflow-y: auto;
}

.mobile-conversation-items {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.mobile-conversation-item {
  background-color: #fff;
  border-radius: 10rpx;
  padding: 20rpx;
  box-shadow: 0 2rpx 10rpx rgba(0, 0, 0, 0.05);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* 聊天界面样式 */
.chat-interface {
  flex: 1;
  height: 100%;
}

/* 欢迎界面样式 */
.welcome-screen {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #f5f7fa;
}

.welcome-content {
  text-align: center;
  padding: 40rpx;
}

.welcome-title {
  font-size: 40rpx;
  font-weight: bold;
  color: #333;
  margin-bottom: 20rpx;
}

.welcome-subtitle {
  font-size: 28rpx;
  color: #666;
  margin-bottom: 40rpx;
}

.welcome-btn {
  background-color: var(--primary-color);
  color: white;
  font-size: 28rpx;
  border-radius: 40rpx;
  height: 80rpx;
  line-height: 80rpx;
  padding: 0 60rpx;
  border: none;
}

/* 通用样式 */
.loading-state, .empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60rpx 0;
  color: #999;
}

.empty-text {
  font-size: 24rpx;
  color: #999;
  text-align: center;
  margin-bottom: 10rpx;
}

/* 响应式设计 */
@media (max-width: 767px) {
  .sidebar {
    display: none;
  }
}

/* 创建机器人按钮样式 */
.create-bot-section {
  padding: 20rpx;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  justify-content: center;
}

.create-bot-btn {
  background-color: var(--primary-color);
  color: white;
  font-size: 24rpx;
  border-radius: 30rpx;
  height: 60rpx;
  line-height: 60rpx;
  padding: 0 30rpx;
  border: none;
}

/* 创建/编辑机器人弹窗样式 */
.bot-dialog {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #fff;
  z-index: 100;
  display: flex;
  flex-direction: column;
}

.dialog-content {
  flex: 1;
  padding: 20rpx;
}

.dialog-title {
  font-size: 28rpx;
  font-weight: bold;
  color: #333;
  margin-bottom: 20rpx;
}

.form-item {
  margin-bottom: 20rpx;
}

.form-label {
  font-size: 24rpx;
  color: #333;
  margin-bottom: 10rpx;
}

.form-input, .form-textarea, .form-picker {
  width: 100%;
  padding: 10rpx;
  border: 1px solid #e0e0e0;
  border-radius: 5rpx;
}

.form-textarea {
  height: 120rpx;
}

.form-picker {
  height: 80rpx;
}

.picker-view {
  padding: 10rpx;
}

.kb-selector {
  margin-bottom: 20rpx;
}

.kb-options {
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.kb-option {
  display: flex;
  align-items: center;
  cursor: pointer;
}

.kb-checkbox {
  width: 20rpx;
  height: 20rpx;
  border: 1px solid #e0e0e0;
  border-radius: 5rpx;
  margin-right: 10rpx;
}

.checkbox-inner {
  width: 100%;
  height: 100%;
  background-color: var(--primary-color);
  border-radius: 2rpx;
}

.kb-option-content {
  flex: 1;
}

.kb-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 5rpx;
}

.kb-name {
  font-size: 24rpx;
  font-weight: bold;
  color: #333;
}

.kb-count {
  font-size: 20rpx;
  color: #999;
}

.kb-desc {
  font-size: 22rpx;
  color: #666;
}

.selected-kb-info {
  padding: 10rpx;
  background-color: #f5f7fa;
  border-radius: 5rpx;
  margin-top: 10rpx;
}

.selected-kb-text {
  font-size: 24rpx;
  color: #333;
}

.dialog-buttons {
  display: flex;
  justify-content: flex-end;
  padding: 20rpx;
}

.cancel-btn, .confirm-btn {
  font-size: 24rpx;
  padding: 10rpx 20rpx;
  border: none;
  border-radius: 5rpx;
  margin-left: 10rpx;
}

.cancel-btn {
  background-color: #f0f0f0;
  color: #333;
}

.confirm-btn {
  background-color: var(--primary-color);
  color: white;
}

.confirm-btn:disabled {
  background-color: #f0f0f0;
  color: #999;
}

/* 登录弹窗样式 */
.guest-banner {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 40rpx;
  background-color: #fff;
  border-bottom: 1px solid #e0e0e0;
}

.login-btn {
  background-color: var(--primary-color);
  color: white;
  font-size: 24rpx;
  border-radius: 30rpx;
  height: 60rpx;
  line-height: 60rpx;
  padding: 0 30rpx;
  border: none;
}
</style> 