<template>
  <app-layout>
    <view class="knowledge-container">
      <!-- 知识库管理区域 -->
      <view class="kb-section">
        <view class="section-header">
          <view class="section-title">渡渡鸟知识库</view>
          <button class="create-kb-btn" @tap="showCreateKBDialog">创建资料库</button>
        </view>
        
        <view v-if="loadingKBs" class="loading">
          <text>加载中...</text>
        </view>
        
        <view v-else-if="knowledgeBases.length === 0" class="empty-state">
          <text>暂无知识资料库</text>
        </view>
        
        <view v-else class="kb-grid">
          <view v-for="kb in knowledgeBases" :key="kb.id" class="kb-card" @tap="navigateToDetail(kb.id)">
            <view class="kb-card-content">
              <view class="kb-card-header">
                <text class="kb-name">{{ kb.name }}</text>
                <text class="kb-doc-count">{{ kb.doc_count || 0 }}个文档</text>
              </view>
              <text class="kb-description">{{ kb.description || '无描述' }}</text>
            </view>
            
            <view class="kb-card-footer">
              <button class="action-btn rename-btn" @tap.stop="showRenameKBDialog(kb)">重命名</button>
              <button class="action-btn delete-btn" @tap.stop="confirmDeleteKB(kb.id)">删除</button>
            </view>
          </view>
        </view>
      </view>
      
      <!-- 创建资料库弹窗 -->
      <view v-if="showCreateKB" class="dialog create-kb-dialog">
        <view class="dialog-content" @tap.stop>
          <text class="dialog-title">创建知识资料库</text>
          
          <view class="form-item">
            <text class="form-label">资料库名称</text>
            <view class="input-wrapper" :class="{ 'focus-within': isNameFocused }">
              <input 
                type="text" 
                v-model="newKB.name"
                placeholder="输入资料库名称" 
                maxlength="140"
                class="basic-input"
                @focus="focusNameInput"
                @blur="isNameFocused = false"
              />
            </view>
          </view>
          
          <view class="form-item">
            <text class="form-label">资料库描述</text>
            <view class="input-wrapper" :class="{ 'focus-within': isDescFocused }">
              <textarea
                v-model="newKB.description"
                placeholder="输入知识库描述(选填)" 
                class="basic-textarea"
                @focus="focusDescInput"
                @blur="isDescFocused = false"
              ></textarea>
            </view>
          </view>
          
          <!-- 分块配置区域 -->
          <view class="form-section">
            <text class="section-label">分块配置</text>
            
            <view class="form-item">
              <text class="form-label">分块策略</text>
              <view class="strategy-selector">
                <view 
                  v-for="strategy in chunkingStrategies" 
                  :key="strategy.value"
                  class="strategy-option"
                  :class="{ 'active': newKB.chunking_strategy === strategy.value }"
                  @tap="selectStrategy(strategy.value)"
                >
                  <text class="strategy-name">{{ strategy.label }}</text>
                  <text class="strategy-desc">{{ strategy.description }}</text>
                </view>
              </view>
            </view>
            
            <view class="form-row">
              <view class="form-item half">
                <text class="form-label">分块大小</text>
                <view class="input-wrapper">
                  <input 
                    type="number" 
                    v-model.number="newKB.chunk_size"
                    placeholder="1000" 
                    class="basic-input"
                  />
                </view>
                <text class="form-hint">字符数 (100-8000)</text>
              </view>
              
              <view class="form-item half">
                <text class="form-label">重叠大小</text>
                <view class="input-wrapper">
                  <input 
                    type="number" 
                    v-model.number="newKB.chunk_overlap"
                    placeholder="200" 
                    class="basic-input"
                  />
                </view>
                <text class="form-hint">字符数</text>
              </view>
            </view>
          </view>
          
          <view class="dialog-buttons">
            <button class="cancel-btn" @tap="cancelCreateKB" :disabled="creating">取消</button>
            <button class="confirm-btn" @tap="confirmCreateKB" :disabled="!newKB.name || creating">
              <text v-if="creating">创建中...</text>
              <text v-else>创建</text>
            </button>
          </view>
        </view>
      </view>
      
      <!-- 重命名/编辑资料库弹窗 -->
      <view v-if="showRenameKB" class="dialog rename-kb-dialog">
        <view class="dialog-content" @tap.stop>
          <text class="dialog-title">编辑知识资料库</text>
          
          <view class="form-item">
            <text class="form-label">资料库名称</text>
            <view class="input-wrapper" :class="{ 'focus-within': isRenameNameFocused }">
              <input 
                type="text" 
                v-model="newKBName"
                placeholder="输入新的资料库名称" 
                maxlength="140"
                class="basic-input"
                @focus="focusRenameNameInput"
                @blur="isRenameNameFocused = false"
              />
            </view>
          </view>
          
          <view class="form-item">
            <text class="form-label">资料库描述</text>
            <view class="input-wrapper" :class="{ 'focus-within': isRenameDescFocused }">
              <textarea
                v-model="newKBDesc"
                placeholder="输入知识库描述(选填)" 
                class="basic-textarea"
                @focus="focusRenameDescInput"
                @blur="isRenameDescFocused = false"
              ></textarea>
            </view>
          </view>
          
          <!-- 分块配置区域 -->
          <view class="form-section">
            <text class="section-label">分块配置</text>
            
            <view class="form-item">
              <text class="form-label">分块策略</text>
              <view class="strategy-selector">
                <view 
                  v-for="strategy in chunkingStrategies" 
                  :key="strategy.value"
                  class="strategy-option"
                  :class="{ 'active': editKB.chunking_strategy === strategy.value }"
                  @tap="selectEditStrategy(strategy.value)"
                >
                  <text class="strategy-name">{{ strategy.label }}</text>
                  <text class="strategy-desc">{{ strategy.description }}</text>
                </view>
              </view>
            </view>
            
            <view class="form-row">
              <view class="form-item half">
                <text class="form-label">分块大小</text>
                <view class="input-wrapper">
                  <input 
                    type="number" 
                    v-model.number="editKB.chunk_size"
                    placeholder="1000" 
                    class="basic-input"
                  />
                </view>
                <text class="form-hint">字符数 (100-8000)</text>
              </view>
              
              <view class="form-item half">
                <text class="form-label">重叠大小</text>
                <view class="input-wrapper">
                  <input 
                    type="number" 
                    v-model.number="editKB.chunk_overlap"
                    placeholder="200" 
                    class="basic-input"
                  />
                </view>
                <text class="form-hint">字符数</text>
              </view>
            </view>
          </view>
          
          <view class="dialog-buttons">
            <button class="cancel-btn" @tap="cancelRenameKB">取消</button>
            <button class="confirm-btn" @tap="confirmRenameKB" :disabled="!newKBName">保存</button>
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
import api from '../../utils/api.js';
import AppLayout from '../../components/layout/AppLayout.vue';
import LoginDialog from '../../components/user/LoginDialog.vue';
import { getCurrentUser } from '../../utils/auth.js';
import auth from '../../utils/auth.js';

export default {
  components: {
    AppLayout,
    LoginDialog
  },
  data() {
    return {
      // 知识库相关
      knowledgeBases: [],
      loadingKBs: false,
      
      // 分块策略列表
      chunkingStrategies: [],
      defaultChunkingConfig: {
        chunking_strategy: 'fixed',
        chunk_size: 1000,
        chunk_overlap: 200
      },
      
      // 创建知识库相关
      showCreateKB: false,
      creating: false,
      newKB: {
        name: '',
        description: '',
        chunking_strategy: 'fixed',
        chunk_size: 1000,
        chunk_overlap: 200
      },
      isNameFocused: false,
      isDescFocused: false,
      
      // 编辑知识库相关
      showRenameKB: false,
      renameKBId: null,
      newKBName: '',
      newKBDesc: '',
      editKB: {
        chunking_strategy: 'fixed',
        chunk_size: 1000,
        chunk_overlap: 200
      },
      isRenameNameFocused: false,
      isRenameDescFocused: false,
      
      // 登录相关
      loginVisible: false,
      userInfo: null,
      isLoggedIn: false,
    }
  },
  onLoad() {
    // 获取用户信息 - 只从本地存储获取一次
    this.userInfo = getCurrentUser();
    this.isLoggedIn = !!this.userInfo;
    
    // 加载分块策略
    this.fetchChunkingStrategies();
    
    // 加载知识库列表
    this.fetchKnowledgeBases();
    
    // 检测设备类型
    this.checkDeviceType();
    
    // 监听用户信息更新事件
    uni.$on('userInfoUpdated', this.handleUserInfoUpdated);
  },
  onUnload() {
    // 移除事件监听
    uni.$off('userInfoUpdated', this.handleUserInfoUpdated);
  },
  methods: {
    // 检测设备类型
    checkDeviceType() {
      uni.getSystemInfo({
        success: (res) => {
          this.isPc = res.windowWidth >= 768;
        }
      });
    },
    
    // 处理用户信息更新事件
    handleUserInfoUpdated(userInfo) {
      this.userInfo = userInfo;
      this.isLoggedIn = !!userInfo;
      
      // 检查是否正在退出应用
      const isExitingApp = uni.getStorageSync('isExitingApp');
      if (isExitingApp === 'true') {
        return;
      }
      
      // 只有在用户登录时才重新加载知识库列表
      if (this.isLoggedIn) {
        this.fetchKnowledgeBases();
      }
    },

    // 获取知识库列表
    async fetchKnowledgeBases() {
      this.loadingKBs = true;
      
      try {
        // 不需要再次验证token，直接使用本地存储的用户信息
        const result = await api.get('/llm/knowledge-bases/basic', {}, this.isLoggedIn);
        
        if (result && (result.code === '0000' || result.code === 'SUCCESS')) {
          this.knowledgeBases = result.data || [];
        } else if (result && result.code === 'UNAUTHORIZED') {
          this.knowledgeBases = [];
          // 清除登录状态
          uni.removeStorageSync('userInfo');
          uni.removeStorageSync('token');
          this.isLoggedIn = false;
          
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
          return; // 提前返回，不执行后续代码
        } else {
          // 其他错误情况
          this.knowledgeBases = [];
          
          // 显示错误信息
          uni.showToast({
            title: result?.message || '获取知识库列表失败',
            icon: 'none',
            duration: 2000
          });
        }
      } catch (error) {
        console.error('获取知识库列表失败:', error);
        this.knowledgeBases = [];
        
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
          this.isLoggedIn = false;
          
          // 跳转到登录页
          setTimeout(() => {
            uni.reLaunch({ url: '/pages/user/login/index' });
          }, 100);
        } else {
          // 其他错误
          uni.showToast({
            title: '获取知识库列表失败',
            icon: 'none',
            duration: 2000
          });
        }
      } finally {
        this.loadingKBs = false;
      }
    },
    
    // 导航到知识库详情页
    navigateToDetail(kbId) {
      // 找到对应的知识库
      const kb = this.knowledgeBases.find(item => item.id === kbId);
      if (!kb) {
        uni.showToast({
          title: '知识库不存在',
          icon: 'none'
        });
        return;
      }
      
      // 传递知识库信息到详情页
      uni.navigateTo({
        url: `/pages/knowledge-base/detail?id=${kbId}&name=${encodeURIComponent(kb.name)}&description=${encodeURIComponent(kb.description || '')}`
      });
    },
    
    // 获取分块策略列表
    async fetchChunkingStrategies() {
      try {
        const result = await api.get('/llm/chunking-strategies');
        if (result && (result.code === '0000' || result.code === 'SUCCESS')) {
          this.chunkingStrategies = result.data.strategies || [];
          this.defaultChunkingConfig = result.data.defaults || {
            chunking_strategy: 'fixed',
            chunk_size: 1000,
            chunk_overlap: 200
          };
        }
      } catch (error) {
        console.error('获取分块策略失败:', error);
        // 使用默认策略
        this.chunkingStrategies = [
          { value: 'fixed', label: '固定长度', description: '按固定字符长度分割，适合大多数场景' },
          { value: 'sentence', label: '句子边界', description: '优先按句子边界分割，保持语义完整性' },
          { value: 'semantic', label: '语义分块', description: '基于段落和语义边界分割，适合长文档' }
        ];
      }
    },

    // 选择分块策略（创建）
    selectStrategy(strategy) {
      this.newKB.chunking_strategy = strategy;
    },

    // 选择分块策略（编辑）
    selectEditStrategy(strategy) {
      this.editKB.chunking_strategy = strategy;
    },

    // 显示创建资料库弹窗
    showCreateKBDialog() {
      // 检查用户是否已登录
      if (!this.isLoggedIn) {
        uni.showModal({
          title: '提示',
          content: '创建知识资料库需要先登录，是否前往登录？',
          success: (res) => {
            if (res.confirm) {
              this.loginVisible = true;
            }
          }
        });
        return;
      }

      this.newKB = {
        name: '',
        description: '',
        chunking_strategy: this.defaultChunkingConfig.chunking_strategy,
        chunk_size: this.defaultChunkingConfig.chunk_size,
        chunk_overlap: this.defaultChunkingConfig.chunk_overlap
      };
      this.showCreateKB = true;
    },
    
    // 取消创建知识库
    cancelCreateKB() {
      this.showCreateKB = false;
    },
    
    // 确认创建知识库
    async confirmCreateKB() {
      if (!this.newKB.name.trim()) {
        api.showError('请输入知识库名称');
        return;
      }
      
      // 再次检查用户是否已登录
      if (!this.isLoggedIn) {
        this.showCreateKB = false;
        uni.showModal({
          title: '提示',
          content: '创建知识资料库需要先登录，是否前往登录？',
          success: (res) => {
            if (res.confirm) {
              this.loginVisible = true;
            }
          }
        });
        return;
      }
      
      this.creating = true; // 显示创建中状态
      
      try {
        // 构建请求数据
        const requestData = {
          name: this.newKB.name,
          description: this.newKB.description || '',
          chunking_strategy: this.newKB.chunking_strategy,
          chunk_size: parseInt(this.newKB.chunk_size) || 1000,
          chunk_overlap: parseInt(this.newKB.chunk_overlap) || 200
        };
        
        // 实际API调用
        const result = await api.post('/llm/knowledge-bases', requestData);
        
        // 检查响应状态
        if (result && result.code === 'UNAUTHORIZED') {
          // 用户未登录，显示登录弹窗
          this.showCreateKB = false;
          this.loginVisible = true;
          return;
        }
        
        if (result && (result.code === '0000')) {
          // 先关闭创建弹窗，避免后续操作失败导致弹窗无法关闭
          this.showCreateKB = false;
          
          // 显示成功提示
          api.showSuccess('知识库创建成功');
          
          // 刷新知识库列表
          this.fetchKnowledgeBases();
          
          // 如果返回了知识库ID，跳转到详情页
          if (result.data && result.data.id) {
            setTimeout(() => {
              this.navigateToDetail(result.data.id);
            }, 500);
          }
        } else {
          // 其他错误情况
          api.showError(result?.message || '创建知识库失败');
        }
      } catch (error) {
        console.error('创建知识库失败:', error);
        api.showError('创建知识库失败');
      } finally {
        this.creating = false; // 隐藏创建中状态
      }
    },
    
    // 显示重命名知识库弹窗
    showRenameKBDialog(kb) {
      // 检查用户是否已登录
      if (!this.isLoggedIn) {
        uni.showModal({
          title: '提示',
          content: '编辑知识库需要先登录，是否前往登录？',
          success: (res) => {
            if (res.confirm) {
              this.loginVisible = true;
            }
          }
        });
        return;
      }

      this.renameKBId = kb.id;
      this.newKBName = kb.name;
      this.newKBDesc = kb.description || '';
      // 加载分块配置
      this.editKB = {
        chunking_strategy: kb.chunking_strategy || 'fixed',
        chunk_size: kb.chunk_size || 1000,
        chunk_overlap: kb.chunk_overlap || 200
      };
      this.showRenameKB = true;
    },
    
    // 取消重命名知识库
    cancelRenameKB() {
      this.showRenameKB = false;
      this.renameKBId = null;
    },
    
    // 确认重命名知识库
    async confirmRenameKB() {
      if (!this.newKBName.trim()) {
        api.showError('请输入知识库名称');
        return;
      }
      
      // 再次检查用户是否已登录
      if (!this.isLoggedIn) {
        this.showRenameKB = false;
        uni.showModal({
          title: '提示',
          content: '编辑知识库需要先登录，是否前往登录？',
          success: (res) => {
            if (res.confirm) {
              this.loginVisible = true;
            }
          }
        });
        return;
      }
      
      try {
        // 实际API调用
        const result = await api.put(`/llm/knowledge-bases/${this.renameKBId}`, {
          name: this.newKBName,
          description: this.newKBDesc || '',
          chunking_strategy: this.editKB.chunking_strategy,
          chunk_size: parseInt(this.editKB.chunk_size) || 1000,
          chunk_overlap: parseInt(this.editKB.chunk_overlap) || 200
        });

        if (result && (result.code === '0000')) {
          api.showSuccess('知识库更新成功');

          // 刷新知识库列表
          this.fetchKnowledgeBases();
        } else {
          api.showError(result?.message || '更新知识库失败');
        }
      } catch (error) {
        console.error('更新知识库失败:', error);
        api.showError('更新知识库失败');
      }

      this.showRenameKB = false;
      this.renameKBId = null;
    },
    
    // 确认删除知识库
    confirmDeleteKB(kbId) {
      // 检查用户是否已登录
      if (!this.isLoggedIn) {
        uni.showModal({
          title: '提示',
          content: '删除知识库需要先登录，是否前往登录？',
          success: (res) => {
            if (res.confirm) {
              this.loginVisible = true;
            }
          }
        });
        return;
      }
      
      uni.showModal({
        title: '确认删除',
        content: '删除知识库将同时删除其中所有文档，此操作不可恢复！确定要删除吗？',
        success: async (res) => {
          if (res.confirm) {
            await this.deleteKnowledgeBase(kbId);
          }
        }
      });
    },
    
    // 删除知识库
    async deleteKnowledgeBase(kbId) {
      try {
        // 实际API调用
        const result = await api.delete(`/llm/knowledge-bases/${kbId}`);
        
        if (result && (result.code === '0000')) {
          api.showSuccess('知识库删除成功');
          
          // 刷新知识库列表
          this.fetchKnowledgeBases();
        } else {
          api.showError(result?.message || '删除知识库失败');
        }
      } catch (error) {
        console.error('删除知识库失败:', error);
        api.showError('删除知识库失败');
      }
    },
    
    // 登录成功后的处理
    onLoginSuccess(userInfo) {
      // 更新用户信息
      if (typeof userInfo === 'string') {
        try {
          this.userInfo = JSON.parse(userInfo);
        } catch (e) {
          console.error('解析用户信息失败:', e);
          this.userInfo = userInfo;
        }
      } else {
        this.userInfo = userInfo;
      }
      
      // 更新登录状态
      this.isLoggedIn = !!this.userInfo;
      
      // 登录成功后，加载知识库列表
      this.fetchKnowledgeBases();
    },

    // 登录弹窗可见性变化的处理
    onLoginVisibleChange(visible) {
      this.loginVisible = visible;
    },

    // 显示登录对话框
    showLoginDialog() {
      this.loginVisible = true;
    },

    // 添加新方法来处理输入框的聚焦
    focusNameInput(e) {
      this.isNameFocused = true;
      this.$nextTick(() => {
        const input = e.target;
        if (input) {
          input.focus();
        }
      });
    },
    
    focusDescInput(e) {
      this.isDescFocused = true;
      this.$nextTick(() => {
        const textarea = e.target;
        if (textarea) {
          textarea.focus();
        }
      });
    },
    
    focusRenameNameInput(e) {
      this.isRenameNameFocused = true;
      this.$nextTick(() => {
        const input = e.target;
        if (input) {
          input.focus();
        }
      });
    },
    
    focusRenameDescInput(e) {
      this.isRenameDescFocused = true;
      this.$nextTick(() => {
        const textarea = e.target;
        if (textarea) {
          textarea.focus();
        }
      });
    }
  }
}
</script>

<style>
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

.section-subtitle {
  font-size: 14px;
  color: #666;
  margin-top: 5px;
}

.create-kb-btn {
  background-color: var(--primary-color, #007AFF);
  color: white;
  padding: 8px 15px;
  border-radius: 6px;
  font-size: 14px;
  border: none;
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

.kb-doc-count {
  font-size: 12px;
  color: #666;
  background-color: #f0f0f0;
  padding: 2px 8px;
  border-radius: 10px;
  white-space: nowrap;
  margin-left: 10px;
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
}

.rename-btn {
  background-color: #f0f0f0;
  color: #333;
}

.delete-btn {
  background-color: rgba(255, 59, 48, 0.1);
  color: #ff3b30;
}

.login-btn {
  background-color: var(--primary-color, #007AFF);
  color: white;
  padding: 5px 15px;
  border-radius: 4px;
  font-size: 14px;
  margin-left: 10px;
}

/* 空状态和加载状态 */
.empty-state, .loading, .login-hint {
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

.login-hint {
  flex-direction: row;
  background-color: #f8f9fa;
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

/* 修改表单样式，避免与uni-app样式冲突 */
.form-input, .form-textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  background-color: #fff;
  color: #333;
  box-sizing: border-box;
  outline: none;
  -webkit-appearance: none;
  appearance: none;
}

.form-textarea {
  min-height: 100px;
  resize: vertical;
}

.form-input:focus, .form-textarea:focus {
  border-color: var(--primary-color, #007AFF);
  box-shadow: 0 0 0 2px rgba(0, 122, 255, 0.1);
}

.dialog-buttons {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
  gap: 10px;
}

.cancel-btn, .confirm-btn {
  padding: 8px 20px;
  border-radius: 6px;
  font-size: 14px;
  border: none;
  cursor: pointer;
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

/* 响应式设计 */
@media screen and (min-width: 768px) {
  .knowledge-container {
    padding: 30px;
  }
  
  .kb-grid {
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  }
}

@media screen and (min-width: 1200px) {
  .kb-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

@media screen and (max-width: 767px) {
  .section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .create-kb-btn {
    width: 100%;
  }
  
  .dialog-content {
    width: 95%;
    padding: 15px;
  }
}

/* 按钮样式修复 */
.create-kb-btn, .action-btn, .login-btn, .select-file-btn, .primary-btn, .cancel-btn, .confirm-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.rename-btn, .delete-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 32px;
}

/* 弹窗按钮修复 */
.dialog-buttons button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 36px;
}

/* uni-app输入框样式修复 */
.uni-input-wrapper, .uni-textarea-wrapper {
  width: 100%;
  position: relative;
}

.uni-input-wrapper .form-input, .uni-textarea-wrapper .form-textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  background-color: #f8f9fa;
  font-size: 14px;
  box-sizing: border-box;
}

.input-container {
  width: 100%;
  position: relative;
}

.native-input, .native-textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  background-color: #fff;
  color: #333;
  box-sizing: border-box;
  outline: none;
  -webkit-appearance: none;
  appearance: none;
}

.native-textarea {
  min-height: 100px;
  resize: vertical;
}

.native-input:focus, .native-textarea:focus {
  border-color: var(--primary-color, #007AFF);
  box-shadow: 0 0 0 2px rgba(0, 122, 255, 0.1);
}

/* 修复uni-app环境下的原生输入元素 */
page input, page textarea {
  width: 100%;
  box-sizing: border-box;
}

/* 确保输入元素在各种环境下显示正常 */
.input-container input, .input-container textarea {
  margin: 0;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  width: 100%;
  background-color: #fff;
  color: #333;
  font-size: 14px;
  outline: none;
  -webkit-appearance: none;
  appearance: none;
}

.input-wrapper {
  width: 100%;
  position: relative;
}

.basic-input, .basic-textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  background-color: #fff;
  color: #333;
  font-size: 14px;
  box-sizing: border-box;
  outline: none;
  -webkit-appearance: none;
  appearance: none;
  height: 40px;
  line-height: 20px;
}

.basic-textarea {
  min-height: 100px;
  height: auto;
  resize: vertical;
}

/* 确保在各种环境下输入框都能正常工作 */
page .basic-input, page .basic-textarea {
  width: 100%;
  box-sizing: border-box;
}

/* 移动端适配 */
@media screen and (max-width: 767px) {
  .basic-input, .basic-textarea {
    font-size: 16px; /* 移动端更大的字体，防止缩放 */
  }
}

/* 修复uni-easyinput组件样式 */
/deep/ .uni-easyinput__content {
  background-color: #fff !important;
  border: 1px solid #ddd !important;
  border-radius: 6px !important;
}

/deep/ .uni-easyinput__content-input {
  font-size: 14px !important;
  color: #333 !important;
}

/deep/ .uni-easyinput__content-textarea {
  min-height: 100px !important;
}

/* 确保基本输入元素在uni-app环境中正确显示 */
.dialog-content .input-wrapper input,
.dialog-content .input-wrapper textarea {
  border: 1px solid #ddd !important;
  background-color: #fff !important;
  color: #333 !important;
  font-size: 14px !important;
  padding: 10px !important;
  border-radius: 6px !important;
  width: 100% !important;
  box-sizing: border-box !important;
  outline: none !important;
  -webkit-appearance: none !important;
  appearance: none !important;
}

.input-wrapper.focus-within {
  outline: none;
}

.input-wrapper.focus-within input,
.input-wrapper.focus-within textarea {
  border-color: var(--primary-color, #007AFF) !important;
  box-shadow: 0 0 0 2px rgba(0, 122, 255, 0.1) !important;
}

/* 分块配置区域样式 */
.form-section {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #eee;
}

.section-label {
  display: block;
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-bottom: 15px;
}

.strategy-selector {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.strategy-option {
  padding: 12px 15px;
  border: 1px solid #ddd;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  background-color: #f8f9fa;
}

.strategy-option.active {
  border-color: var(--primary-color, #007AFF);
  background-color: rgba(0, 122, 255, 0.05);
}

.strategy-name {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.strategy-desc {
  display: block;
  font-size: 12px;
  color: #666;
}

.form-row {
  display: flex;
  gap: 15px;
  margin-top: 15px;
}

.form-item.half {
  flex: 1;
}

.form-hint {
  display: block;
  font-size: 12px;
  color: #999;
  margin-top: 5px;
}

/* 响应式调整 */
@media screen and (max-width: 767px) {
  .form-row {
    flex-direction: column;
    gap: 10px;
  }
}
</style> 