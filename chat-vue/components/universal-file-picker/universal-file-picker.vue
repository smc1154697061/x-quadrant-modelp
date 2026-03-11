<template>
  <view class="universal-file-picker">
    <button class="file-select-btn" @tap="selectFile">{{ buttonText }}</button>
    <view v-if="file" class="file-info">
      <text class="file-name">{{ file.name }}</text>
      <text class="file-size">({{ formatFileSize(file.size) }})</text>
    </view>
  </view>
</template>

<script>
import { getPlatformType, PLATFORM_TYPE } from '../../utils/platform-adapter.js';

export default {
  name: 'UniversalFilePicker',
  props: {
    buttonText: {
      type: String,
      default: '选择文件'
    },
    extensions: {
      type: Array,
      default: () => ['doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'pdf', 'txt', 'md']
    },
    count: {
      type: Number,
      default: 1
    }
  },
  data() {
    return {
      file: null,
      isSelecting: false
    };
  },
  methods: {
    // 选择文件，区分不同环境
    selectFile() {
      // 防止重复点击
      if (this.isSelecting) return;
      
      this.isSelecting = true;
      
      // 根据不同平台选择不同的文件选择方法
      const platform = getPlatformType();
      
      // 提示：暂时仅使用图片选择功能代替
      uni.showToast({
        title: '暂时使用图片选择功能',
        icon: 'none',
        duration: 1500
      });
      
      setTimeout(() => {
        this.chooseImageFallback();
      }, 500);
      
      /* 
      // 文件选择功能暂时注释，后续实现
      if (platform === PLATFORM_TYPE.MP_WEIXIN) {
        // 微信小程序环境
        this.selectFileInWx();
      } else if (platform === PLATFORM_TYPE.H5) {
        // H5环境
        this.selectFileInH5();
      } else if (platform === PLATFORM_TYPE.APP) {
        // App环境
        this.selectFileInApp();
      } else {
        // 默认使用图片选择作为降级方案
        this.chooseImageFallback();
      }
      */
    },
    
    // 使用图片选择作为降级方案
    chooseImageFallback() {
      uni.chooseImage({
        count: 1,
        success: (res) => {
          if (res.tempFilePaths && res.tempFilePaths.length > 0) {
            const path = res.tempFilePaths[0];
            const name = path.substring(path.lastIndexOf('/') + 1) || '图片文件.png';
            const size = res.tempFiles && res.tempFiles[0] ? res.tempFiles[0].size : 0;
            
            this.file = {
              path,
              name,
              size
            };
            
            this.$emit('file-selected', this.file);
          }
        },
        fail: (err) => {
          if (err && !err.errMsg?.includes('cancel')) {
            console.error('选择图片失败:', err);
            // 确保错误对象包含正确的属性
            const error = {
              message: err.errMsg || err.message || '选择图片失败',
              original: err
            };
            this.$emit('file-error', error);
            
            uni.showToast({
              title: '选择图片失败',
              icon: 'none'
            });
          }
        },
        complete: () => {
          this.isSelecting = false;
        }
      });
    },
    
    // 格式化文件大小
    formatFileSize(bytes) {
      if (!bytes || isNaN(bytes) || bytes === 0) return '0 B';
      
      const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
      const i = Math.floor(Math.log(bytes) / Math.log(1024));
      return (bytes / Math.pow(1024, i)).toFixed(2) + ' ' + sizes[i];
    }
  }
};
</script>

<style>
.universal-file-picker {
  display: flex;
  flex-direction: column;
  margin-bottom: 20rpx;
}

.file-select-btn {
  background-color: #f0f0f0;
  color: #333;
  padding: 8px 15px;
  border-radius: 6px;
  font-size: 14px;
  border: none;
  width: fit-content;
}

.file-info {
  margin-top: 10rpx;
  font-size: 14px;
  color: #666;
}

.file-name {
  word-break: break-all;
}

.file-size {
  margin-left: 10rpx;
}
</style> 