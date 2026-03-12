<template>
  <view class="editor-container">
    <view class="editor-section">
      <text class="section-title">水印类型</text>
      <view class="type-selector">
        <view 
          class="type-option" 
          :class="{ active: config.type === 'text' }"
          @tap="changeType('text')"
        >
          <text>文字水印</text>
        </view>
        <view 
          class="type-option" 
          :class="{ active: config.type === 'image' }"
          @tap="changeType('image')"
        >
          <text>图片水印</text>
        </view>
      </view>
    </view>

    <view v-if="config.type === 'text'" class="editor-section">
      <text class="section-title">水印文字</text>
      <input 
        v-model="config.text" 
        class="text-input"
        placeholder="请输入水印文字"
        @input="emitChange"
      />
    </view>

    <view v-if="config.type === 'text'" class="editor-section">
      <text class="section-title">文字样式</text>
      <view class="style-row">
        <text class="style-label">颜色:</text>
        <view class="color-wrapper">
          <input 
            type="color" 
            v-model="config.color" 
            class="color-input"
            @input="emitChange"
          />
          <view class="color-preview" :style="{ backgroundColor: config.color }"></view>
        </view>
        <text class="style-label">大小:</text>
        <view class="size-control">
          <button class="size-btn" @tap.stop="adjustFontSize(-2)">-</button>
          <text class="size-value">{{ config.fontSize }}px</text>
          <button class="size-btn" @tap.stop="adjustFontSize(2)">+</button>
        </view>
      </view>
      <view class="color-palette">
        <view 
          v-for="(color, index) in commonColors" 
          :key="index"
          class="color-block"
          :style="{ backgroundColor: color }"
          :class="{ active: config.color === color }"
          @tap="selectColor(color)"
        ></view>
      </view>
    </view>

    <view v-if="config.type === 'image'" class="editor-section">
      <text class="section-title">水印图片</text>
      <view class="image-upload" @tap="selectWatermarkImage">
        <view v-if="!config.image" class="image-upload-empty">
          <text class="upload-icon">🖼️</text>
          <text class="upload-text">选择水印图片</text>
        </view>
        <image v-else :src="config.image" class="watermark-preview-image" mode="aspectFit" />
      </view>
    </view>

    <view class="editor-section">
      <text class="section-title">透明度</text>
      <view class="slider-container">
        <slider 
          v-model="config.opacity" 
          :min="0" 
          :max="1" 
          :step="0.05"
          @input="emitChange"
          activeColor="#f093fb"
        />
        <text class="slider-value">{{ Math.round(config.opacity * 100) }}%</text>
      </view>
    </view>

    <view class="editor-section">
      <text class="section-title">旋转角度</text>
      <view class="slider-container">
        <slider 
          v-model="config.rotation" 
          :min="-180" 
          :max="180" 
          :step="1"
          @input="emitChange"
          activeColor="#f093fb"
        />
        <text class="slider-value">{{ config.rotation }}°</text>
      </view>
    </view>

    <view class="editor-section">
      <text class="section-title">位置</text>
      <view class="position-grid">
        <view 
          class="position-cell" 
          :class="{ active: config.position === 'top-left' }"
          @tap="setPosition('top-left')"
        >
          <text>左上</text>
        </view>
        <view 
          class="position-cell" 
          :class="{ active: config.position === 'top' }"
          @tap="setPosition('top')"
        >
          <text>中上</text>
        </view>
        <view 
          class="position-cell" 
          :class="{ active: config.position === 'top-right' }"
          @tap="setPosition('top-right')"
        >
          <text>右上</text>
        </view>
        <view 
          class="position-cell" 
          :class="{ active: config.position === 'left' }"
          @tap="setPosition('left')"
        >
          <text>左中</text>
        </view>
        <view 
          class="position-cell" 
          :class="{ active: config.position === 'center' }"
          @tap="setPosition('center')"
        >
          <text>居中</text>
        </view>
        <view 
          class="position-cell" 
          :class="{ active: config.position === 'right' }"
          @tap="setPosition('right')"
        >
          <text>右中</text>
        </view>
        <view 
          class="position-cell" 
          :class="{ active: config.position === 'bottom-left' }"
          @tap="setPosition('bottom-left')"
        >
          <text>左下</text>
        </view>
        <view 
          class="position-cell" 
          :class="{ active: config.position === 'bottom' }"
          @tap="setPosition('bottom')"
        >
          <text>中下</text>
        </view>
        <view 
          class="position-cell" 
          :class="{ active: config.position === 'bottom-right' }"
          @tap="setPosition('bottom-right')"
        >
          <text>右下</text>
        </view>
      </view>
    </view>

    <view class="editor-section">
      <view class="repeat-toggle">
        <view class="toggle-label">
          <text>平铺水印</text>
        </view>
        <switch 
          v-model="config.repeat" 
          color="#f093fb"
          @change="emitChange"
        />
      </view>
    </view>

    <view v-if="config.repeat" class="editor-section">
      <text class="section-title">平铺间距</text>
      <view class="slider-container">
        <slider 
          v-model="config.spacing" 
          :min="50" 
          :max="300" 
          :step="10"
          @input="emitChange"
          activeColor="#f093fb"
        />
        <text class="slider-value">{{ config.spacing }}px</text>
      </view>
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
    }
  },
  data() {
    return {
      config: {
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
      commonColors: [
        '#000000', '#FFFFFF', '#FF0000', '#FF7F00', '#FFFF00',
        '#00FF00', '#00FFFF', '#0000FF', '#7F00FF', '#FF00FF',
        '#8B4513', '#FF4500', '#FF6347', '#FFD700', '#32CD32',
        '#1E90FF', '#9370DB', '#FF1493', '#696969', '#D3D3D3'
      ]
    };
  },
  methods: {
    changeType(type) {
      this.config.type = type;
      this.emitChange();
    },
    adjustFontSize(delta) {
      const newSize = this.config.fontSize + delta;
      if (newSize >= 12 && newSize <= 100) {
        this.config.fontSize = newSize;
        this.emitChange();
      }
    },
    setPosition(position) {
      this.config.position = position;
      this.emitChange();
    },
    selectColor(color) {
      this.config.color = color;
      this.emitChange();
    },
    selectWatermarkImage() {
      const platform = getPlatformType();
      
      if (platform === 'h5') {
        uni.chooseFile({
          count: 1,
          extension: ['.jpg', '.jpeg', '.png', '.gif'],
          success: (res) => {
            if (res.tempFiles && res.tempFiles.length > 0) {
              this.config.image = res.tempFiles[0].path;
              this.emitChange();
            }
          }
        });
      } else {
        uni.chooseImage({
          count: 1,
          success: (res) => {
            if (res.tempFilePaths && res.tempFilePaths.length > 0) {
              this.config.image = res.tempFilePaths[0];
              this.emitChange();
            }
          }
        });
      }
    },
    emitChange() {
      this.$emit('watermark-config-change', { ...this.config });
    }
  },
  mounted() {
    this.emitChange();
  }
}
</script>

<style scoped>
.editor-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.editor-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.type-selector {
  display: flex;
  gap: 8px;
}

.type-option {
  flex: 1;
  padding: 8px 16px;
  text-align: center;
  border: 1px solid #ddd;
  border-radius: 20px;
  font-size: 14px;
  color: #666;
  transition: all 0.3s;
}

.type-option.active {
  border-color: #f093fb;
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: #fff;
}

.text-input {
  padding: 10px 12px;
  border: 1px solid #eee;
  border-radius: 8px;
  font-size: 14px;
  background: #f9f9f9;
}

.style-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.style-label {
  font-size: 14px;
  color: #666;
}

.color-wrapper {
  position: relative;
}

.color-input {
  width: 40px;
  height: 30px;
  border: none;
  border-radius: 4px;
  opacity: 0;
  position: absolute;
  top: 0;
  left: 0;
  z-index: 2;
}

.color-preview {
  width: 40px;
  height: 30px;
  border: 2px solid #eee;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.color-palette {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
  padding: 8px;
  border: 1px solid #eee;
  border-radius: 8px;
  background: #fafafa;
}

.color-block {
  width: 24px;
  height: 24px;
  border-radius: 4px;
  border: 2px solid transparent;
  cursor: pointer;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  transition: all 0.2s;
}

.color-block.active {
  border-color: #f093fb;
  transform: scale(1.1);
  box-shadow: 0 0 0 2px rgba(240, 147, 251, 0.3);
}

.size-control {
  display: flex;
  align-items: center;
  gap: 8px;
}

.size-btn {
  width: 28px;
  height: 28px;
  border: 1px solid #ddd;
  border-radius: 50%;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  padding: 0;
  margin: 0;
}

.size-value {
  font-size: 14px;
  color: #333;
  min-width: 40px;
  text-align: center;
}

.image-upload {
  border: 2px dashed #ddd;
  border-radius: 8px;
  padding: 20px;
  text-align: center;
  min-height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.image-upload-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.upload-icon {
  font-size: 32px;
  opacity: 0.6;
}

.upload-text {
  font-size: 14px;
  color: #666;
}

.watermark-preview-image {
  max-width: 100%;
  max-height: 80px;
}

.slider-container {
  display: flex;
  align-items: center;
  gap: 12px;
}

.slider-container slider {
  flex: 1;
}

.slider-value {
  font-size: 14px;
  color: #666;
  min-width: 50px;
  text-align: right;
}

.position-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.position-cell {
  padding: 8px;
  text-align: center;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 13px;
  color: #666;
  transition: all 0.3s;
}

.position-cell.active {
  border-color: #f093fb;
  background: rgba(240, 147, 251, 0.1);
  color: #f5576c;
}

.repeat-toggle {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.toggle-label {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

@media screen and (min-width: 768px) {
  .type-option:hover {
    border-color: #f093fb;
    background: rgba(240, 147, 251, 0.1);
  }
  
  .position-cell:hover {
    border-color: #f093fb;
    background: rgba(240, 147, 251, 0.05);
  }
  
  .image-upload:hover {
    border-color: #f093fb;
    background: rgba(240, 147, 251, 0.05);
  }
}
</style>
