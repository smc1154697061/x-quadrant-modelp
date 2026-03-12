<template>
  <view class="template-generate-page">
    <view class="custom-navbar">
      <view class="navbar-left" @tap="goBack">
        <text class="back-icon">‹</text>
      </view>
      <view class="navbar-title">
        <text>文档生成</text>
      </view>
      <view class="navbar-right" @tap="showHistoryPopup">
        <text class="history-icon">📋</text>
      </view>
    </view>
    
    <scroll-view class="content-scroll" scroll-y>
      <view class="generate-container">
        <view class="info-card">
          <text class="info-icon">💡</text>
          <text class="info-text">选择模板并输入个人信息，AI将自动生成完整文档</text>
        </view>
        
        <view class="template-select-card">
          <view class="card-header">
            <text class="card-title">选择模板</text>
            <text class="card-tip" v-if="!selectedTemplate">点击选择模板</text>
          </view>
          
          <view v-if="!selectedTemplate" class="template-select-btn" @tap="goToSelectTemplate">
            <text class="select-icon">📄</text>
            <text class="select-text">选择模板</text>
            <text class="select-arrow">›</text>
          </view>
          
          <view v-else class="selected-template">
            <view class="template-preview">
              <view class="template-icon">
                <text>{{ getFileIcon(selectedTemplate.file_type) }}</text>
              </view>
              <view class="template-info">
                <text class="template-name">{{ selectedTemplate.name }}</text>
                <text class="template-category">{{ selectedTemplate.category }}</text>
              </view>
              <text class="change-btn" @tap="goToSelectTemplate">更换</text>
            </view>
          </view>
        </view>
        
        <view class="input-card">
          <view class="card-header">
            <text class="card-title">输入信息</text>
            <text class="char-count">{{ userInput.length }} 字</text>
          </view>
          
          <textarea 
            v-model="userInput" 
            class="user-input"
            placeholder="请输入您的个人信息，如姓名、联系方式、工作经历、教育背景等...&#10;&#10;示例：&#10;姓名：张三&#10;年龄：28岁&#10;联系方式：13812345678&#10;邮箱：zhangsan@example.com&#10;工作经历：5年软件开发经验..."
            :maxlength="-1"
          />
        </view>
        
        <view class="format-card">
          <view class="card-header">
            <text class="card-title">输出格式</text>
          </view>
          
          <view class="format-options">
            <view 
              class="format-option" 
              :class="{ active: outputFormat === 'word' }" 
              @tap="outputFormat = 'word'"
            >
              <text class="format-icon">📝</text>
              <text class="format-name">Word</text>
            </view>
            <view 
              class="format-option" 
              :class="{ active: outputFormat === 'pdf' }" 
              @tap="outputFormat = 'pdf'"
            >
              <text class="format-icon">📕</text>
              <text class="format-name">PDF</text>
            </view>
          </view>
        </view>
        
        <view class="action-bar">
          <button 
            class="generate-btn" 
            :class="{ 'btn-disabled': !canGenerate }"
            :disabled="!canGenerate || generating"
            @tap="generateDocument"
          >
            <text v-if="generating">生成中...</text>
            <text v-else>生成文档</text>
          </button>
        </view>
        
        <view v-if="generatedContent" class="result-card">
          <view class="card-header">
            <text class="card-title">生成结果</text>
            <view class="result-actions">
              <button class="action-btn" @tap="copyContent">
                <text>复制</text>
              </button>
              <button class="action-btn primary" @tap="downloadDocument">
                <text>下载</text>
              </button>
            </view>
          </view>
          
          <view class="result-content">
            <text class="result-text">{{ generatedContent }}</text>
          </view>
        </view>
      </view>
    </scroll-view>
    
    <view v-if="showHistoryModal" class="popup-mask" @tap="closeHistoryPopup">
      <view class="popup-content" @tap.stop>
        <view class="popup-header">
          <text class="popup-title">生成历史</text>
          <text class="popup-close" @tap="closeHistoryPopup">×</text>
        </view>
        
        <scroll-view class="popup-scroll" scroll-y>
          <view v-if="historyList.length === 0" class="empty-state">
            <text class="empty-icon">📭</text>
            <text class="empty-text">暂无生成历史</text>
          </view>
          
          <view v-else>
            <view 
              v-for="item in historyList" 
              :key="item.id" 
              class="history-item"
            >
              <view class="history-header">
                <text class="history-template">{{ item.template_name }}</text>
                <text class="history-time">{{ formatDate(item.created_at) }}</text>
              </view>
              <view class="history-preview">
                <text>{{ item.user_input?.substring(0, 50) }}...</text>
              </view>
              <view class="history-actions">
                <button class="history-btn" @tap="downloadHistoryDoc(item)">下载</button>
              </view>
            </view>
          </view>
        </scroll-view>
      </view>
    </view>
  </view>
</template>

<script>
import api from '../../../utils/api.js';

export default {
  data() {
    return {
      selectedTemplate: null,
      userInput: '',
      outputFormat: 'word',
      generating: false,
      generatedContent: '',
      generatedDocId: null,
      showHistoryModal: false,
      historyList: []
    };
  },
  
  computed: {
    canGenerate() {
      return this.selectedTemplate && this.userInput.trim();
    }
  },
  
  onLoad(options) {
    if (options.template_id) {
      this.loadTemplateInfo(options.template_id);
    }
    if (options.template_name) {
      uni.setNavigationBarTitle({
        title: decodeURIComponent(options.template_name)
      });
    }
  },
  
  onShow() {
    const selectedTemplate = uni.getStorageSync('selectedTemplate');
    if (selectedTemplate) {
      try {
        this.selectedTemplate = typeof selectedTemplate === 'string' ? JSON.parse(selectedTemplate) : selectedTemplate;
        uni.removeStorageSync('selectedTemplate');
      } catch (e) {
        console.error('解析选中模板失败:', e);
      }
    }
  },
  
  methods: {
    goBack() {
      uni.navigateBack();
    },
    
    async loadTemplateInfo(templateId) {
      try {
        const result = await api.get('/llm/templates');
        if (result && result.code === 0 && result.data) {
          const template = result.data.find(t => t.id == templateId);
          if (template) {
            this.selectedTemplate = template;
          }
        }
      } catch (error) {
        console.error('加载模板信息失败:', error);
      }
    },
    
    goToSelectTemplate() {
      uni.navigateTo({
        url: '/pages/tools/template-manage/index'
      });
    },
    
    async generateDocument() {
      if (!this.canGenerate || this.generating) return;
      
      this.generating = true;
      this.generatedContent = '';
      this.generatedDocId = null;
      
      uni.showLoading({
        title: '生成中...',
        mask: true
      });
      
      try {
        const result = await api.post('/llm/documents/generate', {
          template_id: this.selectedTemplate.id,
          user_input: this.userInput,
          output_format: this.outputFormat
        });
        
        uni.hideLoading();
        
        if (result && result.code === 0 && result.data) {
          this.generatedContent = result.data.generated_content || '';
          this.generatedDocId = result.data.id;
          
          uni.showToast({
            title: '生成成功',
            icon: 'success'
          });
        } else {
          uni.showToast({
            title: result?.message || '生成失败',
            icon: 'none'
          });
        }
      } catch (error) {
        uni.hideLoading();
        console.error('生成文档失败:', error);
        uni.showToast({
          title: '生成失败',
          icon: 'none'
        });
      } finally {
        this.generating = false;
      }
    },
    
    copyContent() {
      if (!this.generatedContent) return;
      
      uni.setClipboardData({
        data: this.generatedContent,
        success: () => {
          uni.showToast({
            title: '已复制',
            icon: 'success'
          });
        }
      });
    },
    
    downloadDocument() {
      if (!this.generatedDocId) return;
      
      uni.showLoading({
        title: '下载中...',
        mask: true
      });
      
      const downloadUrl = `${api.baseUrl || ''}/api/llm/documents/generated/${this.generatedDocId}`;
      const token = uni.getStorageSync('token');
      
      uni.downloadFile({
        url: downloadUrl,
        header: {
          'Authorization': `Bearer ${token}`
        },
        success: (res) => {
          uni.hideLoading();
          if (res.statusCode === 200) {
            uni.saveFile({
              tempFilePath: res.tempFilePath,
              success: (saveRes) => {
                uni.showToast({
                  title: '保存成功',
                  icon: 'success'
                });
              },
              fail: () => {
                uni.showToast({
                  title: '保存失败',
                  icon: 'none'
                });
              }
            });
          } else {
            uni.showToast({
              title: '下载失败',
              icon: 'none'
            });
          }
        },
        fail: () => {
          uni.hideLoading();
          uni.showToast({
            title: '下载失败',
            icon: 'none'
          });
        }
      });
    },
    
    showHistoryPopup() {
      this.showHistoryModal = true;
      this.loadHistory();
    },
    
    closeHistoryPopup() {
      this.showHistoryModal = false;
    },
    
    async loadHistory() {
      try {
        const result = await api.get('/llm/documents/generated');
        if (result && result.code === 0) {
          this.historyList = result.data || [];
        }
      } catch (error) {
        console.error('加载历史记录失败:', error);
      }
    },
    
    downloadHistoryDoc(item) {
      uni.showLoading({
        title: '下载中...',
        mask: true
      });
      
      const downloadUrl = `${api.baseUrl || ''}/api/llm/documents/generated/${item.id}`;
      const token = uni.getStorageSync('token');
      
      uni.downloadFile({
        url: downloadUrl,
        header: {
          'Authorization': `Bearer ${token}`
        },
        success: (res) => {
          uni.hideLoading();
          if (res.statusCode === 200) {
            uni.saveFile({
              tempFilePath: res.tempFilePath,
              success: () => {
                uni.showToast({
                  title: '保存成功',
                  icon: 'success'
                });
              },
              fail: () => {
                uni.showToast({
                  title: '保存失败',
                  icon: 'none'
                });
              }
            });
          }
        },
        fail: () => {
          uni.hideLoading();
          uni.showToast({
            title: '下载失败',
            icon: 'none'
          });
        }
      });
    },
    
    getFileIcon(fileType) {
      const icons = {
        'word': '📝',
        'pdf': '📕',
        'txt': '📄'
      };
      return icons[fileType] || '📄';
    },
    
    formatDate(timestamp) {
      if (!timestamp) return '';
      const date = new Date(timestamp);
      return date.toLocaleString('zh-CN', {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      });
    }
  }
};
</script>

<style scoped>
.template-generate-page {
  width: 100%;
  height: 100vh;
  background: #f5f7fa;
  display: flex;
  flex-direction: column;
}

.custom-navbar {
  height: 44px;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 15px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  position: sticky;
  top: 0;
  z-index: 100;
}

.navbar-left,
.navbar-right {
  width: 60px;
}

.back-icon {
  font-size: 32px;
  color: #333;
  font-weight: 300;
}

.history-icon {
  font-size: 22px;
}

.navbar-title {
  flex: 1;
  text-align: center;
  font-size: 17px;
  font-weight: 600;
  color: #333;
}

.content-scroll {
  flex: 1;
  height: 0;
}

.generate-container {
  padding: 15px;
  max-width: 680px;
  margin: 0 auto;
}

.info-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 15px;
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 15px;
}

.info-icon {
  font-size: 24px;
}

.info-text {
  flex: 1;
  font-size: 13px;
  color: #fff;
  line-height: 1.5;
}

.template-select-card,
.input-card,
.format-card,
.result-card {
  background: #fff;
  border-radius: 12px;
  padding: 15px;
  margin-bottom: 15px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.card-tip {
  font-size: 12px;
  color: #999;
}

.char-count {
  font-size: 12px;
  color: #999;
}

.template-select-btn {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 8px;
}

.select-icon {
  font-size: 28px;
}

.select-text {
  flex: 1;
  font-size: 15px;
  color: #666;
}

.select-arrow {
  font-size: 20px;
  color: #ccc;
}

.selected-template {
  background: #f5f7fa;
  border-radius: 8px;
  padding: 12px;
}

.template-preview {
  display: flex;
  align-items: center;
  gap: 12px;
}

.template-preview .template-icon {
  width: 44px;
  height: 44px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
}

.template-preview .template-info {
  flex: 1;
}

.template-preview .template-name {
  font-size: 15px;
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
  display: block;
}

.template-preview .template-category {
  font-size: 12px;
  color: #667eea;
}

.change-btn {
  font-size: 13px;
  color: #667eea;
  padding: 4px 12px;
  background: rgba(102, 126, 234, 0.1);
  border-radius: 12px;
}

.user-input {
  width: 100%;
  min-height: 200px;
  background: #f9f9f9;
  border-radius: 8px;
  padding: 12px;
  font-size: 14px;
  line-height: 1.6;
  box-sizing: border-box;
}

.format-options {
  display: flex;
  gap: 12px;
}

.format-option {
  flex: 1;
  height: 60px;
  background: #f5f7fa;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  transition: all 0.3s;
}

.format-option.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.format-icon {
  font-size: 22px;
}

.format-name {
  font-size: 13px;
  color: #666;
}

.format-option.active .format-name {
  color: #fff;
}

.action-bar {
  margin: 20px 0;
}

.generate-btn {
  width: 100%;
  height: 48px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  border: none;
  border-radius: 24px;
  font-size: 16px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.generate-btn.btn-disabled {
  background: #ddd;
  color: #999;
  box-shadow: none;
}

.result-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  padding: 4px 12px;
  background: #f0f2f5;
  border: none;
  border-radius: 15px;
  font-size: 12px;
  color: #666;
  height: auto;
  line-height: 1;
}

.action-btn.primary {
  background: #667eea;
  color: #fff;
}

.result-content {
  background: #f9f9f9;
  border-radius: 8px;
  padding: 12px;
  max-height: 400px;
  overflow-y: auto;
}

.result-text {
  font-size: 14px;
  color: #333;
  line-height: 1.8;
  white-space: pre-wrap;
}

.popup-mask {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: flex-end;
  z-index: 999;
}

.popup-content {
  width: 100%;
  max-height: 80vh;
  background: #fff;
  border-radius: 20px 20px 0 0;
  display: flex;
  flex-direction: column;
}

.popup-header {
  padding: 15px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #f0f0f0;
}

.popup-title {
  font-size: 17px;
  font-weight: 600;
  color: #333;
}

.popup-close {
  font-size: 32px;
  color: #999;
  font-weight: 300;
}

.popup-scroll {
  padding: 15px 20px;
  max-height: 60vh;
}

.empty-state {
  padding: 60px 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.empty-icon {
  font-size: 48px;
  opacity: 0.5;
}

.empty-text {
  font-size: 14px;
  color: #999;
}

.history-item {
  background: #f9f9f9;
  border-radius: 10px;
  padding: 12px;
  margin-bottom: 10px;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.history-template {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.history-time {
  font-size: 11px;
  color: #999;
}

.history-preview {
  font-size: 12px;
  color: #666;
  margin-bottom: 10px;
}

.history-actions {
  display: flex;
  justify-content: flex-end;
}

.history-btn {
  padding: 4px 16px;
  background: #667eea;
  color: #fff;
  border: none;
  border-radius: 15px;
  font-size: 12px;
  height: auto;
  line-height: 1;
}

@media screen and (min-width: 768px) {
  .generate-container {
    padding: 30px;
  }
}
</style>
