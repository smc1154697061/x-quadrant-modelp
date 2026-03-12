<template>
  <view class="watermark-preview">
    <view class="preview-container">
      <canvas 
        v-if="isH5"
        ref="canvasRef"
        class="preview-canvas"
        :width="canvasWidth"
        :height="canvasHeight"
      />
      <canvas 
        v-else
        canvas-id="watermarkCanvas"
        class="preview-canvas"
        :style="{ width: canvasWidth + 'px', height: canvasHeight + 'px' }"
      />
      
      <view v-if="loading" class="loading-mask">
        <text class="loading-text">生成预览中...</text>
      </view>
    </view>
    
    <view class="preview-info">
      <text class="info-item">尺寸: {{ canvasWidth }} × {{ canvasHeight }}</text>
    </view>
  </view>
</template>

<script>
import { getPlatformType, PLATFORM_TYPE } from '../../../utils/platform-adapter.js';

export default {
  name: 'WatermarkPreview',
  
  props: {
    sourceUrl: {
      type: String,
      default: ''
    },
    watermarkConfig: {
      type: Object,
      default: () => ({})
    },
    fileType: {
      type: String,
      default: 'image'
    }
  },
  
  emits: ['preview-ready'],
  
  data() {
    return {
      canvasWidth: 300,
      canvasHeight: 200,
      loading: false,
      platform: '',
      isH5: false,
      ctx: null,
      imageInfo: null,
      initialized: false
    };
  },
  
  created() {
    this.platform = getPlatformType();
    this.isH5 = this.platform === PLATFORM_TYPE.H5;
  },
  
  mounted() {
    this.$nextTick(() => {
      this.initCanvas();
    });
  },
  
  methods: {
    initCanvas() {
      if (this.isH5) {
        const canvas = this.$refs.canvasRef;
        if (canvas) {
          this.ctx = canvas.getContext('2d');
          this.initialized = true;
        }
      } else {
        this.ctx = uni.createCanvasContext('watermarkCanvas', this);
        this.initialized = true;
      }
    },
    
    async loadSourceImage() {
      if (!this.sourceUrl) {
        console.error('没有源图片URL');
        return;
      }
      
      if (!this.initialized) {
        this.$nextTick(() => {
          this.initCanvas();
          this.loadSourceImage();
        });
        return;
      }
      
      this.loading = true;
      
      try {
        const imageInfo = await this.getImageInfo(this.sourceUrl);
        this.imageInfo = imageInfo;
        
        const maxSize = 400;
        let width = imageInfo.width;
        let height = imageInfo.height;
        
        if (width > maxSize || height > maxSize) {
          const ratio = Math.min(maxSize / width, maxSize / height);
          width = Math.floor(width * ratio);
          height = Math.floor(height * ratio);
        }
        
        this.canvasWidth = width;
        this.canvasHeight = height;
        
        await this.$nextTick();
        
        if (this.isH5) {
          const canvas = this.$refs.canvasRef;
          if (canvas) {
            canvas.width = width;
            canvas.height = height;
            this.ctx = canvas.getContext('2d');
          }
        }
        
        await this.renderPreview();
      } catch (e) {
        console.error('加载图片失败:', e);
        uni.showToast({ title: '加载图片失败', icon: 'none' });
      } finally {
        this.loading = false;
      }
    },
    
    getImageInfo(src) {
      return new Promise((resolve, reject) => {
        if (this.isH5) {
          const img = new Image();
          img.crossOrigin = 'anonymous';
          img.onload = () => {
            resolve({ width: img.width, height: img.height, path: src, img: img });
          };
          img.onerror = (e) => {
            console.error('图片加载错误:', e);
            reject(e);
          };
          img.src = src;
        } else {
          uni.getImageInfo({
            src: src,
            success: resolve,
            fail: reject
          });
        }
      });
    },
    
    async renderPreview() {
      if (!this.ctx || !this.sourceUrl || !this.imageInfo) {
        console.error('渲染条件不满足', {
          hasCtx: !!this.ctx,
          hasSource: !!this.sourceUrl,
          hasImageInfo: !!this.imageInfo
        });
        return;
      }
      
      this.loading = true;
      
      try {
        const config = this.watermarkConfig || {};
        const width = this.canvasWidth;
        const height = this.canvasHeight;
        
        this.ctx.clearRect(0, 0, width, height);
        
        await this.drawImage(this.sourceUrl, 0, 0, width, height);
        
        if (config.tiled) {
          await this.drawTiledWatermark(config, width, height);
        } else {
          await this.drawSingleWatermark(config, width, height);
        }
        
        this.finalizeCanvas();
      } catch (e) {
        console.error('渲染预览失败:', e);
        uni.showToast({ title: '渲染失败', icon: 'none' });
      } finally {
        this.loading = false;
      }
    },
    
    drawImage(src, x, y, w, h) {
      return new Promise((resolve, reject) => {
        if (this.isH5) {
          const img = new Image();
          img.crossOrigin = 'anonymous';
          img.onload = () => {
            this.ctx.drawImage(img, x, y, w, h);
            resolve();
          };
          img.onerror = reject;
          img.src = src;
        } else {
          this.ctx.drawImage(src, x, y, w, h);
          setTimeout(resolve, 150);
        }
      });
    },
    
    async drawSingleWatermark(config, width, height) {
      const pos = this.calculatePosition(config.position, width, height);
      
      this.ctx.save();
      this.ctx.globalAlpha = config.opacity || 0.5;
      this.ctx.translate(pos.x, pos.y);
      this.ctx.rotate((config.rotation * Math.PI) / 180);
      
      if (config.type === 'text') {
        await this.drawTextWatermark(config, 0, 0, width, height);
      } else if (config.type === 'image' && config.imageUrl) {
        await this.drawImageWatermark(config, 0, 0, width, height);
      }
      
      this.ctx.restore();
    },
    
    async drawTiledWatermark(config, width, height) {
      const spacing = config.spacing || 100;
      const stepX = spacing + 50;
      const stepY = spacing + 30;
      
      for (let y = -height; y < height * 2; y += stepY) {
        for (let x = -width; x < width * 2; x += stepX) {
          this.ctx.save();
          this.ctx.globalAlpha = config.opacity || 0.5;
          this.ctx.translate(x, y);
          this.ctx.rotate((config.rotation * Math.PI) / 180);
          
          if (config.type === 'text') {
            await this.drawTextWatermark(config, 0, 0, width, height);
          } else if (config.type === 'image' && config.imageUrl) {
            await this.drawImageWatermark(config, 0, 0, width, height);
          }
          
          this.ctx.restore();
        }
      }
    },
    
    async drawTextWatermark(config, x, y, canvasWidth, canvasHeight) {
      const fontSize = Math.floor((config.fontSize || 24) * ((config.scale || 50) / 50));
      this.ctx.font = `${fontSize}px Arial`;
      this.ctx.fillStyle = config.color || '#888888';
      this.ctx.textAlign = 'center';
      this.ctx.textBaseline = 'middle';
      
      const text = config.text || '水印';
      this.ctx.fillText(text, x, y);
    },
    
    async drawImageWatermark(config, x, y, canvasWidth, canvasHeight) {
      const size = Math.min(canvasWidth, canvasHeight) * ((config.scale || 50) / 100);
      
      try {
        const watermarkImg = await this.getImageInfo(config.imageUrl);
        const imgWidth = watermarkImg.width;
        const imgHeight = watermarkImg.height;
        const ratio = size / Math.max(imgWidth, imgHeight);
        const drawWidth = imgWidth * ratio;
        const drawHeight = imgHeight * ratio;
        
        await this.drawImage(config.imageUrl, x - drawWidth / 2, y - drawHeight / 2, drawWidth, drawHeight);
      } catch (e) {
        console.error('加载水印图片失败:', e);
      }
    },
    
    calculatePosition(position, width, height) {
      const padding = 50;
      const positions = {
        'top-left': { x: padding, y: padding },
        'top-center': { x: width / 2, y: padding },
        'top-right': { x: width - padding, y: padding },
        'middle-left': { x: padding, y: height / 2 },
        'center': { x: width / 2, y: height / 2 },
        'middle-right': { x: width - padding, y: height / 2 },
        'bottom-left': { x: padding, y: height - padding },
        'bottom-center': { x: width / 2, y: height - padding },
        'bottom-right': { x: width - padding, y: height - padding }
      };
      return positions[position] || positions['center'];
    },
    
    finalizeCanvas() {
      if (this.isH5) {
        const canvas = this.$refs.canvasRef;
        if (canvas) {
          const url = canvas.toDataURL('image/png');
          this.$emit('preview-ready', {
            url: url,
            base64: url,
            width: this.canvasWidth,
            height: this.canvasHeight
          });
        }
      } else {
        this.ctx.draw(false, () => {
          setTimeout(() => {
            uni.canvasToTempFilePath({
              canvasId: 'watermarkCanvas',
              success: (res) => {
                this.$emit('preview-ready', {
                  url: res.tempFilePath,
                  base64: res.tempFilePath,
                  width: this.canvasWidth,
                  height: this.canvasHeight
                });
              },
              fail: (err) => {
                console.error('生成预览失败:', err);
                uni.showToast({ title: '生成预览失败', icon: 'none' });
              }
            }, this);
          }, 300);
        });
      }
    }
  }
};
</script>

<style scoped>
.watermark-preview {
  width: 100%;
}

.preview-container {
  position: relative;
  width: 100%;
  display: flex;
  justify-content: center;
  background: #f5f5f5;
  border-radius: 8px;
  overflow: hidden;
  min-height: 100px;
}

.preview-canvas {
  display: block;
  max-width: 100%;
  height: auto;
}

.loading-mask {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
}

.loading-text {
  font-size: 14px;
  color: #666;
}

.preview-info {
  margin-top: 10px;
  display: flex;
  justify-content: center;
}

.info-item {
  font-size: 12px;
  color: #999;
}
</style>
