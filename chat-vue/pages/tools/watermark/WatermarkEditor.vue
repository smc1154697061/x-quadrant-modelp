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
      
      <view class="config-row">
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
          <input 
            v-model="textConfig.color"
            class="color-input"
            type="text"
            placeholder="#000000"
            maxlength="7"
          />
        </view>
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
import { getPlatformType, PLATFORM_TYPE } from '../../../utils/platform-adapter.js';

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
        '#808080', '#C0C0C0', '#800000', '#808000', '#008000', '#800080', '#008080', '#000080',
        '#FFA500', '#FFC0CB', '#FFD700', '#A52A2A', '#FA8072', '#E6E6FA', '#F0E68C', '#DDA0DD',
        '#87CEEB', '#98FB98', '#F5DEB3', '#FFE4E1', '#F0F8FF', '#1E90FF', '#FF6347', '#40E0D0'
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
      const platform = getPlatformType();
      
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

.color-input {
  width: 140rpx;
  height: 56rpx;
  border: 2rpx solid #eee;
  border-radius: 8rpx;
  padding: 0 12rpx;
  font-size: 24rpx;
  font-family: monospace;
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
