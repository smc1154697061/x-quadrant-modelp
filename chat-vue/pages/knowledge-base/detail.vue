<template>
  <app-layout>
    <view class="detail-container">
      <!-- 自定义返回按钮 -->
      <view class="custom-header">
        <view class="back-btn" @tap="goBack">
          <text class="back-icon">返回上级</text>
        </view>
      </view>

      <!-- 知识库信息和上传区域 -->
      <view class="kb-header">
        <view class="kb-header-top">
          <view class="kb-info">
            <view v-if="!knowledgeBase" class="loading-state">
              <text>加载中...</text>
            </view>
            <template v-else>
              <text class="kb-name">{{ knowledgeBase.name }}</text>
              <text class="kb-description">{{ knowledgeBase.description || '无描述' }}</text>
              
              <!-- 分块配置信息 -->
              <view class="chunk-config-info">
                <view class="chunk-config-title">分块配置</view>
                <view class="chunk-config-items">
                  <view class="chunk-config-item">
                    <text class="config-label">策略:</text>
                    <text class="config-value">{{ formatChunkingStrategy(knowledgeBase.chunking_strategy) }}</text>
                  </view>
                  <view class="chunk-config-item" v-if="knowledgeBase.chunking_strategy === 'fixed'">
                    <text class="config-label">大小:</text>
                    <text class="config-value">{{ knowledgeBase.chunk_size }}</text>
                  </view>
                  <view class="chunk-config-item" v-if="knowledgeBase.chunking_strategy === 'fixed'">
                    <text class="config-label">重叠:</text>
                    <text class="config-value">{{ knowledgeBase.chunk_overlap }}</text>
                  </view>
                </view>
              </view>
            </template>
          </view>
          
          <!-- 游客提示 -->
          <view v-if="!isLoggedIn" class="login-hint-inline">
            <text>登录后才能上传和管理文档</text>
            <button class="login-btn" @tap="showLoginDialog">登录</button>
          </view>
          
          <!-- 文件上传控件 -->
          <view v-if="isLoggedIn" class="file-upload-controls">
            <button class="select-file-btn" @tap="selectFile">选择文件</button>
            <button class="upload-btn" @tap="uploadFile" :disabled="loading || !file">上传文件</button>
          </view>
        </view>
        
        <!-- 已选文件信息 -->
        <view v-if="file" class="file-name-container">
          <text class="file-name">已选: {{ file.name }}</text>
          <text class="file-size">({{ formatFileSize(file.size) }})</text>
        </view>
      </view>
      
      <!-- 文件列表 -->
      <view class="file-list-section">
        <view class="section-title">文档列表</view>
        
        <view v-if="loading" class="loading">
          <text>加载中...</text>
        </view>

        <view v-else-if="documents.length === 0" class="empty-state">
          <text>还没有上传任何文档</text>
        </view>

        <view v-else class="table-container">
          <!-- 替换表格为flex布局 -->
          <view class="document-list">
            <!-- 表头 -->
            <view class="document-header">
              <view class="header-cell name-cell">文档名称</view>
              <view class="header-cell size-cell">大小</view>
              <view class="header-cell status-cell">状态</view>
              <view v-if="isLoggedIn" class="header-cell action-cell">操作</view>
            </view>
            
            <!-- 表格内容 -->
            <view 
              v-for="doc in documents" 
              :key="doc.id" 
              class="document-row"
            >
              <view class="doc-cell name-cell">
                <text class="doc-name">{{ doc.name }}</text>
              </view>
              <view class="doc-cell size-cell">
                {{ formatFileSize(doc.file_size) }}
              </view>
              <view class="doc-cell status-cell">
                <span :class="['status-badge', `status-${doc.status}`]">
                  {{ formatDocStatus(doc.status) }}
                </span>
              </view>
              <view v-if="isLoggedIn" class="doc-cell action-cell">
                <button 
                  v-if="doc.status === 'uploaded' || doc.status === 'failed'" 
                  @tap="processDocument(doc.id)" 
                  class="process-btn"
                  :disabled="processingDocIds.includes(doc.id)"
                >
                  {{ processingDocIds.includes(doc.id) ? '处理中...' : '向量化' }}
                </button>
                <button @tap="deleteFile(doc.id)" class="delete-btn">删除</button>
              </view>
            </view>
          </view>
        </view>
      </view>
      
      <!-- 重命名知识库弹窗 -->
      <view v-if="showRenameKB" class="dialog rename-kb-dialog">
        <view class="dialog-content">
          <text class="dialog-title">编辑知识库</text>
          
          <view class="form-item">
            <text class="form-label">知识库名称</text>
            <input 
              type="text" 
              v-model="newKBName" 
              placeholder="输入新的知识库名称" 
              class="form-input" 
            />
          </view>
          
          <view class="form-item">
            <text class="form-label">知识库描述</text>
            <textarea
              v-model="newKBDesc" 
              placeholder="输入知识库描述(选填)" 
              class="form-textarea"
            />
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
import { getCurrentUser } from '../../utils/auth.js';
import api from '../../utils/api.js';
import AppLayout from '../../components/layout/AppLayout.vue';
import LoginDialog from '../../components/user/LoginDialog.vue';
import { normalizeError } from '../../utils/platform-adapter.js';

export default {
  components: {
    AppLayout,
    LoginDialog
  },
  data() {
    return {
      kbId: null,
      knowledgeBase: null,
      
      // 文件上传相关
      loading: false,
      documents: [],
      file: null,
      processingDocIds: [], // 正在处理的文档ID列表
      
      // 重命名知识库相关
      showRenameKB: false,
      newKBName: '',
      newKBDesc: '',
      
      // 用户相关
      userInfo: null,
      loginVisible: false,
      
      isPc: false  // 是否PC端
    }
  },
  computed: {
    isLoggedIn() {
      // 确保用户信息存在且包含id
      return !!this.userInfo && !!this.userInfo.id;
    }
  },
  onLoad(options) {
    // 检查是否有知识库ID
    if (options && options.id && options.id !== 'null' && options.id !== 'undefined') {
      this.kbId = options.id;
      
      // 获取用户信息
      this.userInfo = getCurrentUser();
      
      // 获取知识库详情，它会同时处理文档列表的获取
      this.fetchKnowledgeBaseDetail();
      
      // 设置页面导航
      this.setupNavigation();
    } else {
      console.error('缺少有效的知识库ID，跳转到知识库列表页');
      
      uni.showToast({
        title: '缺少有效的知识库ID',
        icon: 'none'
      });
      
      // 跳转到知识库列表页
      setTimeout(() => {
        uni.switchTab({
          url: '/pages/knowledge-base/index'
        });
      }, 1500);
    }
    
    // 检测设备类型
    this.checkDeviceType();
    
    // 监听用户信息更新事件
    uni.$on('userInfoUpdated', this.handleUserInfoUpdated);
    
    // 监听显示登录弹窗事件
    uni.$on('showLoginDialog', () => {
      this.loginVisible = true;
    });
  },
  
  // 页面显示时检查返回按钮和用户状态
  onShow() {
    // 重新检查用户信息
    const currentUser = getCurrentUser();
    if (JSON.stringify(currentUser) !== JSON.stringify(this.userInfo)) {
      this.userInfo = currentUser;
      // 如果用户状态变化，重新加载数据
      this.fetchKnowledgeBaseDetail();
    }
    
    // 确保导航按钮正确显示
    this.setupNavigation();
  },
  
  onPullDownRefresh() {
    this.fetchKnowledgeBaseDetail();
    setTimeout(() => {
      uni.stopPullDownRefresh();
    }, 1000);
  },
  onUnload() {
    // 移除事件监听
    uni.$off('userInfoUpdated', this.handleUserInfoUpdated);
    uni.$off('showLoginDialog');
  },
  methods: {
    // 设置页面导航
    setupNavigation() {
      // 获取当前页面栈
      const pages = getCurrentPages();
      
      // 如果当前页面是唯一页面或是第一个页面，则需要手动添加返回按钮
      if (pages.length <= 1) {
        uni.setNavigationBarColor({
          frontColor: '#000000',
          backgroundColor: '#ffffff'
        });
        
        // 设置自定义导航按钮
        // #ifdef MP-WEIXIN
        wx.showNavigationBarLoading();
        wx.setNavigationBarTitle({
          title: this.knowledgeBase?.name || '知识库详情'
        });
        // 在微信小程序中设置返回首页按钮
        uni.setNavigationBarButton({
          button: [{
            type: 'back',
            text: '返回',
            color: '#000000'
          }],
          success: () => {
            console.log('设置返回按钮成功');
          },
          fail: (err) => {
            console.error('设置返回按钮失败:', err);
          }
        });
        // #endif
      }
    },
    
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
      
      // 只有在有有效的知识库ID时才重新加载知识库详情
      if (this.kbId && this.kbId !== 'null' && this.kbId !== 'undefined') {
        // 重新加载知识库详情和文件列表
        this.fetchKnowledgeBaseDetail();
      } else {
        // 如果没有有效的知识库ID，跳转到知识库列表页
        uni.switchTab({
          url: '/pages/knowledge-base/index'
        });
      }
    },
    
    // 获取知识库详情
    async fetchKnowledgeBaseDetail() {
      // 检查知识库ID是否有效
      if (!this.kbId || this.kbId === 'null' || this.kbId === 'undefined') {
        console.error('无效的知识库ID:', this.kbId);
        uni.showToast({
          title: '无效的知识库ID',
          icon: 'none'
        });
        
        // 跳转到知识库列表页
        setTimeout(() => {
          uni.switchTab({
            url: '/pages/knowledge-base/index'
          });
        }, 1500);
        return;
      }
      
      try {
        const result = await api.get(`/llm/knowledge-bases/${this.kbId}`);
        
        if (result && (result.code === '0000' || result.code === 'SUCCESS')) {
          this.knowledgeBase = result.data;
          
          // 如果知识库详情中包含文档列表，更新文档列表
          if (this.knowledgeBase && this.knowledgeBase.documents) {
            this.documents = this.knowledgeBase.documents;
            this.loading = false;
          } else {
            // 如果知识库详情中不包含文档列表，单独获取文档列表
            await this.fetchDocuments();
          }
        } else {
          console.error('获取知识库详情失败:', result?.message || '未知错误');
          uni.showToast({
            title: '获取知识库详情失败',
            icon: 'none'
          });
        }
      } catch (error) {
        console.error('获取知识库详情异常:', error);
        uni.showToast({
          title: '网络连接超时，请稍后重试',
          icon: 'none'
        });
      }
    },
    
    // 获取文件列表
    async fetchDocuments() {
      // 如果知识库详情已包含文档列表，直接使用
      if (this.knowledgeBase && this.knowledgeBase.documents) {
        this.documents = this.knowledgeBase.documents;
        this.loading = false;
        return Promise.resolve(this.documents);
      }
      
      // 否则再请求文件列表
      this.loading = true;
      return api.get(`/llm/knowledge-bases/${this.kbId}/files`)
        .then(result => {
          if (result && (result.code === '0000' || result.code === 'SUCCESS')) {
            this.documents = result.data || [];
          } else {
            this.documents = [];
          }
          this.loading = false;
          return this.documents;
        })
        .catch(error => {
          console.error('获取文件列表失败:', error);
          this.documents = [];
          this.loading = false;
          return [];
        });
    },
    
    // 选择文件
    selectFile() {
      // 检查用户是否已登录
      if (!this.isLoggedIn) {
        uni.showModal({
          title: '提示',
          content: '上传文件需要先登录，是否前往登录？',
          success: (res) => {
            if (res.confirm) {
              this.loginVisible = true;
            }
          }
        });
        return;
      }
      
      // #ifdef H5
      try {
        uni.chooseFile({
          count: 1,
          success: (res) => {
            if (res.tempFiles && res.tempFiles.length > 0) {
              this.file = res.tempFiles[0];
            }
          },
          fail: (err) => {
            console.error('选择文件失败:', err);
            uni.showToast({
              title: '选择文件失败',
              icon: 'none'
            });
          }
        });
      } catch (e) {
        console.error('H5环境调用chooseFile出错:', e);
        uni.showToast({
          title: '选择文件功能异常',
          icon: 'none'
        });
      }
      // #endif
      
      // #ifdef MP-WEIXIN
      try {
        uni.chooseMessageFile({
          count: 1,
          type: 'file',
          extension: ['doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'pdf', 'txt', 'md'],
          success: (res) => {
            if (res.tempFiles && res.tempFiles.length > 0) {
              this.file = res.tempFiles[0];
            }
          },
          fail: (err) => {
            console.error('选择文件失败:', err);
            uni.showToast({
              title: '选择文件失败',
              icon: 'none'
            });
          }
        });
      } catch (e) {
        console.error('微信小程序调用chooseMessageFile出错:', e);
        uni.showToast({
          title: '选择文件功能异常',
          icon: 'none'
        });
      }
      // #endif
      
      // #ifdef APP-PLUS
      try {
        // App端先尝试选择文件，如不支持则退回到选择图片
        // 注意：plus.io需要在App环境下才能使用
        if (typeof plus !== 'undefined' && plus.io && plus.io.openDocumentReader) {
          plus.io.openDocumentReader({
            success: (file) => {
              this.file = {
                name: file.name || '未命名文件',
                path: file.path,
                size: file.size || 0
              };
            },
            fail: (error) => {
              // 如果文档选择器失败，退回到图片选择
              this.chooseImageFallback();
            }
          });
        } else {
          // 不支持文档选择，使用图片选择作为备选
          this.chooseImageFallback();
        }
      } catch (e) {
        console.error('App环境调用文件选择出错:', e);
        // 如果出现异常，尝试使用图片选择
        this.chooseImageFallback();
      }
      // #endif
    },
    
    // App环境下使用图片选择作为备选
    chooseImageFallback() {
      uni.chooseImage({
        count: 1,
        success: (res) => {
          if (res.tempFilePaths && res.tempFilePaths.length > 0) {
            // 构造与其他平台一致的格式
            this.file = {
              path: res.tempFilePaths[0],
              name: res.tempFilePaths[0].substring(res.tempFilePaths[0].lastIndexOf('/') + 1) || '图片文件.png',
              size: res.tempFiles && res.tempFiles[0] ? res.tempFiles[0].size : 0
            };
          }
        },
        fail: (err) => {
          console.error('选择图片失败:', err);
          uni.showToast({
            title: '选择文件失败',
            icon: 'none'
          });
        }
      });
    },

    // 上传文件
    async uploadFile() {
      // 检查文件是否已选择
      if (!this.file) {
        api.showError('请先选择文件');
        return;
      }
      
      // 检查知识库ID是否有效
      if (!this.kbId) {
        api.showError('无效的知识库ID');
        return;
      }
      
      // 检查用户是否已登录
      if (!this.isLoggedIn) {
        uni.showModal({
          title: '提示',
          content: '上传文件需要先登录，是否前往登录？',
          success: (res) => {
            if (res.confirm) {
              this.loginVisible = true;
            }
          }
        });
        return;
      }
      
      // 设置加载状态
      this.loading = true;
      
      // 构建上传参数
      const formData = {
        knowledge_base_id: this.kbId
      };
      
      try {
        // 上传文件
        const result = await api.upload('/llm/upload-document', this.file.path, formData);
        
        if (result && result.code === '0000') {
          api.showSuccess('文件上传成功');
        
          // 刷新知识库详情和文档列表
          await this.fetchKnowledgeBaseDetail();
        
          // 清空已选文件
          this.file = null;
        } else {
          // 使用更安全的错误处理
          const errorMessage = result?.message || result?.msg || result?.errMsg || '文件上传失败';
          api.showError(errorMessage);
        }
      } catch (error) {
        console.error('文件上传失败:', error);
        
        // 使用统一的错误处理方法
        const normalizedError = normalizeError(error);
        const errorMessage = normalizedError.message || normalizedError.msg || normalizedError.errMsg || '文件上传失败，请重试';
        api.showError(errorMessage);
      } finally {
        this.loading = false;
      }
    },

    // 删除文件
    async deleteFile(docId) {
      // 检查用户是否已登录
      if (!this.isLoggedIn) {
        uni.showModal({
          title: '提示',
          content: '删除文件需要先登录，是否前往登录？',
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
        content: '确定要删除此文件吗？此操作不可恢复！',
        success: async (res) => {
          if (res.confirm) {
            this.loading = true;
            
            try {
              const result = await api.delete(`/llm/documents/${docId}`);
              
              if (result && result.code === '0000') {
                api.showSuccess('文件删除成功');
              
                // 刷新知识库详情和文档列表
                await this.fetchKnowledgeBaseDetail();
              } else {
                // 使用更安全的错误处理
                const errorMessage = result?.message || result?.msg || '文件删除失败';
                api.showError(errorMessage);
              }
            } catch (error) {
              console.error('文件删除失败:', error);
              // 直接处理错误消息，不依赖于特定属性
              if (error && typeof error === 'object') {
                const errorMessage = 
                  error.message || 
                  error.msg || 
                  error.errMsg || 
                  (error.data && (typeof error.data === 'string' ? error.data : (error.data.message || error.data.msg))) || 
                  '文件删除失败';
                  
                api.showError(errorMessage);
              } else {
                api.showError('文件删除失败，请重试');
              }
            } finally {
              this.loading = false;
            }
          }
        }
      });
    },
    
    // 显示重命名知识库弹窗
    showRenameKBDialog() {
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
      
      this.newKBName = this.knowledgeBase.name;
      this.newKBDesc = this.knowledgeBase.description || '';
      this.showRenameKB = true;
    },
    
    // 取消重命名知识库
    cancelRenameKB() {
      this.showRenameKB = false;
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
        const result = await api.put(`/llm/knowledge-bases/${this.kbId}`, {
          name: this.newKBName,
          description: this.newKBDesc || ''
        });
        
        if (result && result.code === '0000') {
          api.showSuccess('知识库更新成功');
          
          // 刷新知识库详情
          await this.fetchKnowledgeBaseDetail();
        } else {
          // 使用更安全的错误处理
          const errorMessage = result?.message || result?.msg || '更新知识库失败';
          api.showError(errorMessage);
        }
      } catch (error) {
        console.error('更新知识库失败:', error);
        // 直接处理错误消息，不依赖于特定属性
        if (error && typeof error === 'object') {
          const errorMessage = 
            error.message || 
            error.msg || 
            error.errMsg || 
            (error.data && (typeof error.data === 'string' ? error.data : (error.data.message || error.data.msg))) || 
            '更新知识库失败';
            
          api.showError(errorMessage);
        } else {
          api.showError('更新知识库失败，请重试');
        }
      }
      
      this.showRenameKB = false;
    },

    // 格式化文件大小
    formatFileSize(bytes) {
      if (bytes === 0) return '0 Bytes';
      const k = 1024;
      const sizes = ['Bytes', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },
    
    // 格式化分块策略
    formatChunkingStrategy(strategy) {
      const strategies = {
        'fixed': '固定长度',
        'semantic': '语义分块',
        'sentence': '句子分块'
      };
      return strategies[strategy] || strategy;
    },
    
    // 返回列表页
    goBack() {
      // 获取当前页面栈
      const pages = getCurrentPages();
      
      // 如果有上一页，则正常返回
      if (pages.length > 1) {
        uni.navigateBack();
      } else {
        // 如果没有上一页，则返回知识库列表页
        uni.switchTab({
          url: '/pages/knowledge-base/index'
        });
      }
    },

    // 登录成功后的处理
    onLoginSuccess(userInfo) {
      // 更新用户信息
      
      // 如果userInfo是字符串，尝试解析
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
      
      // 登录成功后，重新加载知识库详情和文档列表
      this.fetchKnowledgeBaseDetail();
    },

    // 登录弹窗可见性变化的处理
    onLoginVisibleChange(visible) {
      this.loginVisible = visible;
    },

    // 显示登录对话框
    showLoginDialog() {
      this.loginVisible = true;
    },

    // 格式化文档状态
    formatDocStatus(status) {
      const statusMap = {
        'uploaded': '已上传',
        'pending': '等待处理',
        'processing': '处理中',
        'completed': '已完成',
        'failed': '处理失败'
      };
      return statusMap[status] || status;
    },
    
    // 处理文档（向量化）
    async processDocument(docId) {
      if (!this.isLoggedIn) {
        uni.showModal({
          title: '提示',
          content: '处理文档需要先登录，是否前往登录？',
          success: (res) => {
            if (res.confirm) {
              this.loginVisible = true;
            }
          }
        });
        return;
      }
      
      // 将文档ID添加到处理列表
      this.processingDocIds.push(docId);
      
      try {
        // 调用API处理文档
        const result = await api.put(`/llm/documents/${docId}`);
        
        if (result && result.code === '0000') {
          api.showSuccess('文档处理请求已发送');
          
          // 轮询检查文档状态，直到处理完成
          this.pollDocumentStatus(docId);
        } else {
          // 使用更安全的错误处理
          const errorMessage = result?.message || result?.msg || '文档处理请求失败';
          api.showError(errorMessage);
          // 从处理列表中移除
          const index = this.processingDocIds.indexOf(docId);
          if (index !== -1) {
            this.processingDocIds.splice(index, 1);
          }
        }
      } catch (error) {
        console.error('处理文档失败:', error);
        // 直接处理错误消息，不依赖于特定属性
        if (error && typeof error === 'object') {
          const errorMessage = 
            error.message || 
            error.msg || 
            error.errMsg || 
            (error.data && (typeof error.data === 'string' ? error.data : (error.data.message || error.data.msg))) || 
            '处理文档失败';
            
          api.showError(errorMessage);
        } else {
          api.showError('处理文档失败，请重试');
        }
        // 从处理列表中移除
        const index = this.processingDocIds.indexOf(docId);
        if (index !== -1) {
          this.processingDocIds.splice(index, 1);
        }
      }
    },
    
    // 轮询检查文档状态
    async pollDocumentStatus(docId) {
      try {
        // 先获取单个文档状态
        const result = await api.get(`/llm/documents/${docId}`);
        
        if (result && result.code === '0000') {
          const docStatus = result.data.status;
          
          // 根据状态决定是否继续轮询
          if (docStatus === 'processing' || docStatus === 'pending') {
            // 继续轮询
            setTimeout(() => {
              this.pollDocumentStatus(docId);
            }, 3000); // 每3秒检查一次
          } else {
            // 处理完成或失败，刷新知识库详情和文档列表
            await this.fetchKnowledgeBaseDetail();
            
            // 从处理列表中移除
            const index = this.processingDocIds.indexOf(docId);
            if (index !== -1) {
              this.processingDocIds.splice(index, 1);
            }
            
            // 显示处理结果
            if (docStatus === 'completed') {
              api.showSuccess('文档处理成功');
            } else if (docStatus === 'failed') {
              api.showError('文档处理失败');
            }
          }
        } else {
          // 使用更安全的错误处理
          const errorMessage = result?.message || result?.msg || '获取文档状态失败';
          api.showError(errorMessage);
          
          // 获取状态失败，也刷新知识库详情和文档列表
          await this.fetchKnowledgeBaseDetail();
          
          // 从处理列表中移除
          const index = this.processingDocIds.indexOf(docId);
          if (index !== -1) {
            this.processingDocIds.splice(index, 1);
          }
        }
      } catch (error) {
        console.error('获取文档状态失败:', error);
        // 直接处理错误消息，不依赖于特定属性
        if (error && typeof error === 'object') {
          const errorMessage = 
            error.message || 
            error.msg || 
            error.errMsg || 
            (error.data && (typeof error.data === 'string' ? error.data : (error.data.message || error.data.msg))) || 
            '获取文档状态失败';
            
          api.showError(errorMessage);
        } else {
          api.showError('获取文档状态失败，请重试');
        }
        
        // 出错也刷新知识库详情和文档列表
        await this.fetchKnowledgeBaseDetail();
        
        // 从处理列表中移除
        const index = this.processingDocIds.indexOf(docId);
        if (index !== -1) {
          this.processingDocIds.splice(index, 1);
        }
      }
    }
  }
}
</script>

<style>
.detail-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

/* 自定义返回按钮样式 */
.custom-header {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
}

.back-btn {
  display: flex;
  align-items: center;
  background-color: #f0f0f0;
  padding: 8px 15px;
  border-radius: 6px;
  cursor: pointer;
}

.back-icon {
  font-size: 14px;
  color: #333;
}

.kb-header {
  display: flex;
  flex-direction: column;
  margin-bottom: 20px;
  background-color: white;
  border-radius: 10px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.kb-header-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 15px;
}

.kb-info {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 200px;
}

.kb-name {
  font-size: 24px;
  font-weight: 600;
  color: #333;
  margin-bottom: 5px;
}

.kb-description {
  font-size: 14px;
  color: #666;
}

.login-hint-inline {
  display: flex;
  align-items: center;
  gap: 10px;
}

.file-upload-controls {
  display: flex;
  gap: 10px;
  align-items: center;
}

.file-name-container {
  margin-top: 15px;
  padding: 10px;
  background-color: #f8f9fa;
  border-radius: 6px;
  border: 1px dashed #ddd;
  font-size: 14px;
}

/* 移除不再需要的样式 */
.upload-section {
  display: none;
}

/* 登录提示样式修改，原来的保留给其他地方用 */
.login-hint {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 15px;
  background-color: #f8f9fa;
  border-radius: 10px;
  margin-bottom: 20px;
  color: #666;
  font-size: 14px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

/* 响应式调整 */
@media screen and (max-width: 767px) {
  .kb-header-top {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .file-upload-controls {
    width: 100%;
    margin-top: 10px;
  }
  
  .login-hint-inline {
    width: 100%;
    margin-top: 10px;
    justify-content: flex-start;
  }
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
  margin-bottom: 15px;
}

/* 按钮样式 */
.action-btn {
  font-size: 13px;
  padding: 8px 15px;
  border-radius: 6px;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 32px;
}

.back-btn {
  background-color: #f0f0f0;
  color: #333;
}

.rename-btn {
  background-color: var(--primary-color, #007AFF);
  color: white;
}

.login-btn {
  background-color: var(--primary-color, #007AFF);
  color: white;
  padding: 8px 15px;
  border-radius: 6px;
  font-size: 14px;
  margin-left: 10px;
}

/* 文件上传区域 */
.upload-section {
  background-color: white;
  border-radius: 10px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.file-picker {
  display: flex;
  flex-direction: column;
}

.file-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.select-file-btn, .upload-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 32px;
}

.select-file-btn {
  background-color: #f0f0f0;
  color: #333;
  padding: 8px 15px;
  border-radius: 6px;
  font-size: 14px;
  border: none;
}

.upload-btn {
  background-color: var(--primary-color, #007AFF);
  color: white;
  padding: 8px 15px;
  border-radius: 6px;
  font-size: 14px;
  border: none;
}

.upload-btn[disabled] {
  background-color: #cccccc;
  color: #666;
}

.file-name {
  font-weight: 500;
  color: #333;
}

.file-size {
  color: #999;
  margin-left: 5px;
}

/* 文件列表区域 */
.file-list-section {
  background-color: white;
  border-radius: 10px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.file-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  background-color: #f8f9fa;
  border-radius: 6px;
  transition: background-color 0.2s;
}

.file-item:hover {
  background-color: #f0f0f0;
}

.file-info {
  display: flex;
  flex-direction: column;
}

.file-name {
  font-size: 14px;
  color: #333;
  margin-bottom: 5px;
  word-break: break-word;
}

.file-size {
  font-size: 12px;
  color: #999;
}

/* 加载和空状态 */
.loading, .empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 40px 0;
  text-align: center;
  color: #999;
  font-size: 16px;
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

.form-input, .form-textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  background-color: #f8f9fa;
  font-size: 14px;
  box-sizing: border-box;
}

.form-textarea {
  min-height: 80px;
  resize: vertical;
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

.delete-btn {
  background-color: rgba(255, 59, 48, 0.1);
  color: #ff3b30;
  padding: 5px 10px;
  border-radius: 4px;
  font-size: 12px;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 28px;
}

/* 响应式设计 */
@media screen and (min-width: 768px) {
  .detail-container {
    padding: 30px;
  }
}

/* 文件状态样式 */
.file-meta {
  display: flex;
  gap: 10px;
  align-items: center;
}

.file-status {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 10px;
  background-color: #f0f0f0;
  color: #666;
}

.status-badge {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.status-uploaded {
  background-color: #e6f7ff;
  color: #1890ff;
}

.status-pending {
  background-color: #fff7e6;
  color: #fa8c16;
}

.status-processing {
  background-color: #f6ffed;
  color: #52c41a;
  animation: pulse 1.5s infinite;
}

.status-completed {
  background-color: #f6ffed;
  color: #52c41a;
}

.status-failed {
  background-color: #fff1f0;
  color: #f5222d;
}

@keyframes pulse {
  0% {
    opacity: 0.7;
  }
  50% {
    opacity: 1;
  }
  100% {
    opacity: 0.7;
  }
}

.process-btn, .delete-btn {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  border: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  height: 28px;
  white-space: nowrap;
}

.process-btn {
  background-color: rgba(24, 144, 255, 0.1);
  color: #1890ff;
}

.delete-btn {
  background-color: rgba(255, 59, 48, 0.1);
  color: #ff3b30;
}

.process-btn[disabled] {
  background-color: #f5f5f5;
  color: #d9d9d9;
  cursor: not-allowed;
}

/* 按钮垂直居中修复 */
button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.login-btn, .select-file-btn, .upload-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 36px;
}

/* 弹窗按钮修复 */
.dialog-buttons button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 36px;
}

/* 表格样式 */
.table-container {
  width: 100%;
  overflow-x: auto;
  margin-top: 10px;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.document-list {
  width: 100%;
  display: flex;
  flex-direction: column;
}

.document-header {
  display: flex;
  align-items: center;
  background-color: #f8f9fa;
  padding: 12px 15px;
  border-bottom: 1px solid #eee;
}

.header-cell {
  font-weight: 600;
  color: #333;
  font-size: 14px;
  text-align: left;
}

.document-row {
  display: flex;
  align-items: center;
  padding: 12px 15px;
  border-bottom: 1px solid #eee;
}

.document-row:last-child {
  border-bottom: none;
}

.document-row:hover {
  background-color: #f8f9fa;
}

.doc-cell {
  font-size: 14px;
  color: #333;
  text-align: left;
}

/* 列宽设置 */
.name-cell {
  flex: 3;
  min-width: 120px;
  padding-right: 10px;
}

.size-cell {
  flex: 1;
  min-width: 60px;
}

.status-cell {
  flex: 1;
  min-width: 80px;
}

.action-cell {
  flex: 1.5;
  min-width: 120px;
  display: flex;
  gap: 8px;
  align-items: center;
  justify-content: flex-start;
}

/* 微信小程序特定样式 */
/* #ifdef MP-WEIXIN */
.document-header, .document-row {
  display: flex;
  flex-direction: row;
  flex-wrap: nowrap;
}

.header-cell, .doc-cell {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
/* #endif */

.doc-name {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: block;
}

/* 分块配置信息样式 */
.chunk-config-info {
  margin-top: 15px;
  padding: 12px;
  background-color: #f8f9fa;
  border-radius: 8px;
  border-left: 3px solid var(--primary-color, #007AFF);
}

.chunk-config-title {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  margin-bottom: 8px;
}

.chunk-config-items {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
}

.chunk-config-item {
  display: flex;
  align-items: center;
  gap: 5px;
}

.config-label {
  font-size: 12px;
  color: #999;
}

.config-value {
  font-size: 12px;
  color: #333;
  font-weight: 500;
}
</style> 