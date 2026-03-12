<template>
  <view class="watermark-page">
    <!-- 自定义导航栏 -->
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
        <!-- 提示信息 -->
        <view class="info-card">
          <text class="info-icon">💧</text>
          <text class="info-text">上传图片添加文字或图片水印，支持透明度、位置、旋转等自定义设置</text>
        </view>
        
        <!-- 文件上传区域 -->
        <view class="upload-card">
          <text class="card-title">选择图片</text>
          <view class="upload-zone" @tap="selectFile">
            <view v-if="!originalFile" class="upload-empty">
              <text class="upload-icon">📁</text>
              <text class="upload-hint">点击选择图片</text>
              <text class="upload-support">支持 JPG、PNG 格式</text>
            </view>
            <view v-else class="file-selected">
              <text class="file-icon">🖼️</text>
              <view class="file-detail">
                <text class="file-name">{{ originalFile.name }}</text>
                <text class="file-size">{{ formatFileSize(originalFile.size) }}</text>
              </view>
              <text class="remove-icon" @tap.stop="removeFile">×</text>
            </view>
          </view>
        </view>
        
        <!-- 水印编辑器 -->
        <view class="editor-card">
          <text class="card-title">水印设置</text>
          <WatermarkEditor v-model="watermarkConfig" @change="onConfigChange" />
        </view>
        
        <!-- 预览区域 -->
        <view class="preview-card">
          <WatermarkPreview 
            :original-file="originalFile" 
            :watermark-config="watermarkConfig"
          />
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<script>
import WatermarkEditor from './WatermarkEditor.vue';
import WatermarkPreview from './WatermarkPreview.vue';
import { platformUtils } from '../../../utils/platform-adapter.js';

export default {
  components: {
    WatermarkEditor,
    WatermarkPreview
  },
  
  data() {
    return {
      originalFile: null,
      watermarkConfig: {
        type: 'text',
        text: {
          content: '水印文字',
          fontSize: 24,
          color: '#000000'
        },
        image: {
          src: '',
          width: 100,
          height: 0
        },
        position: 'center',
        customPosition: {
          x: 50,
          y: 50
        },
        opacity: 0.5,
        rotation: 0,
        isTiled: false,
        tileGap: 50
      }
    };
  },
  
  methods: {
    goBack() {
      uni.navigateBack();
    },
    
    selectFile() {
      uni.chooseImage({
        count: 1,
        sizeType: ['original', 'compressed'],
        sourceType: ['album', 'camera'],
        success: (res) => {
          if (res.tempFilePaths && res.tempFilePaths.length > 0) {
            const tempPath = res.tempFilePaths[0];
            const tempFile = res.tempFiles && res.tempFiles[0];
            
            this.originalFile = {
              path: tempPath,
              name: platformUtils.getFileNameFromPath(tempPath),
              size: tempFile ? tempFile.size : 0
            };
          }
        },
        fail: (err) => {
          if (!err.errMsg?.includes('cancel')) {
            uni.showToast({
              title: '选择图片失败',
              icon: 'none'
            });
          }
        }
      });
    },
    
    removeFile() {
      this.originalFile = null;
    },
    
    onConfigChange(config) {
      this.watermarkConfig = config;
    },
    
    formatFileSize(bytes) {
      return platformUtils.formatFileSize(bytes);
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

.watermark-container {
  padding: 15px;
  max-width: 680px;
  margin: 0 auto;
}

/* 提示卡片 */
.info-card {
  background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
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

/* 文件上传 */
.upload-zone {
  border: 2px dashed #ddd;
  border-radius: 8px;
  padding: 20px;
  text-align: center;
  transition: all 0.3s;
}

.upload-zone:active {
  border-color: #11998e;
  background: rgba(17, 153, 142, 0.05);
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

/* 编辑器卡片 */
.editor-card {
  padding: 0;
  overflow: hidden;
}

.editor-card .card-title {
  padding: 15px 15px 0 15px;
}

/* 预览卡片 */
.preview-card {
  padding: 0;
  overflow: hidden;
}

/* PC端适配 */
@media screen and (min-width: 768px) {
  .watermark-container {
    padding: 30px;
    max-width: 720px;
  }
  
  .upload-zone:hover {
    border-color: #11998e;
    background: rgba(17, 153, 142, 0.05);
  }
}
</style>
