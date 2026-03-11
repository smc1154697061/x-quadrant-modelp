<template>
  <view class="extraction-page">
    <!-- 自定义导航栏 -->
    <view class="custom-navbar">
      <view class="navbar-left" @tap="goBack">
        <text class="back-icon">‹</text>
      </view>
      <view class="navbar-title">
        <text>内容提取</text>
      </view>
      <view class="navbar-right"></view>
    </view>
    
    <scroll-view class="content-scroll" scroll-y>
      <view class="extraction-container">
        <!-- 提示信息 -->
        <view class="info-card">
          <text class="info-icon">💡</text>
          <text class="info-text">上传文件并提供JSON模板，AI将智能提取结构化数据</text>
        </view>
        
        <!-- 文件上传区域 -->
        <view class="upload-card">
          <text class="card-title">选择文件</text>
          <view class="upload-zone" @tap="selectFile">
            <view v-if="!selectedFile" class="upload-empty">
              <text class="upload-icon">📁</text>
              <text class="upload-hint">点击选择文件</text>
              <text class="upload-support">支持图片、PDF、Word、TXT等</text>
            </view>
            <view v-else class="file-selected">
              <text class="file-icon">📄</text>
              <view class="file-detail">
                <text class="file-name">{{ selectedFile.name }}</text>
                <text class="file-size">{{ formatFileSize(selectedFile.size) }}</text>
              </view>
              <text class="remove-icon" @tap.stop="removeFile">×</text>
            </view>
          </view>
        </view>
        
        <!-- JSON模板区域 -->
        <view class="schema-card">
          <view class="card-header">
            <text class="card-title">JSON模板</text>
            <text class="card-tip" v-if="!schema">可选择示例快速开始</text>
          </view>
          
          <textarea 
            v-model="schema" 
            class="schema-input"
            placeholder='{"name": "", "age": "", "gender": ""}'
            :maxlength="-1"
          />
          
          <!-- 示例模板 -->
          <view v-if="!schema" class="example-chips">
            <view class="chip" @tap="useExample('person')">
              <text class="chip-text">个人信息</text>
            </view>
            <view class="chip" @tap="useExample('product')">
              <text class="chip-text">产品信息</text>
            </view>
            <view class="chip" @tap="useExample('article')">
              <text class="chip-text">文章摘要</text>
            </view>
          </view>
        </view>
        
        <!-- 提取按钮 -->
        <view class="action-bar">
          <button 
            class="extract-btn" 
            :class="{ 'btn-disabled': !canExtract }"
            :disabled="!canExtract"
            @tap="extractContent"
          >
            <text v-if="loading">提取中...</text>
            <text v-else>开始提取</text>
          </button>
        </view>
        
        <!-- 提取结果 -->
        <view v-if="resultJson" class="result-card">
          <view class="card-header">
            <text class="card-title">提取结果</text>
            <view class="result-actions">
              <button class="action-btn" @tap="copyResult">
                <text>复制</text>
              </button>
              <button class="action-btn" @tap="saveToHistory">
                <text>保存</text>
              </button>
            </view>
          </view>
          <view class="result-content">
            <text class="result-text">{{ prettyJson }}</text>
          </view>
        </view>
        
        <!-- 历史记录入口 -->
        <view v-if="historyCount > 0" class="history-entry" @tap="showHistory">
          <text class="history-text">历史记录 ({{ historyCount }})</text>
          <text class="history-arrow">›</text>
        </view>
      </view>
    </scroll-view>
    
    <!-- 历史记录弹窗 -->
    <view v-if="showHistoryPopup" class="popup-mask" @tap="closeHistory">
      <view class="popup-content" @tap.stop>
        <view class="popup-header">
          <text class="popup-title">历史记录</text>
          <text class="popup-close" @tap="closeHistory">×</text>
        </view>
        <scroll-view class="popup-scroll" scroll-y :style="{height: popupScrollHeight + 'px'}">
          <view v-if="extractionHistory.length === 0" class="empty-state">
            <text class="empty-icon">📭</text>
            <text class="empty-text">暂无历史记录</text>
          </view>
          <view v-else>
            <view 
              v-for="(item, index) in extractionHistory" 
              :key="index" 
              class="history-item"
              @tap="useHistoryItem(item)"
            >
              <view class="history-item-header">
                <text class="history-filename">{{ item.filename }}</text>
                <text class="history-time">{{ formatDate(item.timestamp) }}</text>
              </view>
              <view class="history-preview">
                <text class="preview-text">{{ formatJson(item.result).substring(0, 100) }}...</text>
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
import api from '../../../utils/api.js';

export default {
  data() {
    return {
      selectedFile: null,
      schema: '',
      loading: false,
      resultJson: null,
      extractionHistory: [],
      showHistoryPopup: false,
      windowHeight: 0,
      popupScrollHeight: 0,
      
      schemaExamples: {
        person: JSON.stringify({
          name: "",
          age: "",
          gender: "",
          occupation: "",
          email: "",
          phone: ""
        }, null, 2),
        product: JSON.stringify({
          product_name: "",
          price: "",
          category: "",
          description: "",
          features: []
        }, null, 2),
        article: JSON.stringify({
          title: "",
          author: "",
          date: "",
          summary: "",
          keywords: []
        }, null, 2)
      }
    };
  },
  
  computed: {
    canExtract() {
      return !this.loading && this.selectedFile && this.schema;
    },
    
    prettyJson() {
      if (!this.resultJson) return '';
      return JSON.stringify(this.resultJson, null, 2);
    },
    
    historyCount() {
      return this.extractionHistory.length;
    }
  },
  
  onLoad() {
    this.loadHistory();
    // 计算弹窗滚动区域高度，适配多端
    uni.getSystemInfo({
      success: (res) => {
        // 预留头部与底部按钮区域高度
        this.windowHeight = res.windowHeight || 600;
        const headerFooterReserve = 160; // 头部+底部+间距
        const maxPopupHeight = Math.floor(this.windowHeight * 0.8);
        this.popupScrollHeight = Math.max(200, maxPopupHeight - headerFooterReserve);
      }
    });
  },
  
  methods: {
    goBack() {
      uni.navigateBack();
    },
    
    selectFile() {
      uni.chooseImage({
        count: 1,
        success: (res) => {
          if (res.tempFilePaths && res.tempFilePaths.length > 0) {
            this.selectedFile = {
              path: res.tempFilePaths[0],
              name: res.tempFilePaths[0].substring(res.tempFilePaths[0].lastIndexOf('/') + 1) || '选中的文件',
              size: res.tempFiles && res.tempFiles[0] ? res.tempFiles[0].size : 0
            };
          }
        },
        fail: (err) => {
          if (!err.errMsg?.includes('cancel')) {
            uni.showToast({
              title: '选择文件失败',
              icon: 'none'
            });
          }
        }
      });
    },
    
    removeFile() {
      this.selectedFile = null;
    },
    
    useExample(type) {
      this.schema = this.schemaExamples[type];
    },
    
    async extractContent() {
      if (!this.canExtract) return;
      
      this.loading = true;
      this.resultJson = null;
      
      uni.showLoading({
        title: '提取中...',
        mask: true
      });
      
      const formData = { 
        schema: this.schema
      };
      
      try {
        const result = await api.upload('/llm/extract', this.selectedFile.path, formData);
        
        uni.hideLoading();
        
        if (result && (result.code === 0 || result.code === '0000' || result.code === 'SUCCESS')) {
          if (typeof result.data === 'string') {
            try {
              this.resultJson = JSON.parse(result.data);
            } catch (e) {
              console.error('[内容提取] 解析JSON失败:', e);
              this.resultJson = { error: '解析返回数据失败', raw: result.data };
            }
          } else if (result.data && typeof result.data === 'object') {
            this.resultJson = result.data;
          } else {
            this.resultJson = { error: '提取结果为空' };
          }
          
          if (this.resultJson && !this.resultJson.error) {
            uni.showToast({
              title: '提取成功',
              icon: 'success'
            });
          } else {
            uni.showToast({
              title: this.resultJson.error || '提取失败',
              icon: 'none'
            });
          }
        } else {
          const errorMsg = result?.message || result?.msg || result?.errMsg || '内容提取失败';
          this.resultJson = { error: errorMsg };
          uni.showToast({
            title: errorMsg,
            icon: 'none'
          });
        }
      } catch (error) {
        uni.hideLoading();
        console.error('[内容提取] 提取过程出错:', error);
        const errorMsg = error?.message || error?.msg || error?.errMsg || '系统错误';
        this.resultJson = { error: errorMsg };
        uni.showToast({
          title: errorMsg,
          icon: 'none'
        });
      } finally {
        this.loading = false;
      }
    },
    
    copyResult() {
      if (!this.resultJson) return;
      
      uni.setClipboardData({
        data: this.prettyJson,
        success: () => {
          uni.showToast({
            title: '已复制',
            icon: 'success'
          });
        }
      });
    },
    
    saveToHistory() {
      if (!this.resultJson || this.resultJson.error) return;
      
      const historyItem = {
        filename: this.selectedFile.name,
        schema: this.schema,
        result: this.resultJson,
        timestamp: new Date().toISOString()
      };
      
      this.extractionHistory.unshift(historyItem);
      
      if (this.extractionHistory.length > 20) {
        this.extractionHistory = this.extractionHistory.slice(0, 20);
      }
      
      this.saveHistoryToStorage();
      
      uni.showToast({
        title: '已保存到历史',
        icon: 'success'
      });
    },
    
    loadHistory() {
      const history = uni.getStorageSync('extractionHistory');
      if (history) {
        try {
          this.extractionHistory = JSON.parse(history);
        } catch (e) {
          console.error('解析历史记录失败:', e);
        }
      }
    },
    
    saveHistoryToStorage() {
      uni.setStorageSync('extractionHistory', JSON.stringify(this.extractionHistory));
    },
    
    showHistory() {
      this.showHistoryPopup = true;
    },
    
    closeHistory() {
      this.showHistoryPopup = false;
    },
    
    useHistoryItem(item) {
      this.schema = item.schema;
      this.resultJson = item.result;
      this.closeHistory();
      
      uni.showToast({
        title: '已加载历史记录',
        icon: 'success'
      });
    },
    
    clearHistory() {
      uni.showModal({
        title: '确认清空',
        content: '确定要清空所有历史记录吗？',
        success: (res) => {
          if (res.confirm) {
            this.extractionHistory = [];
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
    
    formatFileSize(bytes) {
      if (!bytes || bytes === 0) return '0 B';
      const k = 1024;
      const sizes = ['B', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
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
    },
    
    formatJson(json) {
      if (!json) return '';
      return JSON.stringify(json, null, 2);
    }
  }
}
</script>

<style scoped>
.extraction-page {
  width: 100%;
  height: 100vh;
  background: #f5f7fa;
  display: flex;
  flex-direction: column;
}

/* 自定义导航栏 */
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

/* 滚动内容 */
.content-scroll {
  flex: 1;
  height: 0;
}

.extraction-container {
  padding: 15px;
  max-width: 680px;
  margin: 0 auto;
}

/* 提示卡片 */
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

/* 卡片通用样式 */
.upload-card,
.schema-card,
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

/* 文件上传 */
.upload-zone {
  border: 2px dashed #ddd;
  border-radius: 8px;
  padding: 20px;
  text-align: center;
  transition: all 0.3s;
}

.upload-zone:active {
  border-color: #667eea;
  background: rgba(102, 126, 234, 0.05);
}

.upload-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.upload-icon {
  font-size: 40px;
  opacity: 0.6;
}

.upload-hint {
  font-size: 15px;
  color: #666;
  font-weight: 500;
}

.upload-support {
  font-size: 12px;
  color: #999;
}

.file-selected {
  display: flex;
  align-items: center;
  gap: 12px;
}

.file-icon {
  font-size: 32px;
}

.file-detail {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  text-align: left;
}

.file-name {
  font-size: 14px;
  color: #333;
  font-weight: 500;
}

.file-size {
  font-size: 12px;
  color: #999;
}

.remove-icon {
  font-size: 32px;
  color: #ff4444;
  font-weight: 300;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* JSON模板 */
.schema-input {
  width: 100%;
  min-height: 150px;
  border: 1px solid #eee;
  border-radius: 8px;
  padding: 12px;
  font-size: 13px;
  font-family: 'Courier New', monospace;
  background: #f9f9f9;
  box-sizing: border-box;
}

.example-chips {
  display: flex;
  gap: 8px;
  margin-top: 12px;
  flex-wrap: wrap;
}

.chip {
  padding: 6px 14px;
  background: #f0f2f5;
  border-radius: 20px;
  font-size: 12px;
  color: #666;
  transition: all 0.3s;
}

.chip:active {
  background: #667eea;
  color: #fff;
}

/* 操作按钮 */
.action-bar {
  margin: 20px 0;
}

.extract-btn {
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

.extract-btn.btn-disabled {
  background: #ddd;
  color: #999;
  box-shadow: none;
}

/* 提取结果 */
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
  font-size: 12px;
  font-family: 'Courier New', monospace;
  color: #333;
  white-space: pre-wrap;
  word-break: break-all;
}

/* 历史记录入口 */
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

/* 历史记录弹窗 */
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
  /* 高度通过内联样式动态设置，确保多端可滚动 */
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

.history-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.history-filename {
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
}

.preview-text {
  font-size: 11px;
  color: #666;
  font-family: 'Courier New', monospace;
  line-height: 1.4;
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

/* PC端适配 */
@media screen and (min-width: 768px) {
  .extraction-container {
    padding: 30px;
    max-width: 720px; /* PC端稍微放宽但仍居中窄栏显示 */
  }
  
  .upload-zone:hover {
    border-color: #667eea;
    background: rgba(102, 126, 234, 0.05);
  }
  
  .chip:hover {
    background: #667eea;
    color: #fff;
  }
  
  .extract-btn:not(.btn-disabled):hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(102, 126, 234, 0.5);
  }
}
</style>

