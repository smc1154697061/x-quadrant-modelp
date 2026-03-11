<template>
  <!-- PC端使用全屏布局，移动端使用AppLayout -->
  <view v-if="isPc" class="chat-fullscreen">
    <view class="chat-layout">
      <!-- 左侧对话列表 - PC端始终显示，移动端条件显示 -->
      <view class="conversation-sidebar" v-if="isPc || showSidebar" :class="{'sidebar-mobile': !isPc && showSidebar}">
        <view class="sidebar-header">
          <text class="sidebar-title">我的对话</text>
          <button class="new-chat-btn" @click="createNewChat">新建对话</button>
        </view>
      
        <scroll-view scroll-y class="conversation-list">
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
              :class="{'active': conversationId === conversation.id}"
              @click="switchConversation(conversation.id)"
            >
              <view class="conversation-info">
                <text class="conversation-name">{{ getConversationTitle(conversation) }}</text>
                <text class="conversation-time">{{ formatTime(conversation.created_at) }}</text>
              </view>
              <button class="delete-btn" @tap.stop="confirmDeleteConversation(conversation.id)">删除</button>
            </view>
          </view>
        </scroll-view>
      </view>
      
      <!-- 聊天主界面 -->
      <view class="chat-container" :class="{'with-sidebar': isPc || showSidebar}">
        <!-- 返回按钮 - 为防止页面卡住时用户无法返回 -->
        <view class="back-button-wrapper">
          <view class="back-button" @tap="goBack">
            <text class="back-icon">← 返回</text>
          </view>
        </view>
        
        <!-- 消息列表 -->
        <scroll-view 
          class="message-list" 
          scroll-y 
          :scroll-into-view="scrollIntoView"
          @scrolltoupper="loadMoreMessages"
          upper-threshold="50"
        >
          <!-- 加载更多 -->
          <uni-load-more :status="loadMoreStatus" v-if="hasMoreMessages"></uni-load-more>
          
          <!-- 消息内容 -->
          <view 
            class="message-item" 
            v-for="(msg, index) in displayMessages" 
            :key="msg.created_at + '-' + index"
            :id="`msg-${index}`"
          >
            <view class="message-content" :class="{ 'user-message': msg.role === 'user', 'bot-message': msg.role === 'assistant' }">
              <!-- 用户消息 -->
              <template v-if="msg.role === 'user'">
                <view class="message-bubble">
                  <!-- 附件区域 -->
                  <view v-if="msg.attachments && msg.attachments.length" class="message-attachments">
                    <view v-for="file in msg.attachments" :key="file.id || file.filename" class="attachment-item" @tap.stop="previewAttachment(file, msg)">
                      <view class="attachment-icon-wrapper">
                        <text class="attachment-icon">📄</text>
                      </view>
                      <view class="attachment-info">
                        <text class="attachment-name">{{ file.filename || file.name || '附件' }}</text>
                        <text class="attachment-size" v-if="file.file_size">{{ formatFileSize(file.file_size) }}</text>
                      </view>
                      <text v-if="isAttachmentPreviewable(file, msg)" class="attachment-preview-tag">点击预览</text>
                    </view>
                  </view>
                  <!-- 文本内容 -->
                  <rich-text v-if="msg.content && msg.content !== '[已上传文件]'" :nodes="formatMessage(msg.content)"></rich-text>
                </view>
                <view class="avatar user-avatar">
                  <text class="iconfont icon-user"></text>
                </view>
              </template>
              
              <!-- 机器人消息 -->
              <template v-else>
                <view class="avatar bot-avatar">
                  <text class="iconfont icon-robot"></text>
                </view>
                <view class="message-bubble">
                  <!-- 附件区域 -->
                  <view v-if="msg.attachments && msg.attachments.length" class="message-attachments">
                    <view v-for="file in msg.attachments" :key="file.id || file.filename" class="attachment-item" @tap.stop="previewAttachment(file, msg)">
                      <view class="attachment-icon-wrapper">
                        <text class="attachment-icon">📄</text>
                      </view>
                      <view class="attachment-info">
                        <text class="attachment-name">{{ file.filename || file.name || '附件' }}</text>
                        <text class="attachment-size" v-if="file.file_size">{{ formatFileSize(file.file_size) }}</text>
                      </view>
                      <text v-if="isAttachmentPreviewable(file, msg)" class="attachment-preview-tag">点击预览</text>
                    </view>
                  </view>
                  <!-- 文本内容 -->
                  <rich-text v-if="msg.content && msg.content !== '[已上传文件]'" :nodes="formatMessage(msg.content)"></rich-text>
                </view>
              </template>
            </view>
            <view class="message-time">{{ formatTime(msg.created_at) }}</view>
          </view>
          
          <!-- 正在输入提示 -->
          <view class="typing-indicator" v-if="isTyping">
            <view class="avatar bot-avatar">
              <text class="iconfont icon-robot"></text>
            </view>
            <view class="typing-dots">
              <view class="dot"></view>
              <view class="dot"></view>
              <view class="dot"></view>
            </view>
          </view>
          
          <!-- 无消息时的提示 -->
          <view v-if="displayMessages.length === 0" class="welcome-container">
            <view class="welcome-message">
              <text class="welcome-title">欢迎与 {{ botInfo.name || '渡渡鸟助手' }} 对话</text>
              <text class="welcome-desc">{{ botInfo.description || '开始发送消息，与渡渡鸟助手对话' }}</text>
              <view class="welcome-tip">
                <text>{{ conversationId ? '此对话已保存' : '发送第一条消息时将自动创建会话' }}</text>
              </view>
            </view>
          </view>
        </scroll-view>
        
        <view v-if="showPreviewModal" class="preview-modal-overlay" @tap="closePreviewModal">
          <view class="preview-modal" @tap.stop>
            <view class="preview-modal-header">
              <text class="preview-title">{{ previewFile ? previewFile.filename : '文件预览' }}</text>
              <text class="preview-close" @tap="closePreviewModal">×</text>
            </view>
            <view class="preview-modal-content">
              <FilePreview
                v-if="previewFile"
                :file-url="previewFile.url"
                :file-name="previewFile.filename"
                :file-ext="previewFile.ext"
                @rendered="onPreviewRendered"
                @error="onPreviewError"
                @download="onPreviewDownload"
              />
            </view>
          </view>
        </view>

        <!-- 输入框包装器 -->
        <view class="input-wrapper" :class="{'pc-input-wrapper': isPc}">
          <view class="input-container">
            <!-- 附件选择提示 -->
            <view class="attachment-bar" v-if="selectedFile">
              <view class="attachment-chip">
                <text class="attachment-chip-icon">📎</text>
                <text class="attachment-chip-name">{{ selectedFile.name }}</text>
                <text class="attachment-chip-remove" @tap="clearSelectedFile">×</text>
              </view>
            </view>
            <view class="input-row">
              <view class="attach-btn" @tap="chooseAttachment">
                <text class="attach-icon">📎</text>
              </view>
              <textarea 
                class="message-input" 
                v-model="inputMessage" 
                placeholder="请输入问题（可附带一个文件）..." 
                :disabled="isTyping"
                auto-height
                @confirm="sendMessage"
                @input="handleInput"
              ></textarea>
              <view class="send-btn" :class="{ 'active': inputMessage.trim() || selectedFile }" @click="sendMessage">
                <text class="send-text">发送</text>
              </view>
            </view>
          </view>
        </view>
      </view>
    </view>
  </view>
  
  <!-- 移动端使用原有AppLayout -->
  <app-layout v-else :hide-tab-bar="true">
    <view class="chat-layout">
      <!-- 左侧对话列表 - 移动端条件显示 -->
      <view v-if="showSidebar" class="conversation-sidebar sidebar-mobile">
        <view class="sidebar-header">
          <text class="sidebar-title">我的对话</text>
          <button class="new-chat-btn" @click="createNewChat">新建对话</button>
        </view>
      
        <scroll-view scroll-y class="conversation-list">
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
              :class="{'active': conversationId === conversation.id}"
              @click="switchConversation(conversation.id)"
            >
              <view class="conversation-info">
                <text class="conversation-name">{{ getConversationTitle(conversation) }}</text>
                <text class="conversation-time">{{ formatTime(conversation.created_at) }}</text>
              </view>
              <button class="delete-btn" @tap.stop="confirmDeleteConversation(conversation.id)">删除</button>
            </view>
          </view>
        </scroll-view>
        
        <!-- 移动端关闭侧边栏按钮 -->
        <view class="close-sidebar-btn" @click="toggleSidebar">
          <text class="close-icon">×</text>
        </view>
      </view>
      
      <!-- 遮罩层 -->
      <view v-if="showSidebar" class="sidebar-mask" @click="toggleSidebar"></view>
      
      <!-- 聊天主界面 -->
      <view class="chat-container" :class="{'with-sidebar': showSidebar}">
        <!-- 侧边栏切换按钮 -->
        <view v-if="!showSidebar" class="sidebar-toggle">
          <view class="toggle-btn" @click="toggleSidebar">
            <text class="toggle-icon">›</text>
          </view>
        </view>
        
        <!-- 移动端返回按钮 -->
        <view class="mobile-header">
          <view class="back-button" @tap="goBack">
            <text class="back-icon">← 返回</text>
          </view>
          <text class="chat-title">{{ botInfo.name || '渡渡鸟助手' }}</text>
        </view>
        
        <!-- 消息列表 -->
        <scroll-view 
          class="message-list" 
          scroll-y 
          :scroll-into-view="scrollIntoView"
          @scrolltoupper="loadMoreMessages"
          upper-threshold="50"
        >
          <!-- 加载更多 -->
          <uni-load-more :status="loadMoreStatus" v-if="hasMoreMessages"></uni-load-more>
          
          <!-- 消息内容 -->
          <view 
            class="message-item" 
            v-for="(msg, index) in displayMessages" 
            :key="msg.created_at + '-' + index"
            :id="`msg-${index}`"
          >
            <view class="message-content" :class="{ 'user-message': msg.role === 'user', 'bot-message': msg.role === 'assistant' }">
              <!-- 用户消息 -->
              <template v-if="msg.role === 'user'">
                <view class="message-bubble">
                  <!-- 附件区域 -->
                  <view v-if="msg.attachments && msg.attachments.length" class="message-attachments">
                    <view v-for="file in msg.attachments" :key="file.id || file.filename" class="attachment-item" @tap.stop="previewAttachment(file, msg)">
                      <view class="attachment-icon-wrapper">
                        <text class="attachment-icon">📄</text>
                      </view>
                      <view class="attachment-info">
                        <text class="attachment-name">{{ file.filename || file.name || '附件' }}</text>
                        <text class="attachment-size" v-if="file.file_size">{{ formatFileSize(file.file_size) }}</text>
                      </view>
                    </view>
                  </view>
                  <!-- 文本内容 -->
                  <rich-text v-if="msg.content && msg.content !== '[已上传文件]'" :nodes="formatMessage(msg.content)"></rich-text>
                </view>
                <view class="avatar user-avatar">
                  <text class="iconfont icon-user"></text>
                </view>
              </template>
              
              <!-- 机器人消息 -->
              <template v-else>
                <view class="avatar bot-avatar">
                  <text class="iconfont icon-robot"></text>
                </view>
                <view class="message-bubble">
                  <!-- 附件区域 -->
                  <view v-if="msg.attachments && msg.attachments.length" class="message-attachments">
                    <view v-for="file in msg.attachments" :key="file.id || file.filename" class="attachment-item" @tap.stop="previewAttachment(file, msg)">
                      <view class="attachment-icon-wrapper">
                        <text class="attachment-icon">📄</text>
                      </view>
                      <view class="attachment-info">
                        <text class="attachment-name">{{ file.filename || file.name || '附件' }}</text>
                        <text class="attachment-size" v-if="file.file_size">{{ formatFileSize(file.file_size) }}</text>
                      </view>
                    </view>
                  </view>
                  <!-- 文本内容 -->
                  <rich-text v-if="msg.content && msg.content !== '[已上传文件]'" :nodes="formatMessage(msg.content)"></rich-text>
                </view>
              </template>
            </view>
            <view class="message-time">{{ formatTime(msg.created_at) }}</view>
          </view>
          
          <!-- 正在输入提示 -->
          <view class="typing-indicator" v-if="isTyping">
            <view class="avatar bot-avatar">
              <text class="iconfont icon-robot"></text>
            </view>
            <view class="typing-dots">
              <view class="dot"></view>
              <view class="dot"></view>
              <view class="dot"></view>
            </view>
          </view>
          
          <!-- 无消息时的提示 -->
          <view v-if="displayMessages.length === 0" class="welcome-container">
            <view class="welcome-message">
              <text class="welcome-title">欢迎与 {{ botInfo.name || '渡渡鸟助手' }} 对话</text>
              <text class="welcome-desc">{{ botInfo.description || '开始发送消息，与渡渡鸟助手对话' }}</text>
              <view class="welcome-tip">
                <text>{{ conversationId ? '此对话已保存' : '发送第一条消息时将自动创建会话' }}</text>
              </view>
            </view>
          </view>
        </scroll-view>
        
                
        <!-- 输入框包装器 -->
        <view class="input-wrapper">
          <view class="input-container">
            <!-- 附件选择提示 -->
            <view class="attachment-bar" v-if="selectedFile">
              <view class="attachment-chip">
                <text class="attachment-chip-icon">📎</text>
                <text class="attachment-chip-name">{{ selectedFile.name }}</text>
                <text class="attachment-chip-remove" @tap="clearSelectedFile">×</text>
              </view>
            </view>
            <view class="input-row">
              <view class="attach-btn" @tap="chooseAttachment">
                <text class="attach-icon">📎</text>
              </view>
              <textarea 
                class="message-input" 
                v-model="inputMessage" 
                placeholder="请输入问题（可附带一个文件）..." 
                :disabled="isTyping"
                auto-height
                @confirm="sendMessage"
                @input="handleInput"
              ></textarea>
              <view class="send-btn" :class="{ 'active': inputMessage.trim() || selectedFile }" @click="sendMessage">
                <text class="send-text">发送</text>
              </view>
            </view>
          </view>
        </view>
      </view>
    </view>
  </app-layout>
</template>

<script>
import api from '@/utils/api.js';
import { marked } from 'marked';
import AppLayout from '@/components/layout/AppLayout.vue';
import FilePreview from '@/components/file-preview/FilePreview.vue';
import { getCurrentUser } from '../../../utils/auth.js';
import { getPlatformType } from '../../../utils/platform-adapter.js';

export default {
  components: {
    AppLayout,
    FilePreview
  },
  data() {
    return {
      conversationId: null,
      botId: null,
      botInfo: {},
      messages: [],
      displayMessages: [],
      inputMessage: '',
      isTyping: false,
      scrollIntoView: '',
      page: 1,
      hasMoreMessages: false,
      loadMoreStatus: 'more',
      isPc: false,
      conversations: [],
      loadingConversations: false,
      lastUserQuestions: {}, // 存储每个对话的最后一个用户问题，用于显示对话标题
      userInfo: null,
      messageListWidth: 0, // 存储消息列表宽度
      showSidebar: false, // 控制侧边栏显示
      isInitialized: false, // 添加初始化标志
      _markdownCache: {}, // 添加内存缓存
      isPageLoading: true, // 页面加载状态
      _updatingInputWidth: false, // 添加输入框宽度更新标志
      selectedFile: null, // 当前选择的附件（单个）
      fileCache: {}, // 缓存已上传文件的本地路径，用于预览 {filename: path}
      showPreviewModal: false, // 预览弹窗显示状态
      previewFile: null, // 当前预览的文件信息
      _objectUrls: [] // 存储创建的 Object URL，用于释放内存
    }
  },
  computed: {
    isLoggedIn() {
      return !!this.userInfo && !!this.userInfo.id;
    },
  },
  created() {
    this.checkLoginStatus();
  },
  onLoad(options) {
    // 标记页面开始加载
    this.isPageLoading = true;
    
    // 确保用户已登录
    this.checkLoginStatus();
    
    // 清除缓存
    this.clearConversationCache();
    
    // 修正参数名称，确保能够正确获取
    this.conversationId = options.id || options.conversationId;
    this.botId = options.botId;
    
    // 检测设备类型
    this.checkDeviceType();
    
    // 获取机器人信息（如果有botId）
    if (this.botId) {
      this.getBotInfo();
    }
    
    // 获取对话历史（如果有conversationId）
    if (this.conversationId) {
      this.getConversationHistory();
    }
    
    // 获取对话列表
    this.fetchConversations();
    
    // 获取用户信息
    this.userInfo = getCurrentUser();
    
    // 监听用户信息更新事件
    uni.$on('userInfoUpdated', this.handleUserInfoUpdated);
    
    // 5秒后结束加载状态（无论是否加载完成）
    setTimeout(() => {
      this.isPageLoading = false;
    }, 5000);
  },
  onUnload() {
    // 移除事件监听
    uni.$off('userInfoUpdated', this.handleUserInfoUpdated);
  },
  mounted() {
    // 获取消息列表宽度并设置输入框宽度
    this.$nextTick(() => {
      // 添加延迟，等页面完全渲染
      setTimeout(() => {
        this.updateInputWidth();
        
        // 初始化完成后，设置一个标志
        this.isInitialized = true;
      }, 300);
    });
    
    // 监听窗口大小变化 - 仅在H5环境中
    // #ifdef H5
    window.addEventListener('resize', this.updateInputWidth);
    // #endif
  },
  beforeDestroy() {
    // 移除事件监听 - 仅在H5环境中
    // #ifdef H5
    window.removeEventListener('resize', this.updateInputWidth);
    
    // 释放所有创建的 Object URL，避免内存泄漏
    if (this._objectUrls && this._objectUrls.length > 0) {
      this._objectUrls.forEach(url => {
        try {
          URL.revokeObjectURL(url);
        } catch (e) {
          console.warn('释放 Object URL 失败:', e);
        }
      });
      this._objectUrls = [];
    }
    // #endif
    
    uni.$off('userInfoUpdated', this.handleUserInfoUpdated);
  },
  methods: {
    // 检查登录状态
    checkLoginStatus() {
      try {
        const token = uni.getStorageSync('token');
        const userInfoStr = uni.getStorageSync('userInfo');
        
        // 如果都没有，才跳转到登录页
        if (!token && !userInfoStr) {
          // 清除可能存在的标记
          uni.removeStorageSync('isLoggingOut');
          
          // 延迟跳转，避免在页面加载过程中立即跳转
          setTimeout(() => {
            // 再次检查，避免在延迟期间已经登录
            const retryToken = uni.getStorageSync('token');
            const retryUserInfo = uni.getStorageSync('userInfo');
            if (!retryToken && !retryUserInfo) {
              uni.reLaunch({
                url: '/pages/user/login/index'
              });
            }
          }, 100);
          return;
        }
        
        // 有 token 或 userInfo，尝试解析
        if (userInfoStr) {
          try {
            const userInfo = typeof userInfoStr === 'string' ? JSON.parse(userInfoStr) : userInfoStr;
            this.userInfo = userInfo;
          } catch (e) {
            console.warn('解析用户信息失败:', e);
            // 解析失败但不影响页面使用，只清空 userInfo
            this.userInfo = null;
          }
        }
      } catch (error) {
        console.error('检查登录状态异常:', error);
        // 异常情况下不强制跳转，让页面正常加载
      }
    },
    
    // 检测设备类型
    checkDeviceType() {
      uni.getSystemInfo({
        success: (res) => {
          this.isPc = res.windowWidth >= 768;
          // 设备类型变化时更新输入框宽度
          this.$nextTick(() => {
            this.updateInputWidth();
          });
        }
      });
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
        
        // 确保conversations始终是一个数组
        this.conversations = [];
        
        const response = await api.get(url, {}, true);
        
        if (response && (response.code === 'SUCCESS' || response.code === '0000')) {
          if (response.data && response.data.conversations && response.data.conversations.length > 0) {
            this.conversations = response.data.conversations;
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
    
    // 切换对话
    switchConversation(conversationId) {
      if (this.conversationId === conversationId) return;
      
      // 更新URL参数而不刷新页面 - 仅在H5环境中
      // #ifdef H5
      const url = `/pages/chat-modules/chat/index?conversationId=${conversationId}`;
      history.pushState({}, '', url);
      // #endif
      
      // 更新当前对话ID并加载对话历史
      this.conversationId = conversationId;
      this.getConversationHistory();
    },
    
    // 确认删除对话
    confirmDeleteConversation(conversationId) {
      // 直接删除对话，不显示确认弹窗
      this.deleteConversationById(conversationId);
    },
    
    // 删除指定对话
    async deleteConversationById(conversationId) {
      try {
        uni.showLoading({
          title: '删除中...'
        });
        
        const response = await api.delete(`/llm/conversations/${conversationId}`);

        uni.hideLoading();
        if (response.code === 'SUCCESS') {
          uni.showToast({
            title: '删除成功',
            icon: 'success'
          });
          
          // 刷新对话列表
          this.fetchConversations();
          
          // 如果删除的是当前对话，清除当前对话信息但不返回上一页
          if (this.conversationId === conversationId) {
            this.conversationId = null;
            this.messages = [];
            this.displayMessages = [];
            
            // 显示温馨提示
            uni.showToast({
              title: '请输入问题开始新对话',
              icon: 'none',
              duration: 2000
            });
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
    
    // 创建新对话（立即在当前机器人下创建一条新的会话）
    async createNewChat() {
      try {
        uni.showLoading({
          title: '正在创建对话...'
        });

        // 优先使用当前页面已有的 botId；如果没有，则取第一个机器人
        let targetBotId = this.botId;
        let targetBotInfo = this.botInfo;

        if (!targetBotId) {
          const resp = await api.get('/llm/bots', {}, true);
          if (!resp || !(resp.code === 'SUCCESS' || resp.code === '0000') || !resp.data.bots || !resp.data.bots.length) {
            uni.hideLoading();
            uni.showToast({
              title: '无可用机器人',
              icon: 'none'
            });
            return;
          }
          targetBotInfo = resp.data.bots[0];
          targetBotId = targetBotInfo.id;
        }

        // 调用后端创建对话
        const createResp = await api.post('/llm/conversations', { bot_id: targetBotId }, true);
        uni.hideLoading();

        if (createResp && createResp.code === 'SUCCESS' && createResp.data) {
          // 设置当前机器人和会话
          this.botId = targetBotId;
          this.botInfo = targetBotInfo || this.botInfo || {};
          this.conversationId = createResp.data.id;

          // 清空当前消息
          this.messages = [];
          this.displayMessages = [];

          // 刷新左侧对话列表（仅 PC 端需要）
          if (this.isPc) {
            this.fetchConversations();
          }

          uni.showToast({
            title: '已创建新对话',
            icon: 'success'
          });
        } else {
          uni.showToast({
            title: createResp?.message || '创建对话失败',
            icon: 'none'
          });
        }
      } catch (error) {
        uni.hideLoading();
        console.error('创建新对话失败:', error);
        uni.showToast({
          title: '创建对话失败',
          icon: 'none'
        });
      }
    },
    
    // 获取机器人信息
    async getBotInfo() {
      if (!this.botId) {
        return;
      }
      
      try {
        uni.showLoading({
          title: '加载中...'
        });
        
        // 直接调用API
        const response = await api.get(`/llm/bots/${this.botId}`);
        
        if (response && (response.code === 'SUCCESS' || response.code === '0000')) {
          this.botInfo = response.data || {};
          
          // 获取对话历史 - 仅在有conversationId时获取
          if (this.conversationId) {
            this.getConversationHistory();
          }
          
          uni.hideLoading();
          return true;
        } else {
          uni.showToast({
            title: response?.message || '获取机器人信息失败',
            icon: 'none'
          });
          uni.hideLoading();
          return false;
        }
      } catch (error) {
        uni.hideLoading();
        console.error('getBotInfo异常:', error);
        
        // 显示简单错误提示
        uni.showToast({
          title: '获取机器人信息失败',
          icon: 'none'
        });
        
        return false;
      } finally {
        // 确保加载状态被取消
        this.isPageLoading = false;
      }
    },
    
    // 获取对话历史
    async getConversationHistory() {
      if (!this.conversationId) {
        return;
      }
      

      try {
        // 显示加载状态
        uni.showLoading({
          title: '加载对话历史...'
        });
        
        // 如果有登录用户和会话ID，获取会话历史
        const response = await api.get(`/llm/conversations/${this.conversationId}`);

        uni.hideLoading();
        
        if (response && response.code === 'SUCCESS') {
          // 检查返回的数据是否有效
          if (response.data && response.data.messages) {
            // 更新机器人信息和消息列表
            this.botInfo = response.data.bot || this.botInfo;
            this.messages = response.data.messages || [];
            
            // 直接设置显示消息，不使用分批渲染
            this.displayMessages = this.messages;
            
            this.botId = response.data.conversation?.bot_id || this.botId;
            

            // 滚动到底部
            this.$nextTick(() => {
              this.scrollToBottom();
            });
          } else {
            // 清空消息列表
            this.messages = [];
            this.displayMessages = [];
          }
        } else {
          console.error('获取对话历史失败:', response?.message || '未知错误');
          uni.showToast({
            title: response?.message || '获取历史消息失败',
            icon: 'none'
          });
          
          // 清空消息列表
          this.messages = [];
          this.displayMessages = [];
        }
      } catch (error) {
        uni.hideLoading();
        console.error('获取对话历史异常:', error);
        uni.showToast({
          title: '获取历史消息失败',
          icon: 'none'
        });
        
        // 清空消息列表
        this.messages = [];
        this.displayMessages = [];
      } finally {
        uni.hideLoading();
        this.isPageLoading = false;
      }
    },
    
    // 加载更多历史消息
    loadMoreMessages() {
      // 实现分页加载更多消息的逻辑
      // ...
    },
    
    // 发送消息
    async sendMessage() {
      const message = this.inputMessage.trim();
      const hasFile = !!this.selectedFile;
      
      // 必须有文字或文件其中之一
      if (!message && !hasFile) return;
      if (this.isTyping) return;
      
      // 保存当前文件引用
      const currentFile = this.selectedFile;
      
      // 清空输入框和文件选择
      this.inputMessage = '';
      this.selectedFile = null;
      
      // 如果有文件，先显示文件消息
      if (currentFile) {
        this.fileCache[currentFile.name] = currentFile.fileObj || currentFile.path;
        const fileMessage = {
          role: 'user',
          content: '[已上传文件]',
          created_at: new Date().toISOString(),
          attachments: [{
            filename: currentFile.name,
            file_size: currentFile.size,
            _cached: true
          }]
        };
        this.messages.push(fileMessage);
      }
      
      // 如果有文字，再显示文字消息
      if (message) {
        const textMessage = {
          role: 'user',
          content: message,
          created_at: new Date().toISOString()
        };
        this.messages.push(textMessage);
      }
      
      this.$set(this, 'displayMessages', [...this.messages]);
      this.$nextTick(() => { this.scrollToBottom(); });
      this.isTyping = true;
      
      try {
        if (!this.botId) throw new Error('缺少机器人信息');
        
        if (this.conversationId) {
          if (currentFile) {
            const response = await api.upload(
              `/llm/conversations/${this.conversationId}`, 
              currentFile, 
              { question: message || '' }, 
              true
            );
            this.handleNormalResponse(response);
          } else {
            await this.sendStreamMessage(message, this.conversationId);
          }
        } else {
          const createResponse = await api.post('/llm/conversations', { bot_id: this.botId }, true);
          if (createResponse.code === 'SUCCESS') {
            this.conversationId = createResponse.data.id;
            if (currentFile) {
              const response = await api.upload(
                `/llm/conversations/${this.conversationId}`, 
                currentFile, 
                { question: message || '' }, 
                true
              );
              this.handleNormalResponse(response);
            } else {
              await this.sendStreamMessage(message, this.conversationId);
            }
            if (this.isPc) this.fetchConversations();
          } else {
            throw new Error(createResponse.message || '创建对话失败');
          }
        }
      } catch (error) {
        console.error('发送消息失败:', error);
        this.handleSendMessageError(error);
      }
    },
    
    // 发送流式消息
    async sendStreamMessage(message, conversationId) {
      return new Promise((resolve, reject) => {
        const botMessage = {
          role: 'assistant',
          content: '',
          created_at: new Date().toISOString(),
          isStreaming: true
        };
        this.messages.push(botMessage);
        this.$set(this, 'displayMessages', [...this.messages]);
        this.$nextTick(() => { this.scrollToBottom(); });
        
        const messageIndex = this.messages.length - 1;
        let hasError = false;
        
        api.streamPost(
          `/llm/conversations/${conversationId}/stream`,
          { question: message, bot_id: this.botId },
          (chunk) => {
            if (chunk.content) {
              this.messages[messageIndex].content += chunk.content;
              this.$set(this, 'displayMessages', [...this.messages]);
              this.$nextTick(() => { this.scrollToBottom(); });
            }
            if (chunk.error) {
              hasError = true;
              this.messages[messageIndex].content = `获取回复失败：${chunk.error}`;
              this.messages[messageIndex].isError = true;
              this.messages[messageIndex].isStreaming = false;
              this.$set(this, 'displayMessages', [...this.messages]);
              uni.showToast({ title: '获取回复失败', icon: 'none', duration: 2000 });
            }
          },
          true
        );
        
        setTimeout(() => {
          if (this.messages[messageIndex]) {
            this.messages[messageIndex].isStreaming = false;
          }
          this.isTyping = false;
          if (this.isPc) this.fetchConversations();
          resolve();
        }, 1000);
      });
    },
    
    // 处理普通API响应
    handleNormalResponse(response) {
      if (response && (response.code === 'SUCCESS' || response.code === '0000')) {
        this.messages.push({
          role: 'assistant',
          content: response.data.answer,
          created_at: new Date().toISOString()
        });
        this.$set(this, 'displayMessages', [...this.messages]);
        if (this.isPc) this.fetchConversations();
        this.$nextTick(() => { this.scrollToBottom(); });
      } else {
        this.handleApiError(response);
      }
      this.isTyping = false;
    },
    
    // 处理发送消息错误
    handleSendMessageError(error) {
      uni.showToast({ title: error.message || '发送消息失败', icon: 'none', duration: 2000 });
      this.messages.push({
        role: 'assistant',
        content: `发送消息失败：${error.message || '未知错误'}`,
        created_at: new Date().toISOString(),
        isError: true
      });
      this.$set(this, 'displayMessages', [...this.messages]);
      this.$nextTick(() => { this.scrollToBottom(); });
      this.isTyping = false;
    },
    
    // 处理API错误
    handleApiError(response) {
      // API返回错误
      uni.showToast({
        title: response?.message || '请求失败',
        icon: 'none',
        duration: 2000
      });
      
      // 添加一个系统消息，提示用户错误
      const errorMessage = {
        role: 'assistant',
        content: `获取回复失败：${response?.message || '未知错误'}`,
        created_at: new Date().toISOString(),
        isError: true
      };
      
      this.messages.push(errorMessage);
      this.$set(this, 'displayMessages', [...this.messages]);
      
      // 滚动到底部
      this.$nextTick(() => {
        this.scrollToBottom();
      });
    },
    
    // 滚动到底部
    scrollToBottom() {
      if (this.messages.length === 0) return;
      
      // 设置滚动到最后一条消息
      this.scrollIntoView = `msg-${this.messages.length - 1}`;
      
      // 不再使用复杂的DOM查询和计算，直接依赖scroll-into-view属性
    },
    
    // 处理输入事件
    handleInput(e) {
      // 自动增加输入框高度
    },
    
    // 格式化消息内容（支持markdown）
    formatMessage(content) {
      if (!content) return '';
      
      // 使用缓存避免重复解析
      if (this._markdownCache[content]) {
        return this._markdownCache[content];
      }
      
      // 直接返回原始内容，但添加到缓存中
      this._markdownCache[content] = content;
      return content;
    },
    
    // 格式化时间
    formatTime(timestamp) {
      if (!timestamp) return '';
      
      const date = new Date(timestamp);
      const now = new Date();
      const diff = (now - date) / 1000; // 秒数差
      
      if (diff < 60) {
        return '刚刚';
      } else if (diff < 3600) {
        return Math.floor(diff / 60) + '分钟前';
      } else if (diff < 86400) {
        return Math.floor(diff / 3600) + '小时前';
      } else {
        return `${date.getMonth()+1}月${date.getDate()}日 ${date.getHours()}:${date.getMinutes().toString().padStart(2, '0')}`;
      }
    },
    
    // 返回上一页
    goBack() {
      try {
        // 获取当前页面栈
        const pages = getCurrentPages();
        const pageStackLength = pages ? pages.length : 0;
        
        // 如果页面栈只有1页或为空（刷新后可能只有当前页），直接跳转到机器人列表
        if (pageStackLength <= 1) {
          this.navigateToBotList();
          return;
        }
        
        // 页面栈有多页，尝试返回
        uni.navigateBack({
          delta: 1,
          fail: (error) => {
            console.warn('navigateBack 失败:', error);
            // 返回失败，跳转到机器人列表
            this.navigateToBotList();
          }
        });
      } catch (error) {
        console.error('返回操作异常:', error);
        // 异常情况下，直接跳转到机器人列表
        this.navigateToBotList();
      }
    },
    
    // 跳转到机器人列表（统一处理）
    navigateToBotList() {
      if (this.isPc) {
        uni.reLaunch({
          url: '/pages/bot-modules/bot-list/index'
        });
      } else {
        // 移动端尝试 switchTab，失败则用 reLaunch
        uni.switchTab({
          url: '/pages/bot-modules/bot-list/index',
          fail: () => {
            uni.reLaunch({
              url: '/pages/bot-modules/bot-list/index'
            });
          }
        });
      }
    },
    
    // 显示菜单
    showMenu() {
      uni.showActionSheet({
        itemList: ['删除对话', '查看机器人信息'],
        success: (res) => {
          if (res.tapIndex === 0) {
            this.deleteConversation();
          } else if (res.tapIndex === 1) {
            this.viewBotInfo();
          }
        }
      });
    },
    
    // 删除当前对话
    async deleteConversation() {
      if (!this.conversationId) return;
      
      this.confirmDeleteConversation(this.conversationId);
    },
    
    // 查看机器人信息
    viewBotInfo() {
      uni.navigateTo({
        url: `/pages/bot-modules/bot-detail/index?botId=${this.botId}`
      });
    },
    
    // 获取最后一个用户问题
    async getLastUserQuestion(conversationId) {
      try {
        const response = await api.get(`/llm/conversations/${conversationId}`);
        
        if (response.code === 'SUCCESS' && response.data.messages) {
          const userMessages = response.data.messages.filter(msg => msg.role === 'user');
          if (userMessages.length > 0) {
            const lastQuestion = userMessages[userMessages.length - 1].content;
            // 保存到本地缓存
            this.$set(this.lastUserQuestions, conversationId, lastQuestion);
          }
        }
      } catch (error) {
        console.error(`获取对话${conversationId}的最后问题失败:`, error);
      }
    },
    
    // 获取对话标题
    getConversationTitle(conversation) {
      // 首先尝试从本地缓存获取最后一个用户问题
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
    
    // 处理用户信息更新事件
    handleUserInfoUpdated(userInfo) {
      this.userInfo = userInfo;
      
      // 检查是否正在退出应用
      const isExitingApp = uni.getStorageSync('isExitingApp');
      if (isExitingApp === 'true') {
        return;
      }
      
      // 重新加载对话列表
      if (userInfo && userInfo.id) {
        this.fetchConversations();
      } else {
        // 清空对话列表
        this.conversations = [];
      }
    },
    
    // 添加新方法：保存当前对话和消息
    async saveConversation() {
      if (!this.botId || this.messages.length === 0) return;
      
      try {
        // 显示加载提示
        uni.showLoading({
          title: '保存对话中...'
        });
        
        // 创建新对话
        const createResponse = await api.post('/api/llm/conversations', {
          bot_id: this.botId,
          messages: this.messages // 将所有消息一起发送给后端
        });
        
        if (createResponse.code === 'SUCCESS') {
          this.conversationId = createResponse.data.id;
          
          uni.showToast({
            title: '对话已保存',
            icon: 'success'
          });
          
          // 刷新左侧对话列表
          if (this.isPc) {
            this.fetchConversations();
          }
        } else {
          uni.showToast({
            title: createResponse.message || '保存失败',
            icon: 'none'
          });
        }
      } catch (error) {
        console.error('保存对话失败:', error);
        uni.showToast({
          title: '保存对话失败',
          icon: 'none'
        });
      } finally {
        uni.hideLoading();
      }
    },
    
    // 更新输入框宽度
    updateInputWidth() {
      // 如果已经在处理中，则不重复执行
      if (this._updatingInputWidth) return;
      this._updatingInputWidth = true;
      
      this.$nextTick(() => {
        // 检查是否正在退出登录
        const isLoggingOut = uni.getStorageSync('isLoggingOut');
        if (isLoggingOut === 'true') {
          this._updatingInputWidth = false;
          return;
        }
        
        // 只在PC模式下执行
        if (this.isPc) {
          // #ifdef H5
          // 使用uni.createSelectorQuery代替document
          const query = uni.createSelectorQuery().in(this);
          query.select('.chat-container').boundingClientRect(data => {
            if (data) {
              // 获取聊天容器宽度并直接设置
              this.messageListWidth = data.width;
            }
            this._updatingInputWidth = false;
          }).exec();
          // #endif
          
          // #ifdef APP-PLUS
          // 在APP平台上简化处理
          const appQuery = uni.createSelectorQuery().in(this);
          appQuery.select('.chat-container').boundingClientRect(data => {
            if (data) {
              this.messageListWidth = data.width;
            }
            this._updatingInputWidth = false;
          }).exec();
          // #endif
        } else {
          this._updatingInputWidth = false;
        }
      });
    },
    
    // 切换侧边栏显示状态
    toggleSidebar() {
      this.showSidebar = !this.showSidebar;
      
      // 如果打开侧边栏，确保对话列表已加载
      if (this.showSidebar && this.conversations.length === 0) {
        this.fetchConversations();
      }
      
      // 强制更新视图
      this.$forceUpdate();
    },
    
    // 清除对话缓存
    clearConversationCache() {
      // 清空对话列表
      this.conversations = [];
      // 清空对话内容
      if (!this.conversationId) {
        this.messages = [];
        this.displayMessages = [];
      }
      // 清空缓存的对话标题
      this.lastUserQuestions = {};
    },
    
    // 格式化文件大小
    formatFileSize(bytes) {
      if (!bytes || bytes === 0) return '0 B';
      const k = 1024;
      const sizes = ['B', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },
    
    // 判断附件是否支持预览
    isAttachmentPreviewable(file, msg) {
      const filename = file.filename || file.name;
      // 仅PC端支持预览
      return this.isPc && ((filename && this.fileCache[filename]) || !!file.preview_url);
    },
    
    // 预览附件
    previewAttachment(file, msg) {
      if (!this.isPc) {
        uni.showToast({ title: '仅支持在PC端预览', icon: 'none' });
        return;
      }
      const filename = file.filename || file.name;
      
      // 优先检查是否有缓存文件（刚上传的文件，还未保存到数据库）
      if (filename && this.fileCache[filename]) {
        const cachedFile = this.fileCache[filename];
        this.openFile(cachedFile, filename);
        return;
      }
      
      // 如果没有缓存，使用数据库返回的URL（从数据库查询的文件）
      // 尝试多个可能的URL字段
      const url = file.preview_url || file.url || file.minio_url || file.file_url;
      if (!url) {
        uni.showToast({ title: '文件链接不可用', icon: 'none' });
        return;
      }
      
      this.openFile(url, filename);
    },
    
    // 选择附件
    async chooseAttachment() {
      try {
        const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB
        
        // #ifdef H5
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.txt,.pdf,.doc,.docx,.md,.jpg,.jpeg,.png,.gif,.bmp,.webp';
        input.onchange = (e) => {
          const file = e.target.files[0];
          if (file) {
            // 检查文件大小
            if (file.size > MAX_FILE_SIZE) {
              uni.showToast({ 
                title: '文件大小超过50MB限制', 
                icon: 'none',
                duration: 3000
              });
              return;
            }
            this.selectedFile = {
              name: file.name,
              size: file.size,
              path: null,
              fileObj: file
            };
          }
        };
        input.click();
        // #endif
        
        // #ifdef MP-WEIXIN
        uni.chooseMessageFile({
          count: 1,
          type: 'file',
          extension: ['doc', 'docx', 'pdf', 'txt', 'md', 'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'],
          maxSize: MAX_FILE_SIZE,
          success: (res) => {
            if (res.tempFiles && res.tempFiles.length > 0) {
              const file = res.tempFiles[0];
              if (file.size > MAX_FILE_SIZE) {
                uni.showToast({ 
                  title: '文件大小超过50MB限制', 
                  icon: 'none',
                  duration: 3000
                });
                return;
              }
              this.selectedFile = file;
            }
          },
          fail: (err) => {
            console.error('选择文件失败:', err);
            uni.showToast({ title: '选择文件失败', icon: 'none' });
          }
        });
        // #endif
        
        // #ifdef APP-PLUS
        uni.chooseImage({
          count: 1,
          success: (res) => {
            if (res.tempFilePaths && res.tempFilePaths.length > 0) {
              const fileSize = res.tempFiles && res.tempFiles[0] ? res.tempFiles[0].size : 0;
              if (fileSize > MAX_FILE_SIZE) {
                uni.showToast({ 
                  title: '文件大小超过50MB限制', 
                  icon: 'none',
                  duration: 3000
                });
                return;
              }
              this.selectedFile = {
                path: res.tempFilePaths[0],
                name: res.tempFilePaths[0].substring(res.tempFilePaths[0].lastIndexOf('/') + 1) || '附件',
                size: fileSize
              };
            }
          },
          fail: (err) => {
            console.error('选择文件失败:', err);
            uni.showToast({ title: '选择文件失败', icon: 'none' });
          }
        });
        // #endif
      } catch (error) {
        console.error('选择附件失败:', error);
        uni.showToast({ title: '选择文件失败', icon: 'none' });
      }
    },
    
    // 清除已选择的附件
    clearSelectedFile() {
      this.selectedFile = null;
    },
    
    // 预览已选择的文件
    previewSelectedFile() {
      if (!this.selectedFile) return;

      if (!this.isPc) {
        uni.showToast({ title: '仅支持在PC端预览', icon: 'none' });
        return;
      }
      // #ifdef H5
      if (this.selectedFile.fileObj) {
        this.openFile(this.selectedFile.fileObj);
      } else {
        uni.showToast({ title: '无法预览该文件', icon: 'none' });
      }
      // #endif
      
      // #ifndef H5
      // 非H5平台使用原来的uni.openDocument
      uni.openDocument({
        filePath: this.selectedFile.path,
        showMenu: true,
        fail: () => uni.showToast({ title: '无法打开文件', icon: 'none' })
      });
      // #endif
    },
    
    // 统一文件打开方法
    openFile(fileSource, originalFilename) {
      if (!this.isPc) {
        uni.showToast({ title: '仅支持在PC端预览', icon: 'none' });
        return;
      }
      // #ifdef H5
      
      let fileUrl = fileSource;
      let fileExt = '';
      let displayName = originalFilename || '';
      
      // 如果 fileSource 是 File 对象，需要创建 Object URL
      if (fileSource instanceof File || (fileSource && fileSource.name && fileSource.size !== undefined)) {
        // 是 File 对象
        fileUrl = URL.createObjectURL(fileSource);
        displayName = fileSource.name || originalFilename || '文件';
        const parts = displayName.split('.');
        fileExt = parts.length > 1 ? parts.pop().toLowerCase() : '';
        
        // 存储 Object URL，关闭预览时释放
        if (!this._objectUrls) {
          this._objectUrls = [];
        }
        this._objectUrls.push(fileUrl);
      } else if (typeof fileSource === 'string') {
        // 是 URL 字符串
        fileUrl = fileSource;
        
        // 从文件名提取扩展名
        if (originalFilename) {
          const parts = originalFilename.split('.');
          fileExt = parts.length > 1 ? parts.pop().toLowerCase() : '';
        }
        
        // 如果没有扩展名，从URL提取
        if (!fileExt) {
          fileExt = this.getFileExtFromUrl(fileSource);
        }
        
        // 获取显示名称
        if (!displayName) {
          try {
            displayName = decodeURIComponent(new URL(fileSource).pathname.split('/').pop() || '');
          } catch (e) {
            displayName = fileSource.split('/').pop() || '文件';
          }
        }
      } else {
        uni.showToast({ title: '不支持的文件类型', icon: 'none' });
        return;
      }

      this.previewFile = {
        url: fileUrl,
        filename: displayName,
        ext: fileExt
      };

      // 如果是文本文件，需要加载内容
      if (this.isTextFile(this.previewFile)) {
        // File 对象需要先读取内容
        if (fileSource instanceof File || (fileSource && fileSource.name && fileSource.size !== undefined)) {
          const reader = new FileReader();
          reader.onload = (e) => {
            if (this.previewFile) {
              this.previewFile.content = e.target.result;
            }
          };
          reader.onerror = () => {
            if (this.previewFile) {
              this.previewFile.content = '无法加载文件内容';
            }
          };
          reader.readAsText(fileSource);
        } else {
          this.loadTextFileContent(fileUrl);
        }
      }
      
      this.showPreviewModal = true;

      // #endif
      
      // #ifndef H5
      // 非H5平台使用原来的uni.openDocument
      uni.openDocument({
        filePath: fileSource,
        showMenu: true,
        fail: () => uni.showToast({ title: '无法打开文件', icon: 'none' })
      });
      // #endif
    },
    
    // 关闭预览弹窗
    closePreviewModal() {
      // #ifdef H5
      // 释放所有创建的 Object URL，避免内存泄漏
      if (this._objectUrls && this._objectUrls.length > 0) {
        this._objectUrls.forEach(url => {
          try {
            URL.revokeObjectURL(url);
          } catch (e) {
            console.warn('释放 Object URL 失败:', e);
          }
        });
        this._objectUrls = [];
      }
      // #endif
      
      this.showPreviewModal = false;
      this.previewFile = null;
    },
    
    // 预览组件渲染完成
    onPreviewRendered() {
      console.log('文件预览渲染完成');
    },
    
    // 预览组件加载失败
    onPreviewError(e) {
      console.error('文件预览失败:', e);
    },
    
    // 预览组件下载事件
    onPreviewDownload() {
      console.log('文件下载');
    },
    
    // 判断是否为图片文件
    isImageFile(file) {
      const imageExts = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'];
      return imageExts.includes(file.ext);
    },
    
    // 判断是否为PDF文件
    isPdfFile(file) {
      return file.ext === 'pdf';
    },
    
    // 判断是否为Office文件
    isOfficeFile(file) {
      const officeExts = ['doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx'];
      return !!file && officeExts.includes(file.ext);
    },
    
    // 生成Office在线预览URL（仅PC/H5使用）
    getOfficeViewerUrl(url) {
      if (typeof url === 'string' && url.startsWith('https://')) {
        return `https://view.officeapps.live.com/op/embed.aspx?src=${encodeURIComponent(url)}`;
      }
      return `https://docs.google.com/gview?embedded=1&url=${encodeURIComponent(url)}`;
    },
    
    // 判断是否为文本文件
    isTextFile(file) {
      const textExts = ['txt', 'md', 'log', 'csv', 'json', 'xml', 'html', 'css', 'js'];
      return textExts.includes(file.ext);
    },
    
    // 加载文本文件内容
    async loadTextFileContent(url) {
      try {
        const response = await fetch(url);
        const text = await response.text();
        if (this.previewFile) {
          this.previewFile.content = text;
        }
      } catch (e) {
        if (this.previewFile) {
          this.previewFile.content = '无法加载文件内容';
        }
      }
    },
    
    // 下载文件
    downloadFile(url) {
      const a = document.createElement('a');
      a.href = url;
      a.download = url.split('/').pop() || 'download';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    },
    
    // 在新窗口打开
    openInNewWindow(url) {
      window.open(url, '_blank');
    },
    
    // 显示文件预览
    showFilePreview(url, filename) {
      // #ifdef H5
      
      // 优先从文件名提取扩展名，如果没有文件名再从URL提取
      let fileExt = '';
      if (filename) {
        const parts = filename.split('.');
        fileExt = parts.length > 1 ? parts.pop().toLowerCase() : '';
      }
      if (!fileExt) {
        fileExt = this.getFileExtFromUrl(url);
      }
      
      let displayName = filename;
      if (!displayName) {
        try {
          displayName = decodeURIComponent(new URL(url).pathname.split('/').pop() || '');
        } catch (e) {
          displayName = url.split('/').pop();
        }
      }

      this.previewFile = {
        url: url,
        filename: displayName,
        ext: fileExt
      };

      // 如果是文本文件，需要加载内容
      if (this.isTextFile(this.previewFile)) {
        this.loadTextFileContent(url);
      }
      
      this.showPreviewModal = true;

      // #endif
      
      // #ifndef H5
      // 非H5平台使用原来的uni.openDocument
      uni.openDocument({
        filePath: url,
        showMenu: true,
        fail: () => uni.showToast({ title: '无法打开文件', icon: 'none' })
      });
      // #endif
    },
    
    // 从URL中获取文件扩展名
    getFileExtFromUrl(url) {
      try {
        const pathname = new URL(url).pathname;
        const parts = pathname.split('.');
        return parts.length > 1 ? parts.pop().toLowerCase() : '';
      } catch (e) {
        // 如果URL解析失败，尝试从字符串中提取
        const match = url.match(/\.([^.?#]+)(?:\?|#|$)/);
        return match ? match[1].toLowerCase() : '';
      }
    },
  }
}
</script>

<style lang="scss">
/* 全屏模式样式 */
.chat-fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  width: 100vw;
  height: 100vh;
  z-index: 1000;
  background-color: #f5f7fa;
}

/* PC端输入框样式 */
.pc-input-wrapper {
  width: calc(100% - 300rpx) !important;
  left: 300rpx;
}

/* 全局加载状态 */
.global-loading {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0.8);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  z-index: 9999;
}

.loading-spinner {
  width: 60rpx;
  height: 60rpx;
  border: 4rpx solid #f3f3f3;
  border-top: 4rpx solid #007AFF;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 20rpx;
}

.loading-text {
  font-size: 28rpx;
  color: #666;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.chat-layout {
  display: flex;
  width: 100%;
  height: 100vh; /* 使用视口高度 */
  background-color: #f5f7fa;
  overflow: hidden; /* 防止内容溢出 */
}

/* 返回按钮样式 */
.back-button-wrapper {
  position: absolute;
  top: 10px;
  left: 10px;
  z-index: 1001;
}

.back-button {
  display: flex;
  align-items: center;
  padding: 8px 15px;
  background-color: rgba(255, 255, 255, 0.9);
  border-radius: 20px;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
  cursor: pointer;
}

.back-icon {
  font-size: 14px;
  font-weight: bold;
  color: #007AFF;
}

/* 左侧对话列表 */
.conversation-sidebar {
  width: 300rpx;
  height: 100%;
  background-color: #fff;
  border-right: 1px solid #e0e0e0;
  display: flex;
  flex-direction: column;
  flex-shrink: 0; /* 防止侧边栏被压缩 */
  z-index: 10; /* 确保侧边栏在上层 */
}

.sidebar-header {
  padding: 20rpx;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  height: 80rpx;
}

.sidebar-title {
  font-size: 28rpx;
  font-weight: bold;
  color: #333;
}

.new-chat-btn {
  background-color: var(--primary-color, #007AFF);
  color: white;
  font-size: 24rpx;
  border-radius: 30rpx;
  height: 60rpx;
  line-height: 60rpx;
  padding: 0 20rpx;
  display: flex;
  align-items: center;
  justify-content: center;
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
  border-bottom: 1rpx solid #eee;
  display: flex;
  align-items: center;
  cursor: pointer;
  transition: background-color 0.2s;
  position: relative;
}

.conversation-item:hover {
  background-color: #f9f9f9;
}

.conversation-item.active {
  background-color: #e6f7ff;
  border-left: 4rpx solid #1890ff;
}

.conversation-info {
  flex: 1;
  overflow: hidden;
}

.conversation-name {
  font-size: 28rpx;
  color: #333;
  margin-bottom: 8rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: block;
}

.conversation-time {
  font-size: 24rpx;
  color: #999;
  display: block;
}

.delete-btn {
  color: #fff;
  font-size: 28rpx;
  font-weight: normal;
  min-width: 80rpx;
  height: 60rpx;
  padding: 0 20rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 1;
  border-radius: 30rpx;
  line-height: 1;
  background-color: #ff4d4f;
  cursor: pointer;
  z-index: 10;
  margin-left: 10rpx;
  border: none;
}

.delete-btn:active {
  background-color: #ff7875;
  transform: scale(0.95);
}

/* 聊天主界面 */
.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: #ffffff;
  height: 100%;
  overflow: hidden; /* 防止内容溢出 */
  position: relative; /* 添加相对定位 */
}

/* 消息列表 */
.message-list {
  flex: 1;
  padding: 20rpx;
  padding-bottom: 140rpx; /* 为输入框留出空间 */
  overflow-y: auto;
  position: absolute; /* 绝对定位 */
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  box-sizing: border-box;
}

.message-item {
  margin-bottom: 30rpx;
  animation: fadeIn 0.3s ease-out;
}

.message-content {
  display: flex;
  align-items: flex-start;
  margin-bottom: 6rpx;
}

.message-content.user-message {
  flex-direction: row-reverse;
  justify-content: flex-start;
}

.avatar {
  width: 80rpx;
  height: 80rpx;
  border-radius: 40rpx;
  display: flex;
  justify-content: center;
  align-items: center;
  flex-shrink: 0;
}

.avatar .iconfont {
  font-size: 40rpx;
}

.user-avatar {
  background-color: #e6f7ff;
}

.user-avatar .iconfont {
  color: #1890ff;
}

.bot-avatar {
  background-color: #f6ffed;
}

.bot-avatar .iconfont {
  color: #52c41a;
}

.message-bubble {
  max-width: 70%;
  padding: 20rpx 24rpx;
  border-radius: 16rpx;
  margin: 0 16rpx;
  word-break: break-word;
}

.user-message .message-bubble {
  background-color: #007AFF;
  color: #fff;
  border-top-right-radius: 4rpx;
  box-shadow: 0 2rpx 8rpx rgba(0, 122, 255, 0.2);
}

.bot-message .message-bubble {
  background-color: #fff;
  color: #333;
  border-top-left-radius: 4rpx;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.1);
}

/* 改进富文本样式 */
.message-bubble rich-text {
  line-height: 1.6;
}

/* 富文本内容样式 */
.message-bubble rich-text p {
  margin: 0 0 10rpx 0;
}

.message-bubble rich-text pre {
  background-color: rgba(0, 0, 0, 0.05);
  padding: 12rpx;
  border-radius: 6rpx;
  overflow-x: auto;
  margin: 10rpx 0;
  font-family: monospace;
}

.message-bubble rich-text code {
  font-family: Consolas, Monaco, monospace;
  font-size: 24rpx;
}

.user-message .message-bubble rich-text code {
  background-color: rgba(255, 255, 255, 0.2);
  padding: 2rpx 6rpx;
  border-radius: 4rpx;
}

.bot-message .message-bubble rich-text code {
  background-color: rgba(0, 0, 0, 0.05);
  padding: 2rpx 6rpx;
  border-radius: 4rpx;
}

.message-bubble rich-text ul,
.message-bubble rich-text ol {
  padding-left: 40rpx;
  margin: 10rpx 0;
}

.message-bubble rich-text a {
  color: #1890ff;
  text-decoration: underline;
}

.user-message .message-bubble rich-text a {
  color: #ffffff;
}

.message-bubble rich-text blockquote {
  border-left: 4rpx solid #bbb;
  padding: 0 15rpx;
  color: #666;
  margin: 10rpx 0;
}

.user-message .message-bubble rich-text blockquote {
  border-left: 4rpx solid rgba(255, 255, 255, 0.5);
  color: rgba(255, 255, 255, 0.9);
}

.message-time {
  font-size: 24rpx;
  color: #bbb;
  text-align: center;
  margin-top: 10rpx;
}

.typing-indicator {
  display: flex;
  align-items: flex-start;
  margin-bottom: 30rpx;
}

.typing-dots {
  display: flex;
  align-items: center;
  background-color: #fff;
  padding: 16rpx 24rpx;
  border-radius: 8rpx;
  margin-left: 16rpx;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.05);
}

.dot {
  width: 12rpx;
  height: 12rpx;
  background-color: #bbb;
  border-radius: 50%;
  margin: 0 6rpx;
  animation: typing 1.5s infinite ease-in-out;
}

.dot:nth-child(1) {
  animation-delay: 0s;
}

.dot:nth-child(2) {
  animation-delay: 0.2s;
}

.dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0% {
    transform: translateY(0);
    opacity: 0.3;
  }
  50% {
    transform: translateY(-6rpx);
    opacity: 1;
  }
  100% {
    transform: translateY(0);
    opacity: 0.3;
  }
}

/* 输入框包装器 */
.input-wrapper {
  position: fixed; /* 固定定位 */
  bottom: 0;
  min-height: 120rpx;
  background-color: #fff;
  border-top: 1rpx solid #eee;
  z-index: 100;
  box-sizing: border-box;
  transition: width 0.3s, left 0.3s, right 0.3s; /* 添加过渡效果 */
  width: 100%;
  left: 0;
  padding: 20rpx;
}

/* 输入框容器 */
.input-container {
  min-height: 100%;
  padding: 20rpx;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
  width: 100%;
}

.message-input {
  flex: 1;
  padding: 20rpx;
  background-color: #ffffff;
  border: none;
  outline: none;
  font-size: 28rpx;
  line-height: 1.5;
  min-height: 80rpx;
  max-height: 300rpx;
  box-sizing: border-box;
  resize: none;
}

.send-btn {
  width: auto;
  min-width: 100rpx;
  height: 80rpx;
  margin-left: 20rpx;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #f5f5f5;
  border-radius: 40rpx;
  padding: 0 20rpx;
  flex-shrink: 0;
}

.send-text {
  font-size: 28rpx;
  color: #999;
}

.send-btn.active {
  background-color: #1890ff;
  cursor: pointer;
}

.send-btn.active .send-text {
  color: #fff;
}

/* 空状态和加载状态 */
.empty-state, .loading-state {
  padding: 40rpx;
  text-align: center;
  color: #999;
  font-size: 24rpx;
}

.empty-text {
  display: block;
  margin-bottom: 10rpx;
}

/* 添加欢迎消息样式 */
.welcome-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 40rpx;
}

.welcome-message {
  background-color: #ffffff;
  border-radius: 16rpx;
  padding: 40rpx;
  text-align: center;
  box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.05);
  max-width: 80%;
}

.welcome-title {
  font-size: 36rpx;
  font-weight: bold;
  color: #333;
  margin-bottom: 20rpx;
  display: block;
}

.welcome-desc {
  font-size: 28rpx;
  color: #666;
  margin-bottom: 30rpx;
  display: block;
}

.welcome-tip {
  font-size: 24rpx;
  color: #999;
  background-color: #f9f9f9;
  padding: 16rpx;
  border-radius: 8rpx;
  margin-top: 20rpx;
}

/* 消息动画 */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10rpx);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 为PC模式添加特殊处理 */
@media screen and (min-width: 768px) {
  .chat-layout {
    flex-direction: row; /* 确保在PC模式下是水平排列 */
  }
  
  .conversation-sidebar {
    width: 300rpx; /* 固定宽度 */
  }
  
  .chat-container {
    width: calc(100% - 300rpx); /* 设置宽度为剩余空间 */
  }
  
  /* PC端输入框样式 */
  .pc-input-wrapper {
    width: calc(100% - 300rpx) !important; /* 确保宽度与聊天容器相同 */
    left: 300rpx; /* 与侧边栏宽度相同 */
  }
}

/* 移动端侧边栏样式 */
.sidebar-mobile {
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  width: 80%;
  z-index: 1001;
  background: white;
  box-shadow: 2px 0 10px rgba(0, 0, 0, 0.15);
  transform: translateX(0);
}

.sidebar-mask {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.4);
  z-index: 1000;
  animation: fadeIn 0.3s ease;
}

.close-sidebar-btn {
  position: absolute;
  top: 15px;
  right: 15px;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.1);
  border-radius: 50%;
  z-index: 10;
}

.close-icon {
  font-size: 20px;
  color: #666;
}

/* 侧边栏切换按钮 */
.sidebar-toggle {
  position: absolute;
  top: 50%;
  left: 0;
  transform: translateY(-50%);
  z-index: 10;
  height: 80px;
  display: flex;
  align-items: center;
}

.toggle-btn {
  width: 18px;
  height: 60px;
  background-color: rgba(0, 122, 255, 0.1);
  border-radius: 0 4px 4px 0;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 1px 0 5px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.toggle-btn:active {
  background-color: rgba(0, 122, 255, 0.2);
  transform: translateX(2px);
}

.toggle-icon {
  font-size: 18px;
  color: #007AFF;
  font-weight: bold;
}

/* 聊天界面在有侧边栏时的样式 */
.chat-container.with-sidebar {
  margin-left: 0;
}

/* 移动端返回按钮样式 */
.mobile-header {
  position: sticky;
  top: 0;
  left: 0;
  right: 0;
  padding: 12px 15px;
  background-color: #ffffff;
  display: flex;
  align-items: center;
  z-index: 10;
  border-bottom: 1px solid #eee;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.chat-title {
  font-size: 16px;
  font-weight: bold;
  color: #333;
  flex: 1;
  text-align: center;
  margin-right: 44px; /* 平衡左侧返回按钮的宽度 */
}

/* 移动端消息列表调整 */
.app-layout .message-list {
  padding-top: 50px; /* 为标题栏留出空间 */
}

/* 移动端返回按钮样式 */
.mobile-header .back-button {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 5px 10px;
  border-radius: 4px;
  background-color: transparent;
}

.mobile-header .back-icon {
  font-size: 14px;
  color: #333;
}

/* 附件样式 */
.message-attachments {
  margin-bottom: 10rpx;
}

.attachment-item {
  display: flex;
  align-items: center;
  padding: 16rpx;
  background-color: rgba(255, 255, 255, 0.1);
  border-radius: 8rpx;
  margin-bottom: 8rpx;
  cursor: pointer;
  transition: background-color 0.2s;
}

.attachment-item:hover {
  background-color: rgba(255, 255, 255, 0.15);
}

.bot-message .attachment-item {
  background-color: #f5f5f5;
}

.bot-message .attachment-item:hover {
  background-color: #ececec;
}

.attachment-icon-wrapper {
  margin-right: 12rpx;
}

.attachment-icon {
  font-size: 40rpx;
}

.attachment-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.attachment-name {
  font-size: 28rpx;
  color: #333;
  margin-bottom: 4rpx;
  word-break: break-all;
}

.user-message .attachment-name {
  color: #fff;
}

.attachment-size {
  font-size: 24rpx;
  color: #999;
}

.user-message .attachment-size {
  color: rgba(255, 255, 255, 0.7);
}

.attachment-preview-tag {
  font-size: 24rpx;
  color: #007AFF;
  padding: 4rpx 12rpx;
  border-radius: 4rpx;
  background-color: rgba(0, 122, 255, 0.1);
  white-space: nowrap;
}

.user-message .attachment-preview-tag {
  color: #fff;
  background-color: rgba(255, 255, 255, 0.2);
}

/* 输入框区域样式 */
.input-row {
  display: flex;
  align-items: flex-end;
  gap: 10rpx;
}

.attach-btn {
  width: 80rpx;
  height: 80rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f5f5f5;
  border-radius: 8rpx;
  cursor: pointer;
  transition: background-color 0.2s;
  flex-shrink: 0;
}

.attach-btn:hover {
  background-color: #e8e8e8;
}

.attach-btn:active {
  background-color: #d8d8d8;
}

.attach-icon {
  font-size: 36rpx;
}

/* 附件提示栏 */
.attachment-bar {
  padding: 16rpx;
  background-color: #f9f9f9;
  border-bottom: 1rpx solid #e8e8e8;
}

.attachment-chip {
  display: inline-flex;
  align-items: center;
  padding: 8rpx 16rpx;
  background-color: #e6f7ff;
  border-radius: 16rpx;
  max-width: 100%;
  cursor: pointer;
  transition: background-color 0.2s;
}

.attachment-chip:hover {
  background-color: #bae7ff;
}

.attachment-chip-icon {
  font-size: 28rpx;
  margin-right: 8rpx;
}

.attachment-chip-name {
  font-size: 26rpx;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 300rpx;
}

.attachment-chip-size {
  font-size: 22rpx;
  color: #666;
  margin-left: 8rpx;
  flex-shrink: 0;
}

.attachment-chip-remove {
  font-size: 36rpx;
  color: #999;
  margin-left: 12rpx;
  cursor: pointer;
  padding: 0 8rpx;
  line-height: 1;
}

.attachment-chip-remove:hover {
  color: #666;
}

/* 预览弹窗样式 */
.preview-modal-overlay {
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
  right: 0 !important;
  bottom: 0 !important;
  background: rgba(0, 0, 0, 0.7) !important;
  z-index: 99999 !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
}

.preview-modal {
  background: white;
  border-radius: 8px;
  width: 90vw;
  height: 80vh;
  max-width: 1200px;
  max-height: 800px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.preview-modal-header {
  padding: 16px 20px;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #f8f9fa;
}

.preview-title {
  font-size: 16px;
  font-weight: bold;
  color: #333;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.preview-close {
  font-size: 24px;
  color: #666;
  cursor: pointer;
  padding: 4px 8px;
  margin: -4px -8px;
}

.preview-close:hover {
  color: #333;
  background: #e9ecef;
  border-radius: 4px;
}

.preview-modal-content {
  flex: 1;
  overflow: auto;
  padding: 0;
}

.preview-content-wrapper {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  display: block;
  margin: auto;
}

.office-preview-container {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.office-fallback {
  text-align: center;
  padding: 40px 20px;
  color: #666;
}

.fallback-icon {
  font-size: 64px;
  margin-bottom: 20px;
  display: block;
}

.fallback-title {
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 12px;
  display: block;
  color: #333;
  word-break: break-all;
}

.fallback-desc {
  font-size: 14px;
  margin-bottom: 8px;
  display: block;
  color: #666;
}

.fallback-tip {
  font-size: 12px;
  color: #999;
  margin-bottom: 24px;
  display: block;
}

.fallback-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  flex-wrap: wrap;
}

.preview-iframe {
  width: 100%;
  height: 100%;
  border: none;
}

.preview-text {
  padding: 20px;
  font-family: monospace;
  font-size: 14px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-all;
  overflow: auto;
  width: 100%;
  height: 100%;
  box-sizing: border-box;
}

.preview-unsupported {
  text-align: center;
  padding: 40px 20px;
  color: #666;
}

.unsupported-icon {
  font-size: 48px;
  margin-bottom: 16px;
  display: block;
}

.unsupported-title {
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 8px;
  display: block;
  color: #333;
}

.unsupported-desc {
  font-size: 14px;
  margin-bottom: 24px;
  display: block;
}

.unsupported-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  flex-wrap: wrap;
}

.preview-download-btn,
.preview-open-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  min-width: 80px;
}

.preview-download-btn {
  background: #007AFF;
  color: white;
}

.preview-download-btn:hover {
  background: #0056b3;
}

.preview-open-btn {
  background: #6c757d;
  color: white;
}

.preview-open-btn:hover {
  background: #545b62;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .preview-modal {
    width: 95vw;
    height: 90vh;
  }
  
  .preview-modal-header {
    padding: 12px 16px;
  }
  
  .preview-title {
    font-size: 14px;
  }
  
  .preview-text {
    padding: 16px;
    font-size: 12px;
  }
  
  .unsupported-actions {
    flex-direction: column;
    align-items: center;
  }
  
  .preview-download-btn,
  .preview-open-btn {
    width: 200px;
  }
}
</style>