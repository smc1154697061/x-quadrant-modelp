<template>
  <view class="watermark-editor">
    <text class="section-title">水印设置</text>
    
    <view class="config-group">
      <text class="config-label">水印类型</text>
      <view class="type-tabs">
        <view 
          class="type-tab" 
          :class="{ active: config.type === 'text' }"
          @tap="config.type = 'text'"
        >
          <text>文字水印</text>
        </view>
        <view 
          class="type-tab" 
          :class="{ active: config.type === 'image' }"
          @tap="config.type = 'image'"
        >
          <text>图片水印</text>
        </view>
      </view>
    </view>
    
    <view v-if="config.type === 'text'" class="config-group">
      <text class="config-label">水印文字</text>
      <input 
        v-model="config.text" 
        class="text-input"
        placeholder="请输入水印文字"
        maxlength="50"
      />
    </view>
    
    <view v-if="config.type === 'image'" class="config-group">
      <text class="config-label">水印图片</text>
      <view class="image-picker" @tap="selectWatermarkImage">
        <view v-if="!config.imageUrl" class="picker-empty">
          <text class="picker-icon">+</text>
          <text class="picker-hint">选择图片</text>
        </view>
        <image 
          v-else 
          :src="config.imageUrl" 
          class="picker-image"
          mode="aspectFit"
        />
      </view>
    </view>
    
    <view class="config-group">
      <view class="config-row">
        <text class="config-label">透明度</text>
        <text class="config-value">{{ Math.round(config.opacity * 100) }}%</text>
      </view>
      <slider 
        :value="config.opacity * 100"
        min="10"
        max="100"
        @change="onOpacityChange"
        activeColor="#4facfe"
        backgroundColor="#e0e0e0"
        block-size="20"
      />
    </view>
    
    <view class="config-group">
      <view class="config-row">
        <text class="config-label">旋转角度</text>
        <text class="config-value">{{ config.rotation }}°</text>
      </view>
      <slider 
        :value="config.rotation"
        min="-180"
        max="180"
        @change="onRotationChange"
        activeColor="#4facfe"
        backgroundColor="#e0e0e0"
        block-size="20"
      />
    </view>
    
    <view class="config-group">
      <text class="config-label">水印位置</text>
      <view class="position-grid">
        <view 
          v-for="pos in positions" 
          :key="pos.value"
          class="position-item"
          :class="{ active: config.position === pos.value }"
          @tap="config.position = pos.value"
        >
          <text>{{ pos.label }}</text>
        </view>
      </view>
    </view>
    
    <view v-if="config.type === 'text'" class="config-group">
      <text class="config-label">字体大小</text>
      <view class="font-size-options">
        <view 
          v-for="size in fontSizes" 
          :key="size.value"
          class="size-item"
          :class="{ active: config.fontSize === size.value }"
          @tap="config.fontSize = size.value"
        >
          <text>{{ size.label }}</text>
        </view>
      </view>
    </view>
    
    <view v-if="config.type === 'text'" class="config-group">
      <text class="config-label">文字颜色</text>
      <view class="color-options">
        <view 
          v-for="color in colors" 
          :key="color.value"
          class="color-item"
          :class="{ active: config.color === color.value }"
          :style="{ backgroundColor: color.value }"
          @tap="config.color = color.value"
        />
      </view>
    </view>
    
    <view class="config-group">
      <view class="config-row">
        <text class="config-label">水印大小</text>
        <text class="config-value">{{ config.scale }}%</text>
      </view>
      <slider 
        :value="config.scale"
        min="20"
        max="100"
        @change="onScaleChange"
        activeColor="#4facfe"
        backgroundColor="#e0e0e0"
        block-size="20"
      />
    </view>
    
    <view class="config-group">
      <view class="config-row">
        <text class="config-label">平铺水印</text>
        <switch 
          :checked="config.tiled"
          @change="config.tiled = $event.detail.value"
          color="#4facfe"
        />
      </view>
      <view v-if="config.tiled" class="config-sub">
        <view class="config-row">
          <text class="config-label">间距</text>
          <text class="config-value">{{ config.spacing }}px</text>
        </view>
        <slider 
          :value="config.spacing"
          min="50"
          max="300"
          @change="onSpacingChange"
          activeColor="#4facfe"
          backgroundColor="#e0e0e0"
          block-size="20"
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
    fileType: {
      type: String,
      default: 'image'
    }
  },
  
  emits: ['update:config'],
  
  data() {
    return {
      config: {
        type: 'text',
        text: '机密文件',
        imageUrl: '',
        imageFile: null,
        opacity: 0.5,
        rotation: -30,
        position: 'center',
        fontSize: 24,
        color: '#888888',
        scale: 50,
        tiled: false,
        spacing: 100
      },
      
      positions: [
        { label: '左上', value: 'top-left' },
        { label: '上中', value: 'top-center' },
        { label: '右上', value: 'top-right' },
        { label: '左中', value: 'middle-left' },
        { label: '居中', value: 'center' },
        { label: '右中', value: 'middle-right' },
        { label: '左下', value: 'bottom-left' },
        { label: '下中', value: 'bottom-center' },
        { label: '右下', value: 'bottom-right' }
      ],
      
      fontSizes: [
        { label: '小', value: 16 },
        { label: '中', value: 24 },
        { label: '大', value: 36 },
        { label: '特大', value: 48 }
      ],
      
      colors: [
        { label: '灰色', value: '#888888' },
        { label: '黑色', value: '#000000' },
        { label: '白色', value: '#ffffff' },
        { label: '红色', value: '#ff4444' },
        { label: '蓝色', value: '#4facfe' },
        { label: '绿色', value: '#38ef7d' }
      ],
      
      platform: ''
    };
  },
  
  watch: {
    config: {
      handler(newVal) {
        this.$emit('update:config', { ...newVal });
      },
      deep: true
    }
  },
  
  created() {
    this.platform = getPlatformType();
    this.$emit('update:config', { ...this.config });
  },
  
  methods: {
    onOpacityChange(e) {
      this.config.opacity = e.detail.value / 100;
    },
    
    onRotationChange(e) {
      this.config.rotation = e.detail.value;
    },
    
    onScaleChange(e) {
      this.config.scale = e.detail.value;
    },
    
    onSpacingChange(e) {
      this.config.spacing = e.detail.value;
    },
    
    selectWatermarkImage() {
      const isH5 = this.platform === PLATFORM_TYPE.H5;
      
      if (isH5) {
        this.selectWatermarkImageH5();
      } else {
        this.selectWatermarkImageNative();
      }
    },
    
    selectWatermarkImageH5() {
      const input = document.createElement('input');
      input.type = 'file';
      input.accept = 'image/*';
      input.onchange = (e) => {
        const file = e.target.files[0];
        if (file) {
          const url = URL.createObjectURL(file);
          this.config.imageUrl = url;
          this.config.imageFile = file;
        }
      };
      input.click();
    },
    
    selectWatermarkImageNative() {
      uni.chooseImage({
        count: 1,
        sourceType: ['album'],
        success: (res) => {
          if (res.tempFilePaths && res.tempFilePaths.length > 0) {
            this.config.imageUrl = res.tempFilePaths[0];
            this.config.imageFile = null;
          }
        },
        fail: (err) => {
          if (!err.errMsg?.includes('cancel')) {
            uni.showToast({ title: '选择图片失败', icon: 'none' });
          }
        }
      });
    }
  }
};
</script>

<style scoped>
.watermark-editor {
  width: 100%;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-bottom: 15px;
  display: block;
}

.config-group {
  margin-bottom: 18px;
}

.config-label {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
  display: block;
}

.config-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.config-value {
  font-size: 14px;
  color: #4facfe;
  font-weight: 500;
}

.type-tabs {
  display: flex;
  gap: 10px;
}

.type-tab {
  flex: 1;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  color: #666;
  transition: all 0.3s;
}

.type-tab.active {
  border-color: #4facfe;
  background: rgba(79, 172, 254, 0.1);
  color: #4facfe;
}

.text-input {
  width: 100%;
  height: 40px;
  border: 1px solid #eee;
  border-radius: 8px;
  padding: 0 12px;
  font-size: 14px;
  background: #f9f9f9;
  box-sizing: border-box;
}

.image-picker {
  width: 100%;
  height: 80px;
  border: 2px dashed #ddd;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.picker-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.picker-icon {
  font-size: 28px;
  color: #ccc;
}

.picker-hint {
  font-size: 12px;
  color: #999;
}

.picker-image {
  width: 100%;
  height: 100%;
}

.position-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.position-item {
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #eee;
  border-radius: 6px;
  font-size: 12px;
  color: #666;
  transition: all 0.3s;
}

.position-item.active {
  border-color: #4facfe;
  background: rgba(79, 172, 254, 0.1);
  color: #4facfe;
}

.font-size-options {
  display: flex;
  gap: 8px;
}

.size-item {
  flex: 1;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #eee;
  border-radius: 6px;
  font-size: 13px;
  color: #666;
  transition: all 0.3s;
}

.size-item.active {
  border-color: #4facfe;
  background: rgba(79, 172, 254, 0.1);
  color: #4facfe;
}

.color-options {
  display: flex;
  gap: 10px;
}

.color-item {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 2px solid #eee;
  transition: all 0.3s;
}

.color-item.active {
  border-color: #4facfe;
  transform: scale(1.1);
}

.config-sub {
  margin-top: 12px;
  padding-left: 12px;
  border-left: 2px solid #eee;
}

@media screen and (min-width: 768px) {
  .type-tab:hover,
  .position-item:hover,
  .size-item:hover {
    border-color: #4facfe;
    color: #4facfe;
  }
  
  .color-item:hover {
    transform: scale(1.1);
  }
}
</style>
