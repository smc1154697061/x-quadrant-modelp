<template>
  <view class="generate-panel">
    <!-- 模板选择区域 -->
    <view class="section">
      <view class="section-header">
        <text class="section-title">选择模板</text>
        <text class="section-action" @tap="$emit('goToManage')">管理模板 ›</text>
      </view>
      
      <view v-if="templates.length === 0" class="empty-templates">
        <text class="empty-text">暂无模板，请先上传</text>
        <view class="empty-btn" @tap="$emit('goToManage')">去上传</view>
      </view>
      
      <scroll-view v-else scroll-x class="template-scroll">
        <view class="template-list">
          <view 
            v-for="template in templates" 
            :key="template.id"
            class="template-card"
            :class="{ selected: selectedTemplate?.id === template.id }"
            @tap="selectTemplate(template)"
          >
            <view class="template-icon">{{ template.file_type === 'word' ? '📄' : '📕' }}</view>
            <view class="template-name">{{ template.name }}</view>
            <view class="template-tags" v-if="template.tags">
              <text class="tag">{{ template.tags.split(',')[0] }}</text>
            </view>
          </view>
        </view>
      </scroll-view>
    </view>
    
    <!-- 信息输入区域 -->
    <view class="section">
      <view class="section-header">
        <text class="section-title">输入您的信息</text>
        <text class="section-hint">AI将根据模板格式生成文档</text>
      </view>
      
      <view class="input-area">
        <textarea 
          class="content-input"
          v-model="userInput"
          placeholder="请输入您的个人信息、项目经历、教育背景等内容...&#10;&#10;例如：&#10;姓名：张三&#10;学历：本科&#10;专业：计算机科学&#10;工作经验：5年软件开发经验..."
          :maxlength="5000"
          auto-height
          :style="{ minHeight: '300rpx' }"
        />
        <view class="input-counter">{{ userInput.length }}/5000</view>
      </view>
    </view>
    
    <!-- 生成按钮 -->
    <view class="action-section">
      <view 
        class="generate-btn"
        :class="{ disabled: !canGenerate || generating }"
        @tap="generateDocument"
      >
        <text v-if="generating" class="btn-text">生成中...</text>
        <text v-else class="btn-text">✨ 生成文档</text>
      </view>
    </view>
  </view>
</template>

<script>
import api from '../../../../utils/api';

export default {
  name: 'TemplateGeneratePanel',
  data() {
    return {
      templates: [],
      selectedTemplate: null,
      userInput: '',
      generating: false
    };
  },
  computed: {
    canGenerate() {
      return this.selectedTemplate && this.userInput.trim().length > 10;
    }
  },
  mounted() {
    this.loadTemplates();
  },
  methods: {
    async loadTemplates() {
      try {
        const res = await api.get('/llm/templates');
        if (res.code === 'SUCCESS') {
          this.templates = res.data || [];
        }
      } catch (e) {
        console.error('加载模板失败:', e);
      }
    },
    
    refreshTemplates() {
      this.loadTemplates();
    },
    
    selectTemplate(template) {
      this.selectedTemplate = template;
    },
    
    async generateDocument() {
      if (!this.canGenerate || this.generating) return;
      
      this.generating = true;
      uni.showLoading({ title: '正在生成文档...' });
      
      try {
        const res = await api.post('/llm/generate', {
          template_id: this.selectedTemplate.id,
          user_input: this.userInput
        });
        
        uni.hideLoading();
        
        if (res.code === 'SUCCESS') {
          uni.showToast({ title: '生成成功', icon: 'success' });
          this.$emit('viewResult', {
            generation_id: res.data.generation_id,
            content: res.data.content,
            template_name: this.selectedTemplate.name
          });
        } else {
          uni.showToast({ title: res.message || '生成失败', icon: 'none' });
        }
      } catch (e) {
        uni.hideLoading();
        console.error('生成失败:', e);
        uni.showToast({ title: '生成失败，请重试', icon: 'none' });
      } finally {
        this.generating = false;
      }
    }
  }
};
</script>

<style scoped>
.generate-panel {
  padding: 20rpx;
  padding-bottom: 200rpx;
}

.section {
  background: #fff;
  border-radius: 16rpx;
  padding: 30rpx;
  margin-bottom: 20rpx;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20rpx;
}

.section-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
}

.section-action {
  font-size: 26rpx;
  color: #007bff;
}

.section-hint {
  font-size: 24rpx;
  color: #999;
}

/* 空模板提示 */
.empty-templates {
  padding: 40rpx;
  text-align: center;
}

.empty-text {
  font-size: 28rpx;
  color: #999;
  display: block;
  margin-bottom: 20rpx;
}

.empty-btn {
  display: inline-block;
  padding: 16rpx 40rpx;
  background: #007bff;
  color: #fff;
  border-radius: 30rpx;
  font-size: 28rpx;
}

/* 模板滚动列表 */
.template-scroll {
  white-space: nowrap;
  margin: 0 -10rpx;
}

.template-list {
  display: inline-flex;
  gap: 20rpx;
  padding: 10rpx;
}

.template-card {
  width: 200rpx;
  padding: 24rpx;
  background: #f5f7fa;
  border-radius: 16rpx;
  text-align: center;
  border: 2rpx solid transparent;
  transition: all 0.3s;
  flex-shrink: 0;
}

.template-card.selected {
  background: #e6f2ff;
  border-color: #007bff;
}

.template-icon {
  font-size: 48rpx;
  margin-bottom: 12rpx;
}

.template-name {
  font-size: 26rpx;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 8rpx;
}

.template-tags .tag {
  font-size: 22rpx;
  color: #666;
  background: rgba(0, 123, 255, 0.1);
  padding: 4rpx 12rpx;
  border-radius: 20rpx;
}

/* 输入区域 */
.input-area {
  position: relative;
}

.content-input {
  width: 100%;
  min-height: 300rpx;
  padding: 20rpx;
  font-size: 28rpx;
  line-height: 1.6;
  background: #f5f7fa;
  border-radius: 12rpx;
  box-sizing: border-box;
}

.input-counter {
  position: absolute;
  right: 20rpx;
  bottom: 20rpx;
  font-size: 24rpx;
  color: #999;
}

/* 生成按钮 */
.action-section {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 20rpx 30rpx;
  padding-bottom: calc(20rpx + env(safe-area-inset-bottom));
  background: #fff;
  box-shadow: 0 -4rpx 20rpx rgba(0, 0, 0, 0.08);
}

.generate-btn {
  height: 96rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
  border-radius: 48rpx;
  transition: all 0.3s;
}

.generate-btn.disabled {
  background: #ccc;
}

.btn-text {
  font-size: 32rpx;
  font-weight: 600;
  color: #fff;
}
</style>
