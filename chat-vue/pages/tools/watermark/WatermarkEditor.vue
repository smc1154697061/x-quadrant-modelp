<template>
  <view class="watermark-editor">
    <!-- 水印类型选择 -->
    <view class="editor-section">
      <text class="section-title">水印类型</text>
      <view class="type-selector">
        <view 
          class="type-option" 
          :class="{ active: watermarkType === 'text' }"
          @tap="setWatermarkType('text')"
        >
          <text class="type-icon">📝</text>
          <text class="type-label">文字水印</text>
        </view>
        <view 
          class="type-option" 
          :class="{ active: watermarkType === 'image' }"
          @tap="setWatermarkType('image')"
        >
          <text class="type-icon">🖼️</text>
          <text class="type-label">图片水印</text>
        </view>
      </view>
    </view>

    <!-- 文字水印配置 -->
    <view v-if="watermarkType === 'text'" class="editor-section">
      <text class="section-title">文字内容</text>
      <input 
        v-model="textConfig.content"
        class="text-input"
        placeholder="请输入水印文字"
        maxlength="50"
      />
      
      <view class="config-row">
        <text class="config-label">字体大小</text>
        <slider 
          class="config-slider" 
          :value="textConfig.fontSize" 
          min="12" 
          max="120" 
          show-value
          @change="onFontSizeChange"
        />
      </view>
      
      <view class="config-row color-row">
        <text class="config-label">文字颜色</text>
        <view class="color-picker">
          <view 
            v-for="color in presetColors" 
            :key="color"
            class="color-option"
            :style="{ backgroundColor: color }"
            :class="{ active: textConfig.color === color }"
            @tap="setTextColor(color)"
          />
          <view class="color-custom" @tap="openColorPanel">
            <view class="color-custom-preview" :style="{ backgroundColor: textConfig.color }"></view>
            <text class="color-custom-icon">▼</text>
          </view>
        </view>
      </view>
      
      <!-- 颜色选择器面板 -->
      <view v-if="showColorPanel" class="color-panel">
        <view class="panel-header">
          <text class="panel-title">自定义颜色</text>
          <text class="panel-close" @tap="closeColorPanel">×</text>
        </view>
        
        <!-- 色相选择器 -->
        <view class="hue-picker">
          <view class="hue-bar" @tap="onHueBarTap">
            <view class="hue-thumb" :style="{ left: (hslColor.h / 360 * 100) + '%' }"></view>
          </view>
        </view>
        
        <!-- 饱和度/明度选择器 -->
        <view class="saturation-lightness-picker" @tap="onSLPickerTap">
          <view 
            class="sl-area" 
            :style="{ background: 'linear-gradient(to right, #fff, hsl(' + hslColor.h + ', 100%, 50%))' }"
          >
            <view class="sl-overlay"></view>
            <view 
              class="sl-thumb" 
              :style="{ left: hslColor.s + '%', top: (100 - hslColor.l) + '%' }"
            ></view>
          </view>
        </view>
        
        <!-- 颜色预览和输入 -->
        <view class="color-result">
          <view class="color-preview-large" :style="{ backgroundColor: textConfig.color }"></view>
          <input 
            v-model="textConfig.color"
            class="color-hex-input"
            type="text"
            placeholder="#000000"
            maxlength="7"
            @input="onHexInput"
          />
        </view>
        
        <!-- 常用颜色快捷选择 -->
        <view class="quick-colors">
          <view 
            v-for="color in quickColors" 
            :key="color"
            class="quick-color-item"
            :style="{ backgroundColor: color }"
            @tap="setTextColor(color); closeColorPanel()"
          />
        </view>
        
        <button class="confirm-btn" @tap="closeColorPanel">确定</button>
      </view>
    </view>

    <!-- 图片水印配置 -->
    <view v-if="watermarkType === 'image'" class="editor-section">
      <text class="section-title">水印图片</text>
      <view class="image-upload" @tap="selectWatermarkImage">
        <view v-if="!imageConfig.src" class="upload-placeholder">
          <text class="upload-icon">➕</text>
          <text class="upload-text">点击选择图片</text>
        </view>
        <image 
          v-else 
          class="watermark-image-preview" 
          :src="imageConfig.src" 
          mode="aspectFit"
        />
      </view>
      
      <view class="config-row">
        <text class="config-label">图片宽度</text>
        <slider 
          class="config-slider" 
          :value="imageConfig.width" 
          min="20" 
          max="500" 
          show-value
          @change="onImageWidthChange"
        />
      </view>
    </view>

    <!-- 通用配置 -->
    <view class="editor-section">
      <text class="section-title">位置设置</text>
      <view class="position-grid">
        <view 
          v-for="pos in positions" 
          :key="pos.value"
          class="position-option"
          :class="{ active: position === pos.value }"
          @tap="setPosition(pos.value)"
        >
          <view class="position-icon" :class="pos.value">
            <view class="position-dot"></view>
          </view>
          <text class="position-label">{{ pos.label }}</text>
        </view>
      </view>
      
      <view v-if="position === 'custom'" class="custom-position">
        <view class="config-row">
          <text class="config-label">水平位置 (%)</text>
          <slider 
            class="config-slider" 
            :value="customPosition.x" 
            min="0" 
            max="100" 
            show-value
            @change="onCustomXChange"
          />
        </view>
        <view class="config-row">
          <text class="config-label">垂直位置 (%)</text>
          <slider 
            class="config-slider" 
            :value="customPosition.y" 
            min="0" 
            max="100" 
            show-value
            @change="onCustomYChange"
          />
        </view>
      </view>
    </view>

    <view class="editor-section">
      <text class="section-title">效果设置</text>
      
      <view class="config-row">
        <text class="config-label">透明度</text>
        <slider 
          class="config-slider" 
          :value="opacity * 100" 
          min="0" 
          max="100" 
          show-value
          @change="onOpacityChange"
        />
      </view>
      
      <view class="config-row">
        <text class="config-label">旋转角度</text>
        <slider 
          class="config-slider" 
          :value="rotation" 
          min="-180" 
          max="180" 
          show-value
          @change="onRotationChange"
        />
      </view>
      
      <view class="config-row">
        <text class="config-label">重复平铺</text>
        <switch 
          :checked="isTiled" 
          @change="onTiledChange"
          color="#667eea"
        />
      </view>
      
      <view v-if="isTiled" class="config-row">
        <text class="config-label">间距</text>
        <slider 
          class="config-slider" 
          :value="tileGap" 
          min="0" 
          max="200" 
          show-value
          @change="onTileGapChange"
        />
      </view>
    </view>
  </view>
</template>

<script>

export default {
  name: 'WatermarkEditor',
  
  props: {
    modelValue: {
      type: Object,
      default: () => ({})
    }
  },
  
  emits: ['update:modelValue', 'change'],
  
  data() {
    return {
      watermarkType: 'text',
      textConfig: {
        content: '水印文字',
        fontSize: 24,
        color: '#000000'
      },
      imageConfig: {
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
      tileGap: 50,
      presetColors: [
        '#000000', '#FFFFFF', '#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF', '#00FFFF',
        '#808080', '#C0C0C0', '#800000', '#808000', '#008000', '#800080', '#008080', '#000080'
      ],
      showColorPanel: false,
      hslColor: { h: 0, s: 50, l: 50 },
      quickColors: [
        '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F',
        '#BB8FCE', '#85C1E9', '#F8B500', '#00CED1', '#FF69B4', '#32CD32', '#FF8C00', '#9370DB'
      ]
    };
  },
  
  computed: {
    positions() {
      return [
        { value: 'top-left', label: '左上' },
        { value: 'top-center', label: '顶部' },
        { value: 'top-right', label: '右上' },
        { value: 'center-left', label: '左侧' },
        { value: 'center', label: '居中' },
        { value: 'center-right', label: '右侧' },
        { value: 'bottom-left', label: '左下' },
        { value: 'bottom-center', label: '底部' },
        { value: 'bottom-right', label: '右下' },
        { value: 'custom', label: '自定义' }
      ];
    },
    
    configData() {
      return {
        type: this.watermarkType,
        text: { ...this.textConfig },
        image: { ...this.imageConfig },
        position: this.position,
        customPosition: { ...this.customPosition },
        opacity: this.opacity,
        rotation: this.rotation,
        isTiled: this.isTiled,
        tileGap: this.tileGap
      };
    }
  },
  
  watch: {
    configData: {
      deep: true,
      handler(newVal) {
        this.$emit('update:modelValue', newVal);
        this.$emit('change', newVal);
      }
    }
  },
  
  methods: {
    setWatermarkType(type) {
      this.watermarkType = type;
    },
    
    setTextColor(color) {
      this.textConfig.color = color;
      this.updateHslFromHex(color);
    },
    
    openColorPanel() {
      this.updateHslFromHex(this.textConfig.color);
      this.showColorPanel = true;
    },
    
    closeColorPanel() {
      this.showColorPanel = false;
    },
    
    updateHslFromHex(hex) {
      const rgb = this.hexToRgb(hex);
      if (rgb) {
        const hsl = this.rgbToHsl(rgb.r, rgb.g, rgb.b);
        this.hslColor = hsl;
      }
    },
    
    hexToRgb(hex) {
      const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
      return result ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16)
      } : null;
    },
    
    rgbToHsl(r, g, b) {
      r /= 255; g /= 255; b /= 255;
      const max = Math.max(r, g, b), min = Math.min(r, g, b);
      let h, s, l = (max + min) / 2;
      
      if (max === min) {
        h = s = 0;
      } else {
        const d = max - min;
        s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
        switch (max) {
          case r: h = ((g - b) / d + (g < b ? 6 : 0)) / 6; break;
          case g: h = ((b - r) / d + 2) / 6; break;
          case b: h = ((r - g) / d + 4) / 6; break;
        }
      }
      return { h: Math.round(h * 360), s: Math.round(s * 100), l: Math.round(l * 100) };
    },
    
    hslToHex(h, s, l) {
      s /= 100; l /= 100;
      const a = s * Math.min(l, 1 - l);
      const f = n => {
        const k = (n + h / 30) % 12;
        const color = l - a * Math.max(Math.min(k - 3, 9 - k, 1), -1);
        return Math.round(255 * color).toString(16).padStart(2, '0');
      };
      return `#${f(0)}${f(8)}${f(4)}`.toUpperCase();
    },
    
    onHueBarTap(e) {
      const rect = e.currentTarget;
      const touch = e.detail || e.touches?.[0] || e;
      // 使用相对位置计算
      const query = uni.createSelectorQuery().in(this);
      query.select('.hue-bar').boundingClientRect(data => {
        if (data) {
          const x = (touch.x !== undefined ? touch.x : touch.clientX) - data.left;
          const percent = Math.max(0, Math.min(1, x / data.width));
          this.hslColor.h = Math.round(percent * 360);
          this.textConfig.color = this.hslToHex(this.hslColor.h, this.hslColor.s, this.hslColor.l);
        }
      }).exec();
    },
    
    onSLPickerTap(e) {
      const touch = e.detail || e.touches?.[0] || e;
      const query = uni.createSelectorQuery().in(this);
      query.select('.sl-area').boundingClientRect(data => {
        if (data) {
          const x = (touch.x !== undefined ? touch.x : touch.clientX) - data.left;
          const y = (touch.y !== undefined ? touch.y : touch.clientY) - data.top;
          const s = Math.max(0, Math.min(100, (x / data.width) * 100));
          const l = Math.max(0, Math.min(100, 100 - (y / data.height) * 100));
          this.hslColor.s = Math.round(s);
          this.hslColor.l = Math.round(l);
          this.textConfig.color = this.hslToHex(this.hslColor.h, this.hslColor.s, this.hslColor.l);
        }
      }).exec();
    },
    
    onHexInput(e) {
      const value = e.detail?.value || e.target?.value || '';
      if (/^#[0-9A-Fa-f]{6}$/.test(value)) {
        this.updateHslFromHex(value);
      }
    },
    
    onFontSizeChange(e) {
      this.textConfig.fontSize = e.detail.value;
    },
    
    onImageWidthChange(e) {
      this.imageConfig.width = e.detail.value;
    },
    
    setPosition(pos) {
      this.position = pos;
    },
    
    onCustomXChange(e) {
      this.customPosition.x = e.detail.value;
    },
    
    onCustomYChange(e) {
      this.customPosition.y = e.detail.value;
    },
    
    onOpacityChange(e) {
      this.opacity = e.detail.value / 100;
    },
    
    onRotationChange(e) {
      this.rotation = e.detail.value;
    },
    
    onTiledChange(e) {
      this.isTiled = e.detail.value;
    },
    
    onTileGapChange(e) {
      this.tileGap = e.detail.value;
    },
    
    selectWatermarkImage() {
      uni.chooseImage({
        count: 1,
        sizeType: ['original', 'compressed'],
        sourceType: ['album', 'camera'],
        success: (res) => {
          if (res.tempFilePaths && res.tempFilePaths.length > 0) {
            const tempPath = res.tempFilePaths[0];
            this.imageConfig.src = tempPath;
            
            // 获取图片原始尺寸
            uni.getImageInfo({
              src: tempPath,
              success: (info) => {
                const ratio = info.width / info.height;
                this.imageConfig.height = Math.round(this.imageConfig.width / ratio);
              }
            });
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
    }
  }
};
</script>

<style scoped>
.watermark-editor {
  padding: 20rpx;
}

.editor-section {
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
  margin-bottom: 20rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.06);
}

.section-title {
  font-size: 28rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 20rpx;
  display: block;
}

/* 类型选择器 */
.type-selector {
  display: flex;
  gap: 20rpx;
}

.type-option {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12rpx;
  padding: 30rpx 20rpx;
  background: #f5f7fa;
  border-radius: 12rpx;
  border: 2rpx solid transparent;
  transition: all 0.3s;
}

.type-option.active {
  background: rgba(102, 126, 234, 0.1);
  border-color: #667eea;
}

.type-icon {
  font-size: 48rpx;
}

.type-label {
  font-size: 26rpx;
  color: #666;
}

.type-option.active .type-label {
  color: #667eea;
  font-weight: 600;
}

/* 输入框 */
.text-input {
  width: 100%;
  height: 80rpx;
  border: 2rpx solid #eee;
  border-radius: 12rpx;
  padding: 0 24rpx;
  font-size: 28rpx;
  box-sizing: border-box;
  margin-bottom: 20rpx;
}

/* 配置行 */
.config-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20rpx;
}

.config-row:last-child {
  margin-bottom: 0;
}

.config-label {
  font-size: 26rpx;
  color: #666;
  min-width: 160rpx;
}

.config-slider {
  flex: 1;
  margin-left: 20rpx;
}

/* 颜色选择器 */
.color-picker {
  flex: 1;
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
  align-items: center;
}

.color-option {
  width: 48rpx;
  height: 48rpx;
  border-radius: 50%;
  border: 4rpx solid #fff;
  box-shadow: 0 0 0 2rpx #ddd;
  transition: all 0.3s;
}

.color-option.active {
  box-shadow: 0 0 0 4rpx #667eea;
  transform: scale(1.1);
}

.color-custom {
  width: 56rpx;
  height: 56rpx;
  border-radius: 8rpx;
  border: 2rpx solid #ddd;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.color-custom-preview {
  width: 100%;
  height: 100%;
  position: absolute;
  top: 0;
  left: 0;
}

.color-custom-icon {
  font-size: 16rpx;
  color: #fff;
  text-shadow: 0 0 2rpx #000;
  position: relative;
  z-index: 1;
}

/* 颜色选择面板 */
.color-panel {
  margin-top: 20rpx;
  background: #f9f9f9;
  border-radius: 12rpx;
  padding: 20rpx;
  border: 2rpx solid #eee;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20rpx;
}

.panel-title {
  font-size: 26rpx;
  font-weight: 600;
  color: #333;
}

.panel-close {
  font-size: 40rpx;
  color: #999;
  line-height: 1;
  padding: 0 10rpx;
}

/* 色相选择器 */
.hue-picker {
  margin-bottom: 20rpx;
}

.hue-bar {
  height: 24rpx;
  border-radius: 12rpx;
  background: linear-gradient(to right, 
    hsl(0, 100%, 50%), 
    hsl(60, 100%, 50%), 
    hsl(120, 100%, 50%), 
    hsl(180, 100%, 50%), 
    hsl(240, 100%, 50%), 
    hsl(300, 100%, 50%), 
    hsl(360, 100%, 50%)
  );
  position: relative;
  cursor: pointer;
}

.hue-thumb {
  width: 24rpx;
  height: 24rpx;
  background: #fff;
  border: 4rpx solid #333;
  border-radius: 50%;
  position: absolute;
  top: 50%;
  transform: translate(-50%, -50%);
  box-shadow: 0 2rpx 6rpx rgba(0,0,0,0.3);
}

/* 饱和度/明度选择器 */
.saturation-lightness-picker {
  margin-bottom: 20rpx;
}

.sl-area {
  width: 100%;
  height: 200rpx;
  border-radius: 8rpx;
  position: relative;
  cursor: pointer;
}

.sl-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(to bottom, transparent 0%, #000 100%);
  border-radius: 8rpx;
}

.sl-thumb {
  width: 20rpx;
  height: 20rpx;
  background: #fff;
  border: 4rpx solid #333;
  border-radius: 50%;
  position: absolute;
  transform: translate(-50%, -50%);
  box-shadow: 0 2rpx 6rpx rgba(0,0,0,0.3);
  pointer-events: none;
}

/* 颜色结果 */
.color-result {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-bottom: 20rpx;
}

.color-preview-large {
  width: 80rpx;
  height: 80rpx;
  border-radius: 8rpx;
  border: 2rpx solid #ddd;
  flex-shrink: 0;
}

.color-hex-input {
  flex: 1;
  height: 80rpx;
  border: 2rpx solid #eee;
  border-radius: 8rpx;
  padding: 0 20rpx;
  font-size: 28rpx;
  font-family: monospace;
  text-transform: uppercase;
  background: #fff;
}

/* 快捷颜色 */
.quick-colors {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
  margin-bottom: 20rpx;
}

.quick-color-item {
  width: 48rpx;
  height: 48rpx;
  border-radius: 8rpx;
  border: 2rpx solid #fff;
  box-shadow: 0 0 0 1rpx #ddd;
}

.confirm-btn {
  width: 100%;
  height: 72rpx;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  border: none;
  border-radius: 36rpx;
  font-size: 28rpx;
  font-weight: 500;
}

.color-row {
  flex-wrap: wrap;
}

/* 图片上传 */
.image-upload {
  width: 100%;
  height: 200rpx;
  border: 2rpx dashed #ddd;
  border-radius: 12rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20rpx;
  background: #f9f9f9;
}

.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12rpx;
}

.upload-icon {
  font-size: 48rpx;
  color: #999;
}

.upload-text {
  font-size: 26rpx;
  color: #999;
}

.watermark-image-preview {
  max-width: 100%;
  max-height: 180rpx;
}

/* 位置网格 */
.position-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16rpx;
}

.position-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8rpx;
  padding: 16rpx 8rpx;
  border-radius: 8rpx;
  background: #f5f7fa;
  transition: all 0.3s;
}

.position-option.active {
  background: rgba(102, 126, 234, 0.1);
}

.position-icon {
  width: 40rpx;
  height: 40rpx;
  border: 2rpx solid #ddd;
  border-radius: 4rpx;
  position: relative;
  background: #fff;
}

.position-icon.top-left .position-dot { position: absolute; top: 4rpx; left: 4rpx; }
.position-icon.top-center .position-dot { position: absolute; top: 4rpx; left: 50%; transform: translateX(-50%); }
.position-icon.top-right .position-dot { position: absolute; top: 4rpx; right: 4rpx; }
.position-icon.center-left .position-dot { position: absolute; top: 50%; left: 4rpx; transform: translateY(-50%); }
.position-icon.center .position-dot { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); }
.position-icon.center-right .position-dot { position: absolute; top: 50%; right: 4rpx; transform: translateY(-50%); }
.position-icon.bottom-left .position-dot { position: absolute; bottom: 4rpx; left: 4rpx; }
.position-icon.bottom-center .position-dot { position: absolute; bottom: 4rpx; left: 50%; transform: translateX(-50%); }
.position-icon.bottom-right .position-dot { position: absolute; bottom: 4rpx; right: 4rpx; }
.position-icon.custom { border-style: dashed; }
.position-icon.custom .position-dot { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); }

.position-option.active .position-icon {
  border-color: #667eea;
}

.position-dot {
  width: 12rpx;
  height: 12rpx;
  background: #ddd;
  border-radius: 50%;
}

.position-option.active .position-dot {
  background: #667eea;
}

.position-label {
  font-size: 20rpx;
  color: #999;
}

.position-option.active .position-label {
  color: #667eea;
  font-weight: 500;
}

/* 自定义位置 */
.custom-position {
  margin-top: 20rpx;
  padding-top: 20rpx;
  border-top: 2rpx solid #f0f0f0;
}

/* PC端适配 */
@media screen and (min-width: 768px) {
  .type-option:hover {
    background: rgba(102, 126, 234, 0.05);
  }
  
  .type-option.active:hover {
    background: rgba(102, 126, 234, 0.1);
  }
  
  .position-option:hover {
    background: rgba(102, 126, 234, 0.05);
  }
  
  .position-option.active:hover {
    background: rgba(102, 126, 234, 0.1);
  }
  
  .color-option:hover {
    transform: scale(1.15);
  }
}
</style>
