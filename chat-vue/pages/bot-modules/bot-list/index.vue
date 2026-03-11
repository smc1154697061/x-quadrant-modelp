<template>
  <app-layout>
    <view class="knowledge-container">
      <!-- 知识库管理区域的样式应用到机器人列表 -->
      <view class="kb-section">
        <view class="section-header">
          <view class="section-title">渡渡鸟对话机器人</view>
          <button class="create-kb-btn" @tap="createNewBot">创建对话机器人</button>
      </view>
      
        <view v-if="loading" class="loading">
          <text>加载中...</text>
      </view>
      
        <view v-else-if="bots.length === 0" class="empty-state">
          <text>暂无对话机器人</text>
      </view>
      
        <!-- 使用与知识库相同的网格布局 -->
        <view v-else class="kb-grid">
        <view 
            v-for="bot in bots" 
          :key="bot.id"
            class="kb-card" 
            hover-class="kb-card-hover"
        >
            <view class="kb-card-content">
              <view class="kb-card-header">
                <text class="kb-name">{{ bot.name }}</text>
            <view class="bot-tags">
              <text v-if="bot.is_public" class="tag public-tag">公开</text>
              <text v-else class="tag private-tag">私有</text>
                  <text class="tag model-tag">{{ bot.model_name || 'qwen2:7b' }}</text>
            </view>
          </view>
              <text class="kb-description">{{ bot.description || '无描述' }}</text>
            
              <!-- 关联知识库标签 -->
              <view v-if="bot.kb_names && bot.kb_names.length > 0" class="kb-tags-container">
                <text class="kb-tags-title">关联知识库:</text>
              <view class="kb-tags">
                <text v-for="(kbName, i) in bot.kb_names" :key="i" class="kb-tag">{{ kbName }}</text>
              </view>
            </view>
          </view>
          
            <view class="kb-card-footer">
              <button class="action-btn chat-btn" @tap.stop="startChat(bot.id)">开始对话</button>
              <button class="action-btn rename-btn" @tap.stop="editBot(bot)">编辑</button>
              <button class="action-btn delete-btn" @tap.stop="confirmDelete(bot.id)">删除</button>
            </view>
          </view>
        </view>
      </view>
      
      <!-- 创建/编辑机器人弹窗 -->
      <view v-if="showBotDialog" class="dialog">
        <view class="dialog-content" @tap.stop>
            <text class="dialog-title">{{ isEditing ? '编辑对话机器人' : '创建新对话机器人' }}</text>
          
            <view class="form-item">
            <text class="form-label">机器人名称</text>
            <view class="input-wrapper">
              <input 
                type="text" 
                v-model="botForm.name" 
                placeholder="输入机器人名称" 
                maxlength="140"
                class="basic-input"
              />
            </view>
            </view>
            
            <view class="form-item">
            <text class="form-label">机器人描述</text>
            <view class="input-wrapper">
              <textarea
                v-model="botForm.description"
                placeholder="输入机器人描述(选填)" 
                class="basic-textarea"
              ></textarea>
            </view>
            </view>
            
            <view class="form-item">
              <text class="form-label">系统提示词</text>
            <view class="input-wrapper">
              <textarea
                v-model="botForm.system_prompt"
                placeholder="系统提示词暂不支持自定义" 
                class="basic-textarea"
                disabled
              ></textarea>
            </view>
            <text class="form-tip">系统提示词暂不支持自定义</text>
            </view>
            
            <view class="form-item">
            <text class="form-label">模型名称</text>
              <view class="fixed-model-wrapper">
                <text class="fixed-model-name">qwen2:7b</text>
              </view>
            </view>
          
            <view class="form-item">
            <text class="form-label">选择知识库（单选）</text>
              <view class="kb-selector">
                <view v-if="loadingKnowledgeBases" class="loading-kb">
                  <text>加载知识库中...</text>
                </view>
                
                <view v-else-if="knowledgeBases.length === 0" class="empty-kb">
                  <text>暂无可用知识库</text>
                  <navigator url="/pages/knowledge-base/index" class="kb-action">去创建知识库</navigator>
                </view>
                
                <view v-else class="kb-options">
                  <view 
                    v-for="(kb, index) in knowledgeBases" 
                    :key="kb.id"
                    class="kb-option"
                  :class="{ 'selected': botForm.kb_ids[0] === kb.id }"
                  @tap="selectKnowledgeBase(kb.id, kb.name)"
                  >
                  <view class="kb-radio">
                    <view class="radio-inner" v-if="botForm.kb_ids[0] === kb.id"></view>
                    </view>
                    <view class="kb-option-content">
                      <view class="kb-header">
                        <text class="kb-name">{{ kb.name }}</text>
                        <text class="kb-count">{{ kb.documents?.length || 0 }}个文档</text>
                      </view>
                      <text class="kb-desc">{{ kb.description || '无描述' }}</text>
                    </view>
                  </view>
                </view>
              </view>
              
              <!-- 已选知识库标签 -->
              <view class="selected-kb-info" v-if="botForm.kb_names.length > 0">
              <text class="selected-kb-text">已选择知识库: {{ botForm.kb_names[0] }}</text>
              </view>
            </view>
            
            <view class="form-item">
              <label class="checkbox-label">
                <switch 
                  :checked="botForm.is_public" 
                  @change="(e) => botForm.is_public = e.detail.value" 
                  color="var(--primary-color)" 
                />
                <text>设为公开（所有用户可见）</text>
              </label>
            </view>
          
          <view class="dialog-buttons">
            <button class="cancel-btn" @tap="cancelBotDialog">取消</button>
            <button class="confirm-btn" @tap="saveBotDialog" :disabled="!botForm.name || creating">
              <text v-if="creating">保存中...</text>
              <text v-else>保存</text>
            </button>
          </view>
        </view>
      </view>
    </view>
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
        model_name: 'qwen2:7b',
        kb_ids: [],
        kb_names: [],
        is_public: false
      },
      loadingKnowledgeBases: false,
      knowledgeBases: [],
      botId: null,
      loginVisible: false,
      creating: false,
      refreshInterval: null
    };
  },
  computed: {
    isLoggedIn() {
      return !!this.userInfo && !!this.userInfo.id;
    }
  },
  created() {
    this.checkLoginStatus();
    
    // 监听用户信息更新事件
    uni.$on('userInfoUpdated', this.handleUserInfoUpdated);
  },
  mounted() {
    this.fetchBots();
  },
  beforeDestroy() {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
    }
    
    // 移除事件监听
    uni.$off('userInfoUpdated', this.handleUserInfoUpdated);
  },
  methods: {
    // 处理用户信息更新事件
    handleUserInfoUpdated(userInfo) {
      this.userInfo = userInfo;
      
      // 检查是否正在退出应用
      const isExitingApp = uni.getStorageSync('isExitingApp');
      if (isExitingApp === 'true') {
        return;
      }
      
      // 只有在用户登录时才重新加载机器人列表
      if (userInfo) {
        this.fetchBots();
      }
    },
    
    // 检查登录状态
    checkLoginStatus() {
      const token = uni.getStorageSync('token');
      const userInfoStr = uni.getStorageSync('userInfo');
      
      if (!token || !userInfoStr) {
        uni.reLaunch({
          url: '/pages/user/login/index'
        });
        return;
      }
      
      try {
        const userInfo = typeof userInfoStr === 'string' ? JSON.parse(userInfoStr) : userInfoStr;
        this.userInfo = userInfo;
      } catch (e) {
        console.error('解析用户信息失败:', e);
        this.userInfo = null;
        
        // 解析失败也跳转到登录页
        uni.reLaunch({
          url: '/pages/user/login/index'
        });
      }
    },
    
    // 获取机器人列表
    async fetchBots() {
      try {
        this.loading = true;
        const response = await api.get('/llm/bots');
        
        if (response && (response.code === '0000' || response.code === 'SUCCESS')) {
          // 处理响应数据
          this.bots = response.data.bots || [];
        } else if (response && response.code === 'UNAUTHORIZED') {
          this.bots = [];
          // 清除登录状态
          uni.removeStorageSync('userInfo');
          uni.removeStorageSync('token');
          
          // 显示提示
          uni.showToast({
            title: '登录已过期，请重新登录',
            icon: 'none',
            duration: 2000
          });
          
          // 跳转到登录页
          setTimeout(() => {
            uni.reLaunch({ 
              url: '/pages/user/login/index' 
            });
          }, 1500);
        } else {
          // 其他错误情况
          this.bots = [];
          
          // 显示错误信息
          uni.showToast({
            title: response?.message || '获取机器人列表失败',
            icon: 'none',
            duration: 2000
          });
        }
      } catch (error) {
        console.error('获取机器人列表失败:', error);
        this.bots = [];
        
        // 检查是否是网络错误
        const isNetworkError = error.code === 'NETWORK_ERROR' || 
          (error.errMsg && (
            error.errMsg.includes('request:fail') || 
            error.errMsg.includes('timeout') || 
            error.errMsg.includes('connection refused')
          ));
        
        if (isNetworkError) {
          // 网络错误，显示友好提示
          uni.showToast({
            title: '网络连接失败，请检查网络或服务器状态',
            icon: 'none',
            duration: 3000
          });
        } else if (error.message && error.message.includes('未授权')) {
          // 未授权错误，清除登录状态并跳转到登录页
          uni.removeStorageSync('userInfo');
          uni.removeStorageSync('token');
          
          // 跳转到登录页
          setTimeout(() => {
            uni.reLaunch({ url: '/pages/user/login/index' });
          }, 100);
        } else {
          // 其他错误
          uni.showToast({
            title: '获取机器人列表失败',
            icon: 'none',
            duration: 2000
          });
        }
      } finally {
        this.loading = false;
      }
    },
    
    // 获取知识库列表
    async fetchKnowledgeBases() {
      this.loadingKnowledgeBases = true;
      
      try {
        const result = await api.get('/llm/knowledge-bases');
        
        if (result && (result.code === '0000' || result.code === 'SUCCESS')) {
          // 获取 knowledge_bases 数组并统一 ID 类型为数字
          const kbs = result.data?.knowledge_bases || result.data || [];
          this.knowledgeBases = kbs.map(kb => ({
            ...kb,
            id: Number(kb.id)  // 统一转换为数字类型
          }));
          
        } else {
          console.error('获取知识库列表失败:', result?.message || '未知错误');
          this.knowledgeBases = [];
        }
      } catch (error) {
        console.error('获取知识库列表失败:', error);
        uni.showToast({
          title: '获取知识库列表失败',
          icon: 'none'
        });
        this.knowledgeBases = [];
      } finally {
        this.loadingKnowledgeBases = false;
      }
    },
    
    // 创建新机器人
    createNewBot() {
      this.isEditing = false;
      this.selectedBotId = null;
      this.botForm = {
        name: '',
        description: '',
        system_prompt: '',
        model_name: 'qwen2:7b',
        is_public: false,
        kb_ids: [],
        kb_names: []
      };
      
      // 获取知识库列表
      this.fetchKnowledgeBases();
      
      this.showBotDialog = true;
    },
    
    // 编辑机器人
    async editBot(bot) {
      this.isEditing = true;
      this.selectedBotId = bot.id;
      
      try {
        // 从后端重新获取机器人详情，确保数据最新
        const response = await api.get(`/llm/bots/${bot.id}`);
        
        if (response && response.code === 'SUCCESS' && response.data) {
          const botInfo = response.data;
          
          // 设置表单数据，统一 kb_ids 为数字数组
          this.botForm = {
            name: botInfo.name,
            description: botInfo.description || '',
            system_prompt: botInfo.system_prompt || '',
            model_name: botInfo.model_name || 'qwen2:7b',
            is_public: botInfo.is_public || false,
            kb_ids: (botInfo.kb_ids || []).map(id => Number(id)),  // 统一转换为数字
            kb_names: botInfo.kb_names || []
          };
          
        } else {
          // 如果获取失败，使用列表中的数据
          this.botForm = {
            name: bot.name,
            description: bot.description || '',
            system_prompt: bot.system_prompt || '',
            model_name: bot.model_name || 'qwen2:7b',
            is_public: bot.is_public || false,
            kb_ids: (bot.kb_ids || []).map(id => Number(id)),
            kb_names: bot.kb_names || []
          };
        }
      } catch (error) {
        console.error('获取机器人详情失败:', error);
        // 使用列表中的数据作为后备
        this.botForm = {
          name: bot.name,
          description: bot.description || '',
          system_prompt: bot.system_prompt || '',
          model_name: bot.model_name || 'qwen2:7b',
          is_public: bot.is_public || false,
          kb_ids: (bot.kb_ids || []).map(id => Number(id)),
          kb_names: bot.kb_names || []
        };
      }
      
      // 获取知识库列表
      await this.fetchKnowledgeBases();
      
      this.showBotDialog = true;
    },
    
    // 取消对话框
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
      
      this.creating = true;
      
      try {
        const botData = {
          name: this.botForm.name,
          description: this.botForm.description,
          system_prompt: this.botForm.system_prompt,
          model_name: 'qwen2:7b',  // 使用固定的模型名称
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
      } finally {
        this.creating = false;
      }
    },
    
    // 开始对话 - 修改为直接跳转到聊天页面，不创建对话
    startChat(botId) {
      // 显示加载提示
      uni.showLoading({
        title: '加载中...'
      });
      
      // 直接跳转到聊天页面，只带上botId参数
      uni.navigateTo({
        url: `/pages/chat-modules/chat/index?botId=${botId}`,
        success: () => {
          uni.hideLoading();
        },
        fail: (error) => {
          console.error('跳转失败:', error);
          uni.hideLoading();
          uni.showToast({
            title: '页面跳转失败',
            icon: 'none'
          });
        }
      });
    },
    
    // 确认删除
    confirmDelete(botId) {
      uni.showModal({
        title: '确认删除',
        content: '删除后将无法恢复，确定要删除这个机器人吗？',
        success: async (res) => {
          if (res.confirm) {
            await this.deleteBot(botId);
          }
        }
      });
    },
    
    // 删除机器人
    async deleteBot(botId) {
      try {
        const response = await api.delete(`/llm/bots/${botId}`);
        
        if (response && (response.code === 'SUCCESS' || response.code === '0000')) {
          uni.showToast({
            title: '删除成功',
            icon: 'success'
          });
          
          this.fetchBots();  // 刷新列表
        } else {
          uni.showToast({
            title: response?.message || '删除失败',
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
    
    // 选择知识库（单选）
    selectKnowledgeBase(kbId, kbName) {
      // 清空之前的选择
      this.botForm.kb_ids = [kbId];
      this.botForm.kb_names = [kbName];
    },
    
    // 查看机器人的对话列表
    viewChats(botId) {
      uni.navigateTo({
        url: `/pages/chat-modules/chat-list/index?botId=${botId}`
      });
    }
  }
}
</script>

<style>
/* 导入知识库页面的样式 */
.knowledge-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-title {
  font-size: 24px;
  font-weight: 600;
  color: #333;
}

.create-kb-btn {
  background-color: var(--primary-color, #007AFF);
  color: white;
  padding: 8px 15px;
  border-radius: 6px;
  font-size: 14px;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
  height: 36px;
}

/* 知识库卡片网格布局 */
.kb-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

/* 知识库卡片样式 */
.kb-card {
  background-color: white;
  border-radius: 10px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  transition: transform 0.2s, box-shadow 0.2s;
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 150px;
}

.kb-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.15);
}

.kb-card-content {
  padding: 15px;
  flex-grow: 1;
  display: flex;
  flex-direction: column;
}

.kb-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;
}

.kb-name {
  font-size: 18px;
  font-weight: 600;
  color: #333;
  word-break: break-word;
}

.bot-tags {
  display: flex;
  flex-wrap: wrap;
}

.tag {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 10px;
  margin-left: 5px;
}

.public-tag {
  background-color: #e6f7ff;
  color: #1890ff;
}

.private-tag {
  background-color: #f9f0ff;
  color: #722ed1;
}

.model-tag {
  background-color: #f0f0f0;
  color: #666;
}

.kb-description {
  font-size: 14px;
  color: #666;
  flex-grow: 1;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.kb-tags-container {
  margin-top: 10px;
}

.kb-tags-title {
  font-size: 12px;
  color: #666;
  margin-bottom: 5px;
}

.kb-tags {
  display: flex;
  flex-wrap: wrap;
}

.kb-tag {
  font-size: 12px;
  background-color: #f5f5f5;
  color: #666;
  padding: 2px 8px;
  border-radius: 4px;
  margin-right: 5px;
  margin-bottom: 5px;
}

.kb-card-footer {
  display: flex;
  justify-content: flex-end;
  padding: 10px 15px;
  background-color: #f8f9fa;
  border-top: 1px solid #eee;
  align-items: center;
}

/* 按钮样式 */
.action-btn {
  font-size: 12px;
  padding: 5px 10px;
  margin-left: 10px;
  border-radius: 4px;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 28px;
  line-height: 1;
}

.chat-btn {
  background-color: var(--primary-color, #007AFF);
  color: white;
}

.rename-btn {
  background-color: #f0f0f0;
  color: #333;
}

.delete-btn {
  background-color: rgba(255, 59, 48, 0.1);
  color: #ff3b30;
}

/* 空状态和加载状态 */
.empty-state, .loading {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 40px 0;
  background-color: white;
  border-radius: 10px;
  margin-bottom: 20px;
  text-align: center;
  color: #999;
  font-size: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

/* 对话框样式 */
.dialog {
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
  border-radius: 10px;
  padding: 20px;
  width: 90%;
  max-width: 500px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

.dialog-title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
  margin-bottom: 20px;
  text-align: center;
}

.form-item {
  margin-bottom: 15px;
}

.form-label {
  display: block;
  font-size: 14px;
  color: #333;
  margin-bottom: 5px;
}

.input-wrapper {
  border: 1px solid #ddd;
  border-radius: 6px;
  background-color: #f8f9fa;
  padding: 5px;
}

.basic-input, .basic-textarea {
  width: 100%;
  font-size: 14px;
  color: #333;
  background-color: transparent;
  border: none;
  outline: none;
  padding: 5px;
}

.basic-textarea {
  height: 80px;
}

.form-picker {
  border: 1px solid #ddd;
  border-radius: 6px;
  background-color: #f8f9fa;
  padding: 10px;
}

.picker-view {
  font-size: 14px;
  color: #333;
}

.dialog-buttons {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

.cancel-btn, .confirm-btn {
  padding: 8px 20px;
  border-radius: 6px;
  font-size: 14px;
  margin-left: 10px;
  line-height: 1;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.cancel-btn {
  background-color: #f0f0f0;
  color: #333;
}

.confirm-btn {
  background-color: var(--primary-color, #007AFF);
  color: white;
}

.confirm-btn[disabled] {
  background-color: #cccccc;
  color: #666;
}

/* 知识库选择器样式 */
.kb-selector {
  border: 1px solid #ddd;
  border-radius: 6px;
  background-color: #f8f9fa;
  max-height: 200px;
  overflow-y: auto;
}

.kb-options {
  display: flex;
  flex-direction: column;
}

.kb-option {
  display: flex;
  padding: 10px;
  border-bottom: 1px solid #eee;
  cursor: pointer;
}

.kb-option:last-child {
  border-bottom: none;
}

.kb-option.selected {
  background-color: rgba(0, 122, 255, 0.1);
}

.kb-radio {
  width: 18px;
  height: 18px;
  border: 1px solid #ddd;
  border-radius: 50%;
  margin-right: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.radio-inner {
  width: 10px;
  height: 10px;
  background-color: var(--primary-color, #007AFF);
  border-radius: 50%;
}

.kb-option-content {
  flex: 1;
}

.kb-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 5px;
}

.kb-count {
  font-size: 12px;
  color: #999;
}

.kb-desc {
  font-size: 12px;
  color: #666;
}

.selected-kb-info {
  margin-top: 10px;
  font-size: 12px;
  color: #666;
}

.loading-kb, .empty-kb {
  padding: 15px;
  text-align: center;
  color: #999;
  font-size: 14px;
}

.kb-action {
  color: var(--primary-color, #007AFF);
  margin-left: 5px;
}

.checkbox-label {
  display: flex;
  align-items: center;
}

.form-tip {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.basic-textarea:disabled {
  background-color: #f0f0f0;
  color: #999;
}

/* 固定模型名称样式 */
.fixed-model-wrapper {
  background-color: #f5f5f5;
  padding: 10rpx;
  border-radius: 5rpx;
  width: 100%;
  box-sizing: border-box;
}

.fixed-model-name {
  font-size: 24rpx;
  color: #666;
  display: inline-block;
}
</style> 