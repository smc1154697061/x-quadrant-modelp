<template>
  <view class="preview-container">
    <text class="section-title">预览效果</text>
    <view class="preview-wrapper">
      <view v-if="!isLoaded" class="loading-state">
        <text>加载中...</text>
      </view>
      <view v-else-if="file.type === 'pdf'" class="pdf-notice">
        <text class="notice-icon">ℹ️</text>
        <text class="notice-text">PDF文件暂不支持预览，下载后可查看效果</text>
      </view>
      <canvas 
        v-else 
        canvas-id="watermark-canvas" 
        id="watermark-canvas" 
        class="preview-canvas"
        :width="drawWidth"
        :height="drawHeight"
        :style="{ width: displayWidth + 'px', height: displayHeight + 'px' }"
      ></canvas>
    </view>
  </view>
</template>

<script>
import { getPlatformType } from '../../../../utils/platform-adapter.js';

export default {
  props: {
    file: {
      type: Object,
      default: null
    },
    watermarkConfig: {
      type: Object,
      default: () => ({
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
      })
    }
  },
  data() {
    return {
      isLoaded: false,
      displayWidth: 0,
      displayHeight: 0,
      originalImage: null,
      watermarkImage: null,
      platform: 'h5',
      ctx: null,
      imgInfo: null,
      drawWidth: 0,
      drawHeight: 0
    };
  },
  watch: {
    file: {
      handler(newFile) {
        if (newFile) {
          this.initCanvas();
        }
      },
      immediate: true
    },
    watermarkConfig: {
      handler(newVal, oldVal) {
        if (!this.isLoaded || !this.file || this.file.type !== 'image') return;
        
        const typeChanged = !oldVal || newVal.type !== oldVal.type;
        const imageChanged = !oldVal || newVal.image !== oldVal.image;
        
        if ((newVal.type === 'image' && (typeChanged || imageChanged)) || 
            (newVal.type === 'image' && !this.watermarkImage && newVal.image)) {
          this.loadWatermarkImageIfNeeded();
        } else {
          this.drawWatermark();
        }
      },
      deep: true
    }
  },
  mounted() {
    this.platform = getPlatformType();
    if (this.file) {
      this.initCanvas();
    }
  },
  methods: {
    initCanvas() {
      this.isLoaded = false;
      this.originalImage = null;
      this.watermarkImage = null;
      
      if (this.file.type === 'image') {
        this.getImageInfo(this.file.path, (info) => {
          this.imgInfo = info;
          this.calculateCanvasSize(info.width, info.height);
          this.loadWatermarkImageIfNeeded();
        });
      } else if (this.file.type === 'pdf') {
        this.isLoaded = true;
        uni.showToast({
          title: 'PDF文件将在下载时处理',
          icon: 'none'
        });
      }
    },
    getImageInfo(path, callback) {
      uni.getImageInfo({
        src: path,
        success: (res) => {
          callback(res);
        },
        fail: () => {
          uni.showToast({
            title: '图片加载失败',
            icon: 'none'
          });
          this.isLoaded = true;
        }
      });
    },
    calculateCanvasSize(width, height) {
      const maxWidth = uni.getSystemInfoSync().windowWidth - 60;
      const maxHeight = 400;
      
      let displayScale = 1;
      if (width > maxWidth || height > maxHeight) {
        const widthScale = maxWidth / width;
        const heightScale = maxHeight / height;
        displayScale = Math.min(widthScale, heightScale);
      }
      
      this.displayWidth = Math.floor(width * displayScale);
      this.displayHeight = Math.floor(height * displayScale);
      
      const maxDrawSize = 2048;
      let drawScale = 1;
      if (width > maxDrawSize || height > maxDrawSize) {
        const widthScale = maxDrawSize / width;
        const heightScale = maxDrawSize / height;
        drawScale = Math.min(widthScale, heightScale);
      }
      this.drawWidth = Math.floor(width * drawScale);
      this.drawHeight = Math.floor(height * drawScale);
    },
    loadWatermarkImageIfNeeded() {
      if (this.watermarkConfig.type === 'image' && this.watermarkConfig.image) {
        this.getImageInfo(this.watermarkConfig.image, (info) => {
          this.watermarkImage = info;
          this.isLoaded = true;
          this.$nextTick(() => {
            this.drawWatermark();
          });
        });
      } else {
        this.isLoaded = true;
        this.$nextTick(() => {
          this.drawWatermark();
        });
      }
    },
    drawWatermark() {
      if (!this.imgInfo) return;
      
      const ctx = uni.createCanvasContext('watermark-canvas', this);
      if (!ctx) return;
      
      const imgWidth = this.drawWidth;
      const imgHeight = this.drawHeight;
      
      ctx.drawImage(this.file.path, 0, 0, imgWidth, imgHeight);
      
      const config = this.watermarkConfig;
      ctx.globalAlpha = config.opacity;
      
      if (config.repeat) {
        this.drawRepeatedWatermark(ctx, imgWidth, imgHeight);
      } else {
        this.drawSingleWatermark(ctx, imgWidth, imgHeight);
      }
      
      ctx.globalAlpha = 1.0;
      ctx.draw();
    },
    drawSingleWatermark(ctx, imgWidth, imgHeight) {
      const config = this.watermarkConfig;
      const position = this.calculatePosition(config.position, imgWidth, imgHeight);
      
      ctx.save();
      ctx.translate(position.x, position.y);
      ctx.rotate((config.rotation * Math.PI) / 180);
      
      if (config.type === 'text') {
        this.drawTextWatermark(ctx, 0, 0);
      } else if (config.type === 'image' && this.watermarkImage) {
        this.drawImageWatermark(ctx, 0, 0);
      }
      
      ctx.restore();
    },
    drawRepeatedWatermark(ctx, imgWidth, imgHeight) {
      const config = this.watermarkConfig;
      const spacing = config.spacing || 100;
      
      const watermarkSize = this.getWatermarkSize();
      const watermarkWidth = watermarkSize.width;
      const watermarkHeight = watermarkSize.height;
      
      const cols = Math.ceil(imgWidth / (watermarkWidth + spacing)) + 1;
      const rows = Math.ceil(imgHeight / (watermarkHeight + spacing)) + 1;
      
      for (let row = 0; row < rows; row++) {
        for (let col = 0; col < cols; col++) {
          const x = col * (watermarkWidth + spacing);
          const y = row * (watermarkHeight + spacing);
          
          ctx.save();
          ctx.translate(x, y);
          ctx.rotate((config.rotation * Math.PI) / 180);
          
          if (config.type === 'text') {
            this.drawTextWatermark(ctx, 0, 0);
          } else if (config.type === 'image' && this.watermarkImage) {
            this.drawImageWatermark(ctx, 0, 0);
          }
          
          ctx.restore();
        }
      }
    },
    getWatermarkSize() {
      const config = this.watermarkConfig;
      if (config.type === 'text') {
        return {
          width: config.fontSize * config.text.length,
          height: config.fontSize * 1.5
        };
      } else if (config.type === 'image' && this.watermarkImage) {
        let width = this.watermarkImage.width;
        let height = this.watermarkImage.height;
        const maxWatermarkSize = 150;
        if (width > maxWatermarkSize || height > maxWatermarkSize) {
          const scale = Math.min(maxWatermarkSize / width, maxWatermarkSize / height);
          width = width * scale;
          height = height * scale;
        }
        return { width, height };
      }
      return { width: 0, height: 0 };
    },
    drawTextWatermark(ctx, x, y) {
      const config = this.watermarkConfig;
      ctx.font = `${config.fontSize}px Arial, sans-serif`;
      ctx.setFillStyle(config.color);
      ctx.setTextAlign('center');
      ctx.setTextBaseline('middle');
      ctx.fillText(config.text, x, y);
    },
    drawImageWatermark(ctx, x, y) {
      if (!this.watermarkImage) return;
      
      const size = this.getWatermarkSize();
      const width = size.width;
      const height = size.height;
      
      ctx.drawImage(
        this.watermarkImage.path,
        x - width / 2,
        y - height / 2,
        width,
        height
      );
    },
    calculatePosition(position, imgWidth, imgHeight) {
      let x = imgWidth / 2;
      let y = imgHeight / 2;
      
      const margin = 20;
      
      switch (position) {
        case 'top-left':
          x = margin;
          y = margin;
          break;
        case 'top':
          x = imgWidth / 2;
          y = margin;
          break;
        case 'top-right':
          x = imgWidth - margin;
          y = margin;
          break;
        case 'left':
          x = margin;
          y = imgHeight / 2;
          break;
        case 'center':
          x = imgWidth / 2;
          y = imgHeight / 2;
          break;
        case 'right':
          x = imgWidth - margin;
          y = imgHeight / 2;
          break;
        case 'bottom-left':
          x = margin;
          y = imgHeight - margin;
          break;
        case 'bottom':
          x = imgWidth / 2;
          y = imgHeight - margin;
          break;
        case 'bottom-right':
          x = imgWidth - margin;
          y = imgHeight - margin;
          break;
      }
      
      return { x, y };
    },
    exportImage() {
      if (this.file.type === 'pdf') {
        uni.showToast({
          title: 'PDF处理中...',
          icon: 'loading'
        });
        setTimeout(() => {
          uni.showToast({
            title: 'PDF功能开发中',
            icon: 'none'
          });
        }, 1000);
        return;
      }
      
      setTimeout(() => {
        uni.canvasToTempFilePath({
          canvasId: 'watermark-canvas',
          success: (res) => {
            if (this.platform === 'h5') {
              uni.downloadFile({
                url: res.tempFilePath,
                success: (downloadRes) => {
                  const a = document.createElement('a');
                  a.href = downloadRes.tempFilePath || res.tempFilePath;
                  a.download = `watermarked_${this.file.name || 'image.png'}`;
                  document.body.appendChild(a);
                  a.click();
                  document.body.removeChild(a);
                  uni.showToast({
                    title: '下载成功',
                    icon: 'success'
                  });
                },
                fail: () => {
                  const a = document.createElement('a');
                  a.href = res.tempFilePath;
                  a.download = `watermarked_${this.file.name || 'image.png'}`;
                  document.body.appendChild(a);
                  a.click();
                  document.body.removeChild(a);
                  uni.showToast({
                    title: '下载成功',
                    icon: 'success'
                  });
                }
              });
            } else {
              uni.saveImageToPhotosAlbum({
                filePath: res.tempFilePath,
                success: () => {
                  uni.showToast({
                    title: '已保存到相册',
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
          fail: (err) => {
            console.error('导出失败', err);
            uni.showToast({
              title: '导出失败',
              icon: 'none'
            });
          }
        }, this);
      }, 300);
    }
  }
}
</script>

<style scoped>
.preview-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.preview-wrapper {
  border: 1px solid #eee;
  border-radius: 8px;
  padding: 10px;
  background: #fafafa;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}

.loading-state {
  color: #999;
  font-size: 14px;
}

.pdf-notice {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 20px;
  background: #fff3cd;
  border-radius: 8px;
}

.notice-icon {
  font-size: 20px;
}

.notice-text {
  font-size: 14px;
  color: #856404;
}

.preview-canvas {
  object-fit: contain;
}
</style>
