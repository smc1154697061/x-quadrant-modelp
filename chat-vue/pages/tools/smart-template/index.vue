<template>
  <app-layout ref="appLayout" title="智能模板" :showBack="true">
    <view class="smart-template-container">
      <!-- 顶部标签栏 -->
      <view class="tab-bar">
        <view 
          v-for="tab in tabs" 
          :key="tab.key"
          class="tab-item"
          :class="{ active: currentTab === tab.key }"
          @tap="switchTab(tab.key)"
        >
          <text class="tab-icon">{{ tab.icon }}</text>
          <text class="tab-text">{{ tab.name }}</text>
        </view>
      </view>
      
      <!-- 内容区域 -->
      <view class="tab-content">
        <!-- 文档生成 -->
        <view v-if="currentTab === 'generate'" class="panel">
          <template-generate-panel 
            ref="generatePanel"
            @goToManage="switchTab('manage')"
            @viewResult="viewResult"
          />
        </view>
        
        <!-- 模板管理 -->
        <view v-if="currentTab === 'manage'" class="panel">
          <template-manage-panel 
            ref="managePanel"
            @templateUploaded="onTemplateUploaded"
          />
        </view>
        
        <!-- 历史记录 -->
        <view v-if="currentTab === 'history'" class="panel">
          <template-history-panel 
            ref="historyPanel"
            @viewDetail="viewHistoryDetail"
          />
        </view>
      </view>
    </view>
    
    <!-- 生成结果弹窗 -->
    <uni-popup ref="resultPopup" type="center" :maskClick="false">
      <view class="result-modal">
        <view class="modal-header">
          <text class="modal-title">生成结果</text>
          <text class="modal-close" @tap="closeResultModal">×</text>
        </view>
        <view class="modal-body">
          <scroll-view scroll-y class="result-content">
            <text class="result-text">{{ currentResult?.content || '' }}</text>
          </scroll-view>
        </view>
        <view class="modal-footer">
          <view class="btn secondary" @tap="copyResultContent">复制内容</view>
          <view class="btn primary" @tap="showDownloadOptions">下载文档</view>
        </view>
      </view>
    </uni-popup>
    
    <!-- 下载格式选择弹窗 -->
    <uni-popup ref="downloadPopup" type="bottom">
      <view class="download-modal">
        <view class="download-title">选择下载格式</view>
        <view class="download-options">
          <view class="download-option" @tap="downloadAs('word')">
            <text class="option-icon">📄</text>
            <text class="option-text">Word文档 (.docx)</text>
          </view>
          <view class="download-option" @tap="downloadAs('pdf')">
            <text class="option-icon">📕</text>
            <text class="option-text">PDF文档 (.pdf)</text>
          </view>
        </view>
        <view class="download-cancel" @tap="closeDownloadModal">取消</view>
      </view>
    </uni-popup>
  </app-layout>
</template>

<script>
import AppLayout from '../../../components/layout/AppLayout.vue';
import TemplateGeneratePanel from './components/GeneratePanel.vue';
import TemplateManagePanel from './components/ManagePanel.vue';
import TemplateHistoryPanel from './components/HistoryPanel.vue';
import api from '../../../utils/api';
import router from '../../../utils/router.js';

export default {
  components: {
    AppLayout,
    TemplateGeneratePanel,
    TemplateManagePanel,
    TemplateHistoryPanel
  },
  data() {
    return {
      currentTab: 'generate',
      tabs: [
        { key: 'generate', name: '文档生成', icon: '✨' },
        { key: 'manage', name: '模板管理', icon: '📁' },
        { key: 'history', name: '历史记录', icon: '📋' }
      ],
      currentResult: null,
      currentGenerationId: null
    };
  },
  onLoad(options) {
    if (options.tab) {
      this.currentTab = options.tab;
    }
    if (this.$refs.appLayout) {
      this.$refs.appLayout.goBack = () => router.navigateBack();
    }
  },
  onBackPress() {
    router.navigateBack();
    return true;
  },
  mounted() {
    if (this.$refs.appLayout) {
      this.$refs.appLayout.goBack = () => router.navigateBack();
    }
  },
  methods: {
    switchTab(tab) {
      this.currentTab = tab;
      // 切换到历史记录时刷新数据
      if (tab === 'history' && this.$refs.historyPanel) {
        this.$refs.historyPanel.refresh();
      }
      // 切换到模板管理时刷新数据
      if (tab === 'manage' && this.$refs.managePanel) {
        this.$refs.managePanel.refresh();
      }
      // 切换到文档生成时刷新模板列表
      if (tab === 'generate' && this.$refs.generatePanel) {
        this.$refs.generatePanel.refreshTemplates();
      }
    },
    
    onTemplateUploaded() {
      // 模板上传成功后，刷新生成面板的模板列表
      if (this.$refs.generatePanel) {
        this.$refs.generatePanel.refreshTemplates();
      }
    },
    
    viewResult(result) {
      this.currentResult = result;
      this.currentGenerationId = result.generation_id;
      this.$refs.resultPopup.open();
    },
    
    viewHistoryDetail(generation) {
      this.currentResult = {
        content: generation.generated_content,
        template_name: generation.template_name
      };
      this.currentGenerationId = generation.id;
      this.$refs.resultPopup.open();
    },
    
    closeResultModal() {
      this.$refs.resultPopup.close();
    },
    
    copyResultContent() {
      if (!this.currentResult?.content) return;
      
      uni.setClipboardData({
        data: this.currentResult.content,
        success: () => {
          uni.showToast({ title: '已复制到剪贴板', icon: 'success' });
        }
      });
    },
    
    showDownloadOptions() {
      this.$refs.downloadPopup.open();
    },
    
    closeDownloadModal() {
      this.$refs.downloadPopup.close();
    },
    
    async downloadAs(format) {
      this.closeDownloadModal();
      
      if (!this.currentGenerationId) {
        uni.showToast({ title: '无法下载', icon: 'none' });
        return;
      }
      
      uni.showLoading({ title: '准备下载...' });
      
      try {
        const token = uni.getStorageSync('token');
        const baseUrl = api.baseUrl || '';
        const downloadUrl = `${baseUrl}/llm/generations/${this.currentGenerationId}/export?format=${format}`;
        
        // #ifdef H5
        const response = await fetch(downloadUrl, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (!response.ok) {
          throw new Error('下载失败');
        }
        
        const contentDisposition = response.headers.get('content-disposition');
        let fileName = this.currentResult?.template_name || '文档';
        if (contentDisposition) {
          const match = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
          if (match && match[1]) {
            fileName = decodeURIComponent(match[1].replace(/['"]/g, ''));
          }
        }
        if (!fileName.includes('.')) {
          fileName += format === 'word' ? '.docx' : '.pdf';
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = fileName;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        uni.hideLoading();
        uni.showToast({ title: '下载成功', icon: 'success' });
        // #endif
        
        // #ifndef H5
        uni.downloadFile({
          url: downloadUrl,
          header: {
            'Authorization': `Bearer ${token}`
          },
          success: (res) => {
            if (res.statusCode === 200) {
              uni.saveFile({
                tempFilePath: res.tempFilePath,
                success: () => {
                  uni.hideLoading();
                  uni.showToast({ title: '下载成功', icon: 'success' });
                },
                fail: () => {
                  uni.openDocument({
                    filePath: res.tempFilePath,
                    success: () => uni.hideLoading(),
                    fail: () => {
                      uni.hideLoading();
                      uni.showToast({ title: '打开文件失败', icon: 'none' });
                    }
                  });
                }
              });
            } else {
              uni.hideLoading();
              uni.showToast({ title: '下载失败', icon: 'none' });
            }
          },
          fail: () => {
            uni.hideLoading();
            uni.showToast({ title: '下载失败', icon: 'none' });
          }
        });
        // #endif
      } catch (e) {
        console.error('下载失败:', e);
        uni.hideLoading();
        uni.showToast({ title: '下载失败', icon: 'none' });
      }
    }
  }
};
</script>

<style scoped>
.smart-template-container {
  min-height: 100vh;
  background-color: #f5f7fa;
  display: flex;
  flex-direction: column;
}

/* 标签栏 */
.tab-bar {
  display: flex;
  background: #fff;
  padding: 0 20rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.08);
  position: sticky;
  top: 0;
  z-index: 100;
}

.tab-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 24rpx 0;
  position: relative;
  transition: all 0.3s;
}

.tab-item.active {
  color: #007bff;
}

.tab-item.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 60rpx;
  height: 4rpx;
  background: #007bff;
  border-radius: 2rpx;
}

.tab-icon {
  font-size: 36rpx;
  margin-bottom: 8rpx;
}

.tab-text {
  font-size: 26rpx;
  font-weight: 500;
}

/* 内容区域 */
.tab-content {
  flex: 1;
  overflow: hidden;
}

.panel {
  height: 100%;
}

/* 结果弹窗 */
.result-modal {
  width: 90vw;
  max-width: 700px;
  max-height: 80vh;
  background: #fff;
  border-radius: 20rpx;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 30rpx;
  border-bottom: 1rpx solid #eee;
}

.modal-title {
  font-size: 34rpx;
  font-weight: 600;
  color: #333;
}

.modal-close {
  font-size: 48rpx;
  color: #999;
  line-height: 1;
}

.modal-body {
  flex: 1;
  overflow: hidden;
  padding: 20rpx 30rpx;
}

.result-content {
  height: 50vh;
}

.result-text {
  font-size: 28rpx;
  line-height: 1.8;
  color: #333;
  white-space: pre-wrap;
}

.modal-footer {
  display: flex;
  gap: 20rpx;
  padding: 20rpx 30rpx 30rpx;
  border-top: 1rpx solid #eee;
}

.btn {
  flex: 1;
  height: 80rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12rpx;
  font-size: 28rpx;
  font-weight: 500;
}

.btn.primary {
  background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
  color: #fff;
}

.btn.secondary {
  background: #f5f7fa;
  color: #666;
}

/* 下载弹窗 */
.download-modal {
  background: #fff;
  border-radius: 24rpx 24rpx 0 0;
  padding: 30rpx;
  padding-bottom: calc(30rpx + env(safe-area-inset-bottom));
}

.download-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
  text-align: center;
  margin-bottom: 30rpx;
}

.download-options {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.download-option {
  display: flex;
  align-items: center;
  gap: 20rpx;
  padding: 30rpx;
  background: #f5f7fa;
  border-radius: 16rpx;
}

.option-icon {
  font-size: 40rpx;
}

.option-text {
  font-size: 30rpx;
  color: #333;
}

.download-cancel {
  margin-top: 20rpx;
  padding: 30rpx;
  text-align: center;
  font-size: 30rpx;
  color: #666;
  background: #f5f7fa;
  border-radius: 16rpx;
}
</style>
