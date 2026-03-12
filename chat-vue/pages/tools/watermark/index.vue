<template>
  <view class="watermark-page">
    <view class="custom-navbar">
      <view class="navbar-left" @tap="goBack">
        <text class="back-icon">‹</text>
      </view>
      <view class="navbar-title">
        <text>文档水印工具</text>
      </view>
      <view class="navbar-right"></view>
    </view>
    
    <scroll-view class="content-scroll" scroll-y>
      <view class="watermark-container">
        <view class="info-card">
          <text class="info-icon">💧</text>
          <text class="info-text">上传图片，添加自定义水印后下载</text>
        </view>
        
        <view class="upload-card">
          <text class="card-title">选择文件</text>
          <view class="upload-zone" @tap="selectFile">
            <view v-if="!selectedFile" class="upload-empty">
              <text class="upload-icon">📁</text>
              <text class="upload-hint">点击选择文件</text>
              <text class="upload-support">支持图片(JPG/PNG)</text>
            </view>
            <view v-else class="file-selected">
              <text class="file-icon">{{ fileIcon }}</text>
              <view class="file-detail">
                <text class="file-name">{{ selectedFile.name }}</text>
                <text class="file-size">{{ formatFileSize(selectedFile.size) }}</text>
              </view>
              <text class="remove-icon" @tap.stop="removeFile">×</text>
            </view>
          </view>
        </view>
        
        <view v-if="selectedFile" class="editor-section">
          <watermark-editor
            ref="editorRef"
            :file-type="fileType"
            @update:config="onConfigUpdate"
          />
          
          <view class="generate-btn-wrapper">
            <button class="generate-btn" @tap="generatePreview">
              <text>生成预览</text>
            </button>
          </view>
        </view>
        
        <view v-if="showPreview" class="preview-section">
          <text class="section-title">预览效果</text>
          <watermark-preview
            ref="previewRef"
            :source-url="selectedFile.path"
            :watermark-config="watermarkConfig"
            :file-type="fileType"
            @preview-ready="onPreviewReady"
          />
        </view>
        
        <view v-if="canDownload" class="action-bar">
          <button class="download-btn" @tap="downloadFile">
            <text>下载水印文件</text>
          </button>
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<script>
import { getPlatformType, PLATFORM_TYPE } from '../../../utils/platform-adapter.js';
import WatermarkEditor from './WatermarkEditor.vue';
import WatermarkPreview from './WatermarkPreview.vue';

export default {
  components: {
    WatermarkEditor,
    WatermarkPreview
  },
  
  data() {
    return {
      selectedFile: null,
      watermarkConfig: null,
      previewUrl: null,
      canvasData: null,
      platform: '',
      showPreview: false
    };
  },
  
  computed: {
    fileType() {
      if (!this.selectedFile) return '';
      const name = this.selectedFile.name.toLowerCase();
      if (name.endsWith('.pdf')) return 'pdf';
      if (name.endsWith('.png')) return 'png';
      if (name.endsWith('.jpg') || name.endsWith('.jpeg')) return 'jpg';
      return 'image';
    },
    
    fileIcon() {
      if (this.fileType === 'pdf') return '📄';
      return '🖼️';
    },
    
    canDownload() {
      return this.canvasData && this.canvasData.url;
    }
  },
  
  onLoad() {
    this.platform = getPlatformType();
  },
  
  methods: {
    goBack() {
      uni.navigateBack();
    },
    
    selectFile() {
      const isH5 = this.platform === PLATFORM_TYPE.H5;
      
      if (isH5) {
        this.selectFileH5();
      } else {
        this.selectFileNative();
      }
    },
    
    selectFileH5() {
      const input = document.createElement('input');
      input.type = 'file';
      input.accept = 'image/*';
      input.onchange = (e) => {
        const file = e.target.files[0];
        if (file) {
          const url = URL.createObjectURL(file);
          this.selectedFile = {
            path: url,
            name: file.name,
            size: file.size,
            file: file
          };
          this.showPreview = false;
          this.previewUrl = null;
          this.canvasData = null;
        }
      };
      input.click();
    },
    
    selectFileNative() {
      uni.chooseImage({
        count: 1,
        sourceType: ['album', 'camera'],
        success: (res) => {
          if (res.tempFilePaths && res.tempFilePaths.length > 0) {
            const path = res.tempFilePaths[0];
            this.selectedFile = {
              path: path,
              name: path.substring(path.lastIndexOf('/') + 1) || 'image.jpg',
              size: res.tempFiles?.[0]?.size || 0
            };
            this.showPreview = false;
            this.previewUrl = null;
            this.canvasData = null;
          }
        },
        fail: (err) => {
          if (!err.errMsg?.includes('cancel')) {
            uni.showToast({ title: '选择文件失败', icon: 'none' });
          }
        }
      });
    },
    
    removeFile() {
      if (this.selectedFile?.path?.startsWith('blob:')) {
        URL.revokeObjectURL(this.selectedFile.path);
      }
      this.selectedFile = null;
      this.showPreview = false;
      this.previewUrl = null;
      this.canvasData = null;
    },
    
    onConfigUpdate(config) {
      this.watermarkConfig = config;
    },
    
    generatePreview() {
      if (!this.selectedFile || !this.watermarkConfig) {
        uni.showToast({ title: '请先选择文件', icon: 'none' });
        return;
      }
      
      if (this.watermarkConfig.type === 'text' && !this.watermarkConfig.text) {
        uni.showToast({ title: '请输入水印文字', icon: 'none' });
        return;
      }
      
      if (this.watermarkConfig.type === 'image' && !this.watermarkConfig.imageUrl) {
        uni.showToast({ title: '请选择水印图片', icon: 'none' });
        return;
      }
      
      this.showPreview = true;
      this.canvasData = null;
      
      this.$nextTick(() => {
        if (this.$refs.previewRef) {
          this.$refs.previewRef.loadSourceImage();
        }
      });
    },
    
    onPreviewReady(data) {
      this.canvasData = data;
      this.previewUrl = data.url;
    },
    
    async downloadFile() {
      if (!this.canvasData || !this.canvasData.url) {
        uni.showToast({ title: '请先生成预览', icon: 'none' });
        return;
      }
      
      const isH5 = this.platform === PLATFORM_TYPE.H5;
      
      if (isH5) {
        this.downloadH5();
      } else {
        this.downloadNative();
      }
    },
    
    downloadH5() {
      try {
        const link = document.createElement('a');
        const fileName = this.selectedFile?.name || 'image.png';
        link.download = `watermarked_${fileName}`;
        link.href = this.canvasData.url;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        uni.showToast({ title: '下载成功', icon: 'success' });
      } catch (e) {
        console.error('下载失败:', e);
        uni.showToast({ title: '下载失败', icon: 'none' });
      }
    },
    
    async downloadNative() {
      try {
        uni.showLoading({ title: '保存中...', mask: true });
        
        const base64 = this.canvasData.base64;
        if (!base64) {
          uni.hideLoading();
          uni.showToast({ title: '数据无效', icon: 'none' });
          return;
        }
        
        const filePath = `${wx.env.USER_DATA_PATH}/watermarked_${Date.now()}.png`;
        
        const fs = uni.getFileSystemManager();
        const base64Data = base64.replace(/^data:image\/\w+;base64,/, '');
        const buffer = uni.base64ToArrayBuffer(base64Data);
        
        fs.writeFile({
          filePath: filePath,
          data: buffer,
          encoding: 'binary',
          success: () => {
            uni.saveImageToPhotosAlbum({
              filePath: filePath,
              success: () => {
                uni.hideLoading();
                uni.showToast({ title: '已保存到相册', icon: 'success' });
              },
              fail: (err) => {
                uni.hideLoading();
                if (err.errMsg?.includes('auth deny')) {
                  uni.showModal({
                    title: '提示',
                    content: '需要授权保存图片到相册',
                    success: (res) => {
                      if (res.confirm) {
                        uni.openSetting({});
                      }
                    }
                  });
                } else {
                  uni.showToast({ title: '保存失败', icon: 'none' });
                }
              }
            });
          },
          fail: () => {
            uni.hideLoading();
            uni.showToast({ title: '保存失败', icon: 'none' });
          }
        });
      } catch (e) {
        uni.hideLoading();
        uni.showToast({ title: '保存失败', icon: 'none' });
      }
    },
    
    formatFileSize(bytes) {
      if (!bytes || bytes === 0) return '0 B';
      const k = 1024;
      const sizes = ['B', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
  }
};
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
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
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

.upload-card {
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
  border-color: #4facfe;
  background: rgba(79, 172, 254, 0.05);
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

.editor-section,
.preview-section {
  background: #fff;
  border-radius: 12px;
  padding: 15px;
  margin-bottom: 15px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-bottom: 12px;
  display: block;
}

.generate-btn-wrapper {
  margin-top: 20px;
  padding-top: 15px;
  border-top: 1px solid #f0f0f0;
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

.action-bar {
  margin: 20px 0;
}

.download-btn {
  width: 100%;
  height: 44px;
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  color: #fff;
  border: none;
  border-radius: 22px;
  font-size: 16px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(79, 172, 254, 0.4);
}

@media screen and (min-width: 768px) {
  .watermark-container {
    padding: 30px;
    max-width: 720px;
  }
  
  .upload-zone:hover {
    border-color: #4facfe;
    background: rgba(79, 172, 254, 0.05);
  }
  
  .download-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(79, 172, 254, 0.5);
  }
}
</style>
