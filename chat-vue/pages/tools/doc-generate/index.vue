<template>
  <view class="doc-generate-page">
    <view class="custom-navbar">
      <view class="navbar-left" @tap="goBack">
        <text class="back-icon">‹</text>
      </view>
      <view class="navbar-title">
        <text>文档生成</text>
      </view>
      <view class="navbar-right"></view>
    </view>
    
    <scroll-view class="content-scroll" scroll-y>
      <view class="generate-container">
        <view class="info-card">
          <text class="info-icon">✍️</text>
          <text class="info-text">选择模板并输入需求，AI将智能生成专业文档</text>
        </view>
        
        <view class="template-select-card">
          <text class="card-title">选择模板</text>
          <view class="template-selector" @tap="showTemplatePicker">
            <view v-if="!selectedTemplate" class="selector-empty">
              <text class="selector-hint">点击选择模板</text>
            </view>
            <view v-else class="template-selected">
              <text class="template-icon">{{ getTemplateIcon(selectedTemplate.type) }}</text>
              <view class="template-info">
                <text class="template-name">{{ selectedTemplate.name }}</text>
                <text class="template-tag">{{ selectedTemplate.tag }}</text>
              </view>
            </view>
            <text class="selector-arrow">›</text>
          </view>
        </view>
        
        <view class="input-card">
          <view class="card-header">
            <text class="card-title">文档需求</text>
            <text class="card-tip">请详细描述您的需求</text>
          </view>
          <textarea 
            v-model="userInput" 
            class="user-input"
            placeholder="例如：生成一份前端开发工程师的简历，包含3年工作经验，擅长Vue3、uni-app，有RAG项目经验..."
            :maxlength="-1"
          />
        </view>
        
        <view class="action-bar">
          <button 
            class="generate-btn" 
            :class="{ 'btn-disabled': !canGenerate }"
            :disabled="!canGenerate"
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
              <button class="action-btn" @tap="copyResult">
                <text>复制</text>
              </button>
              <button class="action-btn" @tap="downloadDoc('word')">
                <text>Word</text>
              </button>
              <button class="action-btn" @tap="downloadDoc('pdf')">
                <text>PDF</text>
              </button>
            </view>
          </view>
          <view class="result-content">
            <text class="result-text">{{ generatedContent }}</text>
          </view>
        </view>
        
        <view v-if="historyCount > 0" class="history-entry" @tap="showHistory">
          <text class="history-text">历史记录 ({{ historyCount }})</text>
          <text class="history-arrow">›</text>
        </view>
      </view>
    </scroll-view>
    
    <view v-if="showTemplatePopup" class="popup-mask" @tap="closeTemplatePicker">
      <view class="popup-content" @tap.stop>
        <view class="popup-header">
          <text class="popup-title">选择模板</text>
          <text class="popup-close" @tap="closeTemplatePicker">×</text>
        </view>
        <scroll-view class="popup-scroll" scroll-y :style="{height: popupScrollHeight + 'px'}">
          <view v-if="availableTemplates.length === 0" class="empty-state">
            <text class="empty-icon">📭</text>
            <text class="empty-text">暂无可用模板</text>
          </view>
          <view v-else>
            <view 
              v-for="template in availableTemplates" 
              :key="template.id" 
              class="template-item"
              @tap="selectTemplate(template)"
            >
              <text class="item-icon">{{ getTemplateIcon(template.type) }}</text>
              <view class="item-info">
                <text class="item-name">{{ template.name }}</text>
                <text class="item-tag">{{ template.tag }}</text>
              </view>
            </view>
          </view>
        </scroll-view>
      </view>
    </view>
    
    <view v-if="showHistoryPopup" class="popup-mask" @tap="closeHistory">
      <view class="popup-content history-popup" @tap.stop>
        <view class="popup-header">
          <text class="popup-title">生成历史</text>
          <text class="popup-close" @tap="closeHistory">×</text>
        </view>
        <scroll-view class="popup-scroll" scroll-y :style="{height: popupScrollHeight + 'px'}">
          <view v-if="generationHistory.length === 0" class="empty-state">
            <text class="empty-icon">📭</text>
            <text class="empty-text">暂无历史记录</text>
          </view>
          <view v-else>
            <view 
              v-for="(item, index) in generationHistory" 
              :key="index" 
              class="history-item"
              @tap="useHistoryItem(item)"
            >
              <view class="history-item-header">
                <text class="history-title">{{ item.title || '未命名文档' }}</text>
                <text class="history-time">{{ formatDate(item.timestamp) }}</text>
              </view>
              <view class="history-preview">
                <text class="preview-text">{{ item.content.substring(0, 80) }}...</text>
              </view>
              <view class="history-actions">
                <button class="history-action-btn" @tap.stop="downloadHistoryDoc(item, 'word')">
                  <text>Word</text>
                </button>
                <button class="history-action-btn" @tap.stop="downloadHistoryDoc(item, 'pdf')">
                  <text>PDF</text>
                </button>
              </view>
            </view>
          </view>
        </scroll-view>
        <view class="popup-footer">
          <button class="popup-btn danger" @tap="clearHistory">清空历史</button>
          <button class="popup-btn" @tap="closeHistory">关闭</button>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { docGenerateApi, templateApi } from '../../../utils/api.js';

export default {
  data() {
    return {
      selectedTemplate: null,
      userInput: '',
      generating: false,
      generatedContent: null,
      currentResultId: null,
      availableTemplates: [],
      showTemplatePopup: false,
      showHistoryPopup: false,
      generationHistory: [],
      windowHeight: 0,
      popupScrollHeight: 0,
      
      mockTemplates: [
        {
          id: 1,
          name: '个人简历模板',
          tag: '简历',
          type: 'word'
        },
        {
          id: 2,
          name: '技术报告模板',
          tag: '报告',
          type: 'pdf'
        },
        {
          id: 3,
          name: '销售合同模板',
          tag: '合同',
          type: 'word'
        },
        {
          id: 4,
          name: '毕业论文模板',
          tag: '论文',
          type: 'word'
        }
      ]
    };
  },
  
  computed: {
    canGenerate() {
      return !this.generating && this.selectedTemplate && this.userInput.trim();
    },
    
    historyCount() {
      return this.generationHistory.length;
    }
  },
  
  onLoad() {
    this.loadTemplates();
    this.loadHistory();
    uni.getSystemInfo({
      success: (res) => {
        this.windowHeight = res.windowHeight || 600;
        const headerFooterReserve = 160;
        const maxPopupHeight = Math.floor(this.windowHeight * 0.8);
        this.popupScrollHeight = Math.max(200, maxPopupHeight - headerFooterReserve);
      }
    });
  },
  
  methods: {
    goBack() {
      uni.navigateBack();
    },
    
    loadTemplates() {
      templateApi.getTemplates()
        .then(res => {
          if (res.code === 0 || res.code === '0000' || res.code === 'SUCCESS') {
            this.availableTemplates = res.data.map(item => ({
              id: item.id,
              name: item.name,
              tag: item.tag,
              type: item.file_type,
              createdAt: item.created_at
            }));
          } else {
            this.availableTemplates = [...this.mockTemplates];
          }
        })
        .catch(err => {
          console.error('加载模板失败:', err);
          this.availableTemplates = [...this.mockTemplates];
        });
    },
    
    showTemplatePicker() {
      this.showTemplatePopup = true;
    },
    
    closeTemplatePicker() {
      this.showTemplatePopup = false;
    },
    
    selectTemplate(template) {
      this.selectedTemplate = template;
      this.closeTemplatePicker();
    },
    
    async generateDocument() {
      if (!this.canGenerate) return;
      
      this.generating = true;
      this.generatedContent = null;
      
      uni.showLoading({
        title: '生成中...',
        mask: true
      });
      
      try {
        const requestData = {
          template_id: this.selectedTemplate.id,
          user_input: this.userInput
        };
        
        const result = await docGenerateApi.generateDocument(requestData);
        
        uni.hideLoading();
        
        if (result && (result.code === 0 || result.code === '0000' || result.code === 'SUCCESS')) {
          this.generatedContent = result.data?.generated_content || result.data?.content || result.data;
          this.currentResultId = result.data?.id || null;
          this.saveToHistory(result.data);
          uni.showToast({
            title: '生成成功',
            icon: 'success'
          });
        } else {
          uni.showToast({
            title: result.message || '生成失败',
            icon: 'none'
          });
          return;
        }
      } catch (error) {
        uni.hideLoading();
        console.error('生成失败:', error);
        uni.showToast({
          title: error.message || '生成失败',
          icon: 'none'
        });
      } finally {
        this.generating = false;
      }
    },
    
    copyResult() {
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
    
    async downloadDoc(type) {
      if (!this.currentResultId) {
        uni.showToast({
          title: '没有可下载的文档',
          icon: 'none'
        });
        return;
      }
      
      try {
        uni.showLoading({ title: '准备下载...' });
        
        const result = await docGenerateApi.downloadDocument(this.currentResultId, type);
        uni.hideLoading();
        
        if (result && (result.code === 0 || result.code === '0000' || result.code === 'SUCCESS')) {
          const downloadUrl = result.data?.download_url || result.data;
          if (downloadUrl) {
            this._downloadFileByUrl(downloadUrl, `文档.${type === 'pdf' ? 'pdf' : 'docx'}`);
          } else {
            uni.showToast({
              title: '下载链接获取失败',
              icon: 'none'
            });
          }
        } else {
          uni.showToast({
            title: result?.message || '获取下载链接失败',
            icon: 'none'
          });
        }
      } catch (error) {
        uni.hideLoading();
        console.error('下载失败:', error);
        uni.showToast({
          title: error.message || '下载失败',
          icon: 'none'
        });
      }
    },
    
    saveToHistory(resultData = {}) {
      const historyItem = {
        id: resultData?.id || this.currentResultId,
        title: `${this.selectedTemplate.name} - ${new Date().toLocaleDateString()}`,
        templateId: this.selectedTemplate.id,
        templateName: this.selectedTemplate.name,
        userInput: this.userInput,
        content: this.generatedContent,
        wordUrl: resultData?.word_url || null,
        pdfUrl: resultData?.pdf_url || null,
        timestamp: new Date().toISOString()
      };
      
      this.generationHistory.unshift(historyItem);
      
      if (this.generationHistory.length > 20) {
        this.generationHistory = this.generationHistory.slice(0, 20);
      }
      
      this.saveHistoryToStorage();
    },
    
    loadHistory() {
      docGenerateApi.getHistory()
        .then(res => {
          if (res.code === 0 || res.code === '0000' || res.code === 'SUCCESS') {
            this.generationHistory = res.data.map(item => ({
              id: item.id,
              title: item.template_name || '未命名文档',
              templateId: item.template_id,
              templateName: item.template_name,
              userInput: item.user_input,
              content: item.generated_content,
              wordUrl: item.word_url,
              pdfUrl: item.pdf_url,
              timestamp: item.created_at
            }));
          }
        })
        .catch(err => {
          console.error('加载历史失败:', err);
          const history = uni.getStorageSync('docGenerationHistory');
          if (history) {
            try {
              this.generationHistory = JSON.parse(history);
            } catch (e) {
              console.error('解析历史记录失败:', e);
            }
          }
        });
    },
    
    saveHistoryToStorage() {
      uni.setStorageSync('docGenerationHistory', JSON.stringify(this.generationHistory));
    },
    
    showHistory() {
      this.showHistoryPopup = true;
    },
    
    closeHistory() {
      this.showHistoryPopup = false;
    },
    
    useHistoryItem(item) {
      this.selectedTemplate = this.availableTemplates.find(t => t.id === item.templateId) || null;
      this.userInput = item.userInput;
      this.generatedContent = item.content;
      this.closeHistory();
    },
    
    async downloadHistoryDoc(item, type) {
      try {
        const directUrl = type === 'word' ? item.wordUrl : item.pdfUrl;
        if (directUrl) {
          this._downloadFileByUrl(directUrl, `文档.${type === 'pdf' ? 'pdf' : 'docx'}`);
          return;
        }
        
        if (!item.id) {
          uni.showToast({
            title: '该记录无法下载',
            icon: 'none'
          });
          return;
        }
        
        uni.showLoading({ title: '准备下载...' });
        
        const result = await docGenerateApi.downloadDocument(item.id, type);
        uni.hideLoading();
        
        if (result && (result.code === 0 || result.code === '0000' || result.code === 'SUCCESS')) {
          const downloadUrl = result.data?.download_url || result.data;
          if (downloadUrl) {
            this._downloadFileByUrl(downloadUrl, `文档.${type === 'pdf' ? 'pdf' : 'docx'}`);
          } else {
            uni.showToast({
              title: '下载链接获取失败',
              icon: 'none'
            });
          }
        } else {
          uni.showToast({
            title: result?.message || '获取下载链接失败',
            icon: 'none'
          });
        }
      } catch (error) {
        uni.hideLoading();
        console.error('下载失败:', error);
        uni.showToast({
          title: error.message || '下载失败',
          icon: 'none'
        });
      }
    },
    
    clearHistory() {
      uni.showModal({
        title: '确认清空',
        content: '确定要清空所有历史记录吗？',
        success: (res) => {
          if (res.confirm) {
            this.generationHistory = [];
            this.saveHistoryToStorage();
            this.closeHistory();
            uni.showToast({
              title: '已清空',
              icon: 'success'
            });
          }
        }
      });
    },
    
    _downloadFileByUrl(url, filename) {
      // #ifdef H5
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      // #endif
      
      // #ifndef H5
      uni.showLoading({ title: '下载中...' });
      uni.downloadFile({
        url: url,
        success: (res) => {
          uni.hideLoading();
          if (res.statusCode === 200) {
            uni.saveFile({
              tempFilePath: res.tempFilePath,
              success: (saveRes) => {
                uni.showToast({
                  title: '下载成功',
                  icon: 'success'
                });
                uni.openDocument({
                  filePath: saveRes.savedFilePath,
                  showMenu: true
                });
              },
              fail: () => {
                uni.openDocument({
                  filePath: res.tempFilePath,
                  showMenu: true
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
        fail: (err) => {
          uni.hideLoading();
          console.error('下载文件失败:', err);
          uni.showToast({
            title: '下载失败',
            icon: 'none'
          });
        }
      });
      // #endif
    },
    
    getTemplateIcon(type) {
      if (type === 'pdf') return '📕';
      if (type === 'word') return '📘';
      return '📄';
    },
    
    formatDate(timestamp) {
      const date = new Date(timestamp);
      const now = new Date();
      const diff = now - date;
      
      if (diff < 60000) return '刚刚';
      if (diff < 3600000) return Math.floor(diff / 60000) + '分钟前';
      if (diff < 86400000) return Math.floor(diff / 3600000) + '小时前';
      
      return date.toLocaleString('zh-CN', {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      });
    }
  }
}
</script>

<style scoped>
.doc-generate-page {
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

.navbar-left {
  display: flex;
  align-items: center;
}

.back-icon {
  font-size: 32px;
  color: #333;
  font-weight: 300;
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
.result-card {
  background: #fff;
  border-radius: 12px;
  padding: 15px;
  margin-bottom: 15px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-bottom: 12px;
  display: block;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.card-tip {
  font-size: 12px;
  color: #999;
}

.template-selector {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border: 1px solid #eee;
  border-radius: 8px;
  padding: 12px;
}

.selector-empty {
  flex: 1;
}

.selector-hint {
  color: #999;
  font-size: 14px;
}

.template-selected {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.template-icon {
  font-size: 32px;
}

.selector-arrow {
  font-size: 24px;
  color: #ddd;
}

.user-input {
  width: 100%;
  min-height: 120px;
  border: 1px solid #eee;
  border-radius: 8px;
  padding: 12px;
  font-size: 14px;
  line-height: 1.5;
  box-sizing: border-box;
}

.action-bar {
  margin: 20px 0;
}

.generate-btn {
  width: 100%;
  height: 44px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  border: none;
  border-radius: 22px;
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

.result-content {
  background: #f9f9f9;
  border-radius: 8px;
  padding: 12px;
  max-height: 300px;
  overflow-y: auto;
}

.result-text {
  font-size: 13px;
  color: #333;
  white-space: pre-wrap;
  word-break: break-all;
  line-height: 1.6;
}

.history-entry {
  background: #fff;
  border-radius: 12px;
  padding: 15px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.history-text {
  font-size: 15px;
  color: #333;
  font-weight: 500;
}

.history-arrow {
  font-size: 24px;
  color: #ddd;
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
  max-height: 85vh;
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

.template-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f9f9f9;
  border-radius: 10px;
  margin-bottom: 10px;
}

.item-icon {
  font-size: 32px;
}

.item-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.item-name {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.item-tag {
  font-size: 12px;
  color: #667eea;
  background: #f0f2ff;
  padding: 2px 8px;
  border-radius: 10px;
  align-self: flex-start;
}

.history-item {
  background: #f9f9f9;
  border-radius: 10px;
  padding: 12px;
  margin-bottom: 10px;
}

.history-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.history-title {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  flex: 1;
}

.history-time {
  font-size: 11px;
  color: #999;
}

.history-preview {
  background: #fff;
  border-radius: 6px;
  padding: 8px;
  margin-bottom: 8px;
}

.preview-text {
  font-size: 11px;
  color: #666;
  line-height: 1.4;
}

.history-actions {
  display: flex;
  gap: 8px;
}

.history-action-btn {
  flex: 1;
  padding: 6px 0;
  background: #f0f2f5;
  border: none;
  border-radius: 6px;
  font-size: 12px;
  color: #666;
  height: auto;
}

.popup-footer {
  padding: 15px 20px;
  display: flex;
  gap: 10px;
  border-top: 1px solid #f0f0f0;
}

.popup-btn {
  flex: 1;
  height: 40px;
  background: #f0f2f5;
  border: none;
  border-radius: 20px;
  font-size: 14px;
  color: #666;
  font-weight: 500;
}

.popup-btn.danger {
  background: #ffe5e5;
  color: #ff4444;
}

@media screen and (min-width: 768px) {
  .generate-container {
    padding: 30px;
    max-width: 720px;
  }
  
  .generate-btn:not(.btn-disabled):hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(102, 126, 234, 0.5);
  }
}
</style>