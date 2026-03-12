<template>
  <view class="watermark-page">
    <view class="custom-navbar">
      <view class="navbar-left" @tap="goBack">
        <text class="back-icon">‹</text>
      </view>
      <view class="navbar-title">
        <text>文档水印</text>
      </view>
      <view class="navbar-right"></view>
    </view>
    
    <scroll-view class="content-scroll" scroll-y>
      <view class="watermark-container">
        <view class="info-card">
          <text class="info-icon">💡</text>
          <text class="info-text">上传图片或PDF文件，添加自定义文字或图片水印后下载</text>
        </view>
        
        <view class="upload-card">
          <text class="card-title">选择文件</text>
          <view class="upload-zone" @tap="selectFile">
            <view v-if="!selectedFile" class="upload-empty">
              <text class="upload-icon">📁</text>
              <text class="upload-hint">点击选择文件</text>
              <text class="upload-support">支持图片、PDF格式</text>
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
        
        <view v-if="selectedFile" class="editor-card">
          <WatermarkEditor 
            :file="selectedFile" 
            @watermark-config-change="onWatermarkConfigChange"
          />
        </view>
        
        <view v-if="selectedFile" class="preview-card">
          <WatermarkPreview 
            :file="selectedFile" 
            :watermark-config="watermarkConfig"
            ref="previewRef"
          />
        </view>
        
        <view v-if="selectedFile" class="action-bar">
          <button class="download-btn" @tap="downloadResult">
            <text>下载带水印文件</text>
          </button>
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<script>
import { getPlatformType, platformUtils } from '../../../utils/platform-adapter.js';
import WatermarkEditor from './components/WatermarkEditor.vue';
import WatermarkPreview from './components/WatermarkPreview.vue';

export default {
  components: {
    WatermarkEditor,
    WatermarkPreview
  },
  data() {
    return {
      selectedFile: null,
      watermarkConfig: {
        type: 'text',
        text: '水印文字',
        image: null,
        opacity: 0.5,
        position: 'center',
        rotation: 0,
        fontSize: 30,
        color: '#000000',
        spacing: 100,
        repeat: false
      },
      isPc: false
    };
  },
  computed: {
    previewRef() {
      return this.$refs.previewRef;
    }
  },
  onLoad() {
    this.checkPlatform();
  },
  methods: {
    checkPlatform() {
      const platform = getPlatformType();
      this.isPc = platform === 'h5';
    },
    goBack() {
      uni.navigateBack();
    },
    selectFile() {
      const platform = getPlatformType();
      
      if (platform === 'h5') {
        uni.chooseFile({
          count: 1,
          extension: ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.pdf'],
          success: (res) => {
            if (res.tempFiles && res.tempFiles.length > 0) {
              const file = res.tempFiles[0];
              this.selectedFile = {
                path: file.path,
                name: file.name,
                size: file.size,
                type: this.getFileType(file.name)
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
      } else {
        uni.chooseImage({
          count: 1,
          success: (res) => {
            if (res.tempFilePaths && res.tempFilePaths.length > 0) {
              this.selectedFile = {
                path: res.tempFilePaths[0],
                name: res.tempFilePaths[0].substring(res.tempFilePaths[0].lastIndexOf('/') + 1) || '选中的图片',
                size: res.tempFiles && res.tempFiles[0] ? res.tempFiles[0].size : 0,
                type: 'image'
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
      }
    },
    getFileType(fileName) {
      const ext = fileName.split('.').pop().toLowerCase();
      const imageExts = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'];
      if (imageExts.includes(ext)) return 'image';
      if (ext === 'pdf') return 'pdf';
      return 'unknown';
    },
    removeFile() {
      this.selectedFile = null;
    },
    onWatermarkConfigChange(config) {
      this.watermarkConfig = { ...this.watermarkConfig, ...config };
    },
    downloadResult() {
      if (this.$refs.previewRef) {
        this.$refs.previewRef.exportImage();
      }
    },
    formatFileSize(bytes) {
      return platformUtils.formatFileSize(bytes);
    }
  }
}
</script>

<style scoped>
.watermark-page {
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

.watermark-container {
  padding: 15px;
  max-width: 680px;
  margin: 0 auto;
}

.info-card {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
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

.upload-card,
.editor-card,
.preview-card {
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

.upload-zone {
  border: 2px dashed #ddd;
  border-radius: 8px;
  padding: 20px;
  text-align: center;
  transition: all 0.3s;
}

.upload-zone:active {
  border-color: #f093fb;
  background: rgba(240, 147, 251, 0.05);
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

.action-bar {
  margin: 20px 0;
}

.download-btn {
  width: 100%;
  height: 44px;
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: #fff;
  border: none;
  border-radius: 22px;
  font-size: 16px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(240, 147, 251, 0.4);
}

@media screen and (min-width: 768px) {
  .watermark-container {
    padding: 30px;
    max-width: 720px;
  }
  
  .upload-zone:hover {
    border-color: #f093fb;
    background: rgba(240, 147, 251, 0.05);
  }
  
  .download-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(240, 147, 251, 0.5);
  }
}
</style>
