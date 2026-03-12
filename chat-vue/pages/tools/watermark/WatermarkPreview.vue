<template>
  <view class="watermark-preview">
    <view class="preview-header">
      <text class="preview-title">预览效果</text>
      <text v-if="originalFile" class="file-info">{{ originalFile.name }}</text>
    </view>
    
    <view class="preview-container">
      <!-- 使用条件渲染确保 Canvas 在尺寸确定后才创建 -->
      <canvas 
        v-if="originalFile && canvasReady"
        :canvas-id="canvasId"
        class="preview-canvas"
        :style="{ width: canvasWidth + 'px', height: canvasHeight + 'px' }"
      />
      <view v-else-if="originalFile && !canvasReady" class="loading-preview">
        <text class="loading-text">加载中...</text>
      </view>
      <view v-else class="empty-preview">
        <text class="empty-icon">🖼️</text>
        <text class="empty-text">请先上传图片或PDF</text>
      </view>
    </view>
    
    <view v-if="originalFile && canvasReady" class="preview-actions">
      <button 
        class="action-btn primary" 
        :disabled="isProcessing"
        @tap="downloadResult"
      >
        <text v-if="isProcessing">处理中...</text>
        <text v-else>下载结果</text>
      </button>
    </view>
  </view>
</template>

<script>
import { getPlatformType, PLATFORM_TYPE } from '../../../utils/platform-adapter.js';

export default {
  name: 'WatermarkPreview',
  
  props: {
    originalFile: {
      type: Object,
      default: null
    },
    watermarkConfig: {
      type: Object,
      default: () => ({})
    }
  },
  
  data() {
    return {
      canvasId: 'watermarkCanvas',
      canvasWidth: 300,
      canvasHeight: 300,
      isProcessing: false,
      platform: '',
      imageInfo: null,
      canvasReady: false,
      drawTimeout: null
    };
  },
  
  watch: {
    originalFile: {
      immediate: true,
      handler(newVal, oldVal) {
        // 只有当文件真正改变时才重新加载
        if (newVal && newVal.path && (!oldVal || newVal.path !== oldVal.path)) {
          this.canvasReady = false;
          this.loadImageInfo();
        }
      }
    },
    watermarkConfig: {
      deep: true,
      handler() {
        if (this.originalFile && this.canvasReady) {
          this.debouncedDraw();
        }
      }
    }
  },
  
  mounted() {
    this.platform = getPlatformType();
  },
  
  beforeDestroy() {
    if (this.drawTimeout) {
      clearTimeout(this.drawTimeout);
    }
  },
  
  methods: {
    loadImageInfo() {
      if (!this.originalFile || !this.originalFile.path) return;
      
      uni.getImageInfo({
        src: this.originalFile.path,
        success: (res) => {
          this.imageInfo = res;
          
          // 限制最大尺寸，避免 Canvas 过大导致性能问题
          const maxCanvasSize = 2048;
          let targetWidth = res.width;
          let targetHeight = res.height;
          
          if (res.width > maxCanvasSize || res.height > maxCanvasSize) {
            const ratio = res.width / res.height;
            if (ratio > 1) {
              targetWidth = maxCanvasSize;
              targetHeight = Math.round(maxCanvasSize / ratio);
            } else {
              targetHeight = maxCanvasSize;
              targetWidth = Math.round(maxCanvasSize * ratio);
            }
          }
          
          this.canvasWidth = targetWidth;
          this.canvasHeight = targetHeight;
          
          // 先让 Canvas 创建出来
          this.$nextTick(() => {
            this.canvasReady = true;
            // Canvas 创建后再绘制
            this.$nextTick(() => {
              setTimeout(() => {
                this.drawWatermark();
              }, 50);
            });
          });
        },
        fail: (err) => {
          console.error('[水印预览] 获取图片信息失败:', err);
          uni.showToast({
            title: '加载图片失败',
            icon: 'none'
          });
        }
      });
    },
    
    debouncedDraw() {
      if (this.drawTimeout) {
        clearTimeout(this.drawTimeout);
      }
      this.drawTimeout = setTimeout(() => {
        this.drawWatermark();
      }, 100);
    },
    
    async drawWatermark() {
      if (!this.canvasReady || !this.originalFile) return;
      
      this.isProcessing = true;
      
      try {
        const ctx = uni.createCanvasContext(this.canvasId, this);
        const config = this.watermarkConfig;
        
        if (!config || !config.type) {
          this.isProcessing = false;
          return;
        }
        
        // 清空画布
        ctx.clearRect(0, 0, this.canvasWidth, this.canvasHeight);
        
        // 绘制原图 - 使用原始文件路径
        ctx.drawImage(this.originalFile.path, 0, 0, this.canvasWidth, this.canvasHeight);
        
        // 设置透明度
        ctx.globalAlpha = config.opacity || 0.5;
        
        if (config.isTiled) {
          // 平铺模式
          await this.drawTiledWatermark(ctx, config);
        } else {
          // 单水印模式
          await this.drawSingleWatermark(ctx, config);
        }
        
        // 绘制到画布
        ctx.draw(false, () => {
          this.isProcessing = false;
        });
      } catch (error) {
        console.error('[水印预览] 绘制水印失败:', error);
        this.isProcessing = false;
      }
    },
    
    async drawSingleWatermark(ctx, config) {
      const { x, y } = this.calculatePosition(config);
      
      ctx.save();
      ctx.translate(x, y);
      ctx.rotate((config.rotation || 0) * Math.PI / 180);
      
      if (config.type === 'text') {
        this.drawTextWatermark(ctx, config.text, 0, 0);
      } else if (config.type === 'image' && config.image && config.image.src) {
        await this.drawImageWatermark(ctx, config.image, 0, 0);
      }
      
      ctx.restore();
    },
    
    async drawTiledWatermark(ctx, config) {
      const gap = config.tileGap || 50;
      let watermarkWidth, watermarkHeight;
      
      if (config.type === 'text') {
        const fontSize = config.text?.fontSize || 24;
        const content = config.text?.content || '水印';
        watermarkWidth = fontSize * content.length * 0.6;
        watermarkHeight = fontSize * 1.5;
      } else {
        watermarkWidth = config.image?.width || 100;
        watermarkHeight = config.image?.height || 50;
      }
      
      const stepX = watermarkWidth + gap;
      const stepY = watermarkHeight + gap;
      
      // 预加载图片水印（如果是图片类型）
      let watermarkImagePath = null;
      if (config.type === 'image' && config.image && config.image.src) {
        watermarkImagePath = config.image.src;
      }
      
      // 对角线平铺
      for (let row = -1; row < Math.ceil(this.canvasHeight / stepY) + 1; row++) {
        for (let col = -1; col < Math.ceil(this.canvasWidth / stepX) + 1; col++) {
          const x = col * stepX + stepX / 2;
          const y = row * stepY + stepY / 2;
          
          ctx.save();
          ctx.translate(x, y);
          ctx.rotate((config.rotation || 0) * Math.PI / 180);
          
          if (config.type === 'text') {
            this.drawTextWatermark(ctx, config.text, 0, 0);
          } else if (watermarkImagePath) {
            const width = config.image?.width || 100;
            const height = config.image?.height || 50;
            ctx.drawImage(watermarkImagePath, -width / 2, -height / 2, width, height);
          }
          
          ctx.restore();
        }
      }
    },
    
    drawTextWatermark(ctx, textConfig, x, y) {
      const config = textConfig || {};
      const content = config.content || '水印';
      const fontSize = config.fontSize || 24;
      const color = config.color || '#000000';
      
      ctx.font = `bold ${fontSize}px sans-serif`;
      ctx.fillStyle = color;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      
      // 添加文字阴影增强可读性
      ctx.shadowColor = 'rgba(255, 255, 255, 0.5)';
      ctx.shadowBlur = 4;
      ctx.fillText(content, x, y);
      ctx.shadowBlur = 0;
    },
    
    async drawImageWatermark(ctx, imageConfig, x, y) {
      const config = imageConfig || {};
      if (!config.src) return;
      
      const width = config.width || 100;
      const height = config.height || width;
      
      ctx.drawImage(config.src, x - width / 2, y - height / 2, width, height);
    },
    
    calculatePosition(config) {
      const position = config.position || 'center';
      const padding = 40;
      let x = this.canvasWidth / 2;
      let y = this.canvasHeight / 2;
      
      switch (position) {
        case 'top-left':
          x = padding;
          y = padding;
          break;
        case 'top-center':
          x = this.canvasWidth / 2;
          y = padding;
          break;
        case 'top-right':
          x = this.canvasWidth - padding;
          y = padding;
          break;
        case 'center-left':
          x = padding;
          y = this.canvasHeight / 2;
          break;
        case 'center':
          x = this.canvasWidth / 2;
          y = this.canvasHeight / 2;
          break;
        case 'center-right':
          x = this.canvasWidth - padding;
          y = this.canvasHeight / 2;
          break;
        case 'bottom-left':
          x = padding;
          y = this.canvasHeight - padding;
          break;
        case 'bottom-center':
          x = this.canvasWidth / 2;
          y = this.canvasHeight - padding;
          break;
        case 'bottom-right':
          x = this.canvasWidth - padding;
          y = this.canvasHeight - padding;
          break;
        case 'custom':
          const customPos = config.customPosition || { x: 50, y: 50 };
          x = (customPos.x / 100) * this.canvasWidth;
          y = (customPos.y / 100) * this.canvasHeight;
          break;
      }
      
      return { x, y };
    },
    
    downloadResult() {
      if (this.isProcessing || !this.canvasReady) return;
      
      this.isProcessing = true;
      
      uni.canvasToTempFilePath({
        canvasId: this.canvasId,
        x: 0,
        y: 0,
        width: this.canvasWidth,
        height: this.canvasHeight,
        destWidth: this.canvasWidth,
        destHeight: this.canvasHeight,
        fileType: 'png',
        quality: 1,
        success: (res) => {
          this.saveFile(res.tempFilePath);
        },
        fail: (err) => {
          console.error('[水印预览] 导出图片失败:', err);
          uni.showToast({
            title: '导出失败',
            icon: 'none'
          });
          this.isProcessing = false;
        }
      }, this);
    },
    
    saveFile(tempFilePath) {
      const platform = getPlatformType();
      
      if (platform === PLATFORM_TYPE.H5) {
        this.downloadInH5(tempFilePath);
      } else {
        this.saveToAlbum(tempFilePath);
      }
    },
    
    downloadInH5(tempFilePath) {
      fetch(tempFilePath)
        .then(res => res.blob())
        .then(blob => {
          const url = URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          link.download = `watermarked_${Date.now()}.png`;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          URL.revokeObjectURL(url);
          
          uni.showToast({
            title: '下载成功',
            icon: 'success'
          });
        })
        .catch(err => {
          console.error('[水印预览] H5下载失败:', err);
          uni.showToast({
            title: '下载失败',
            icon: 'none'
          });
        })
        .finally(() => {
          this.isProcessing = false;
        });
    },
    
    saveToAlbum(tempFilePath) {
      uni.saveImageToPhotosAlbum({
        filePath: tempFilePath,
        success: () => {
          uni.showToast({
            title: '已保存到相册',
            icon: 'success'
          });
        },
        fail: (err) => {
          console.error('[水印预览] 保存到相册失败:', err);
          if (err.errMsg && err.errMsg.includes('auth')) {
            uni.showModal({
              title: '需要权限',
              content: '请允许访问相册权限以保存图片',
              success: (res) => {
                if (res.confirm) {
                  uni.openSetting();
                }
              }
            });
          } else {
            uni.showToast({
              title: '保存失败',
              icon: 'none'
            });
          }
        },
        complete: () => {
          this.isProcessing = false;
        }
      });
    }
  }
};
</script>

<style scoped>
.watermark-preview {
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.06);
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20rpx;
}

.preview-title {
  font-size: 28rpx;
  font-weight: 600;
  color: #333;
}

.file-info {
  font-size: 24rpx;
  color: #999;
  max-width: 300rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.preview-container {
  min-height: 400rpx;
  background: #f5f7fa;
  border-radius: 12rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: auto;
  padding: 20rpx;
}

.preview-canvas {
  display: block;
  border-radius: 8rpx;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.1);
}

.loading-preview {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 80rpx 40rpx;
}

.loading-text {
  font-size: 28rpx;
  color: #999;
}

.empty-preview {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16rpx;
  padding: 80rpx 40rpx;
}

.empty-icon {
  font-size: 80rpx;
  opacity: 0.5;
}

.empty-text {
  font-size: 28rpx;
  color: #999;
}

.preview-actions {
  margin-top: 24rpx;
  display: flex;
  justify-content: center;
}

.action-btn {
  width: 100%;
  height: 80rpx;
  border-radius: 40rpx;
  font-size: 28rpx;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
}

.action-btn.primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  box-shadow: 0 4rpx 16rpx rgba(102, 126, 234, 0.4);
}

.action-btn[disabled] {
  background: #ddd;
  color: #999;
  box-shadow: none;
}

/* PC端适配 */
@media screen and (min-width: 768px) {
  .preview-container {
    min-height: 500rpx;
  }
  
  .action-btn.primary:not([disabled]):hover {
    transform: translateY(-2rpx);
    box-shadow: 0 6rpx 20rpx rgba(102, 126, 234, 0.5);
  }
}
</style>
