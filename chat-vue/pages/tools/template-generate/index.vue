<template>
  <app-layout title="文档生成">
    <view class="generate-container">
      <!-- 模板选择区域 -->
      <view class="template-section">
        <view class="section-title">
          <text class="title-icon">[模板]</text>
          <text>选择模板</text>
        </view>

        <view v-if="selectedTemplate" class="selected-template">
          <view class="template-info">
            <view class="file-icon" :class="selectedTemplate.file_type">
              <text v-if="selectedTemplate.file_type === 'word'">W</text>
              <text v-else-if="selectedTemplate.file_type === 'pdf'">P</text>
              <text v-else>文</text>
            </view>
            <view class="template-detail">
              <text class="template-name">{{ selectedTemplate.name }}</text>
              <text class="template-tags">{{ selectedTemplate.tags }}</text>
            </view>
          </view>
          <view class="change-btn" @tap="showTemplateSelector">
            <text>更换</text>
          </view>
        </view>
        
        <view v-else class="select-template-btn" @tap="showTemplateSelector">
          <text class="select-icon">+</text>
          <text class="select-text">选择模板</text>
        </view>
      </view>
      
      <!-- 信息输入区域 -->
      <view class="input-section">
        <view class="section-title">
          <text class="title-icon">[编辑]</text>
          <text>填写信息</text>
        </view>

        <textarea
          class="info-textarea"
          v-model="userInput"
          placeholder="请填写您的个人信息，例如：&#10;姓名：张三&#10;年龄：28岁&#10;学历：本科&#10;工作经验：5年&#10;...&#10;&#10;AI将根据模板格式和您提供的信息生成完整文档"
          :maxlength="5000"
        />

        <view class="input-tips">
          <text class="tips-icon">[提示]</text>
          <text class="tips-text">信息越详细，生成的文档越准确</text>
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
          <text v-else class="btn-text">生成文档</text>
        </view>
      </view>
      
      <!-- 模板选择弹窗 -->
      <uni-popup ref="templatePopup" type="bottom">
        <view class="template-selector">
          <view class="selector-header">
            <text class="selector-title">选择模板</text>
            <text class="selector-close" @tap="closeTemplateSelector">×</text>
          </view>
          
          <scroll-view class="template-list" scroll-y>
            <view v-if="templates.length === 0" class="empty-state">
              <text class="empty-text">暂无模板</text>
              <text class="empty-subtext">请先上传模板</text>
            </view>
            
            <view 
              v-for="template in templates" 
              :key="template.id"
              class="template-item"
              :class="{ selected: selectedTemplate && selectedTemplate.id === template.id }"
              @tap="selectTemplate(template)"
            >
              <view class="item-icon" :class="template.file_type">
                <text v-if="template.file_type === 'word'">W</text>
                <text v-else-if="template.file_type === 'pdf'">P</text>
                <text v-else>文</text>
              </view>
              <view class="item-info">
                <text class="item-name">{{ template.name }}</text>
                <text class="item-tags">{{ template.tags }}</text>
              </view>
              <view v-if="selectedTemplate && selectedTemplate.id === template.id" class="check-icon">
                <text>✓</text>
              </view>
            </view>
          </scroll-view>
          
          <view class="selector-footer">
            <view class="manage-btn" @tap="goToManage">
              <text>管理模板</text>
            </view>
          </view>
        </view>
      </uni-popup>
    </view>
  </app-layout>
</template>

<script>
import AppLayout from '../../../components/layout/AppLayout.vue';
import api from '../../../utils/api.js';

export default {
  components: {
    AppLayout
  },
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
      return this.selectedTemplate && this.userInput.trim().length > 0;
    }
  },
  onLoad(options) {
    // 如果传入了模板ID，自动选择
    if (options.templateId) {
      this.preSelectTemplate(options.templateId, options.templateName);
    }
    this.loadTemplates();
  },
  methods: {
    // 预选择模板（从其他页面传入）
    preSelectTemplate(templateId, templateName) {
      this.selectedTemplate = {
        id: parseInt(templateId),
        name: templateName ? decodeURIComponent(templateName) : ''
      };
    },
    
    // 加载模板列表
    async loadTemplates() {
      try {
        const res = await api.get('/llm/templates');
        if (res.code === 'SUCCESS') {
          this.templates = res.data || [];
          
          // 如果已选择模板，更新完整信息
          if (this.selectedTemplate && this.selectedTemplate.id) {
            const fullTemplate = this.templates.find(t => t.id === this.selectedTemplate.id);
            if (fullTemplate) {
              this.selectedTemplate = fullTemplate;
            }
          }
        }
      } catch (e) {
        console.error('加载模板失败:', e);
      }
    },
    
    // 显示模板选择器
    showTemplateSelector() {
      this.loadTemplates();
      this.$refs.templatePopup.open();
    },
    
    // 关闭模板选择器
    closeTemplateSelector() {
      this.$refs.templatePopup.close();
    },
    
    // 选择模板
    selectTemplate(template) {
      this.selectedTemplate = template;
      this.closeTemplateSelector();
    },
    
    // 跳转到模板管理
    goToManage() {
      this.closeTemplateSelector();
      uni.navigateTo({
        url: '/pages/tools/template-manage/index'
      });
    },
    
    // 生成文档
    async generateDocument() {
      if (!this.canGenerate || this.generating) return;
      
      this.generating = true;
      uni.showLoading({ title: 'AI生成中...', mask: true });
      
      try {
        const res = await api.post('/llm/generate', {
          template_id: this.selectedTemplate.id,
          user_input: this.userInput
        });
        
        if (res.code === 'SUCCESS') {
          uni.hideLoading();
          uni.showToast({ title: '生成成功', icon: 'success' });
          
          // 跳转到结果页面
          uni.navigateTo({
            url: `/pages/tools/template-result/index?generationId=${res.data.generation_id}`
          });
        } else {
          uni.hideLoading();
          uni.showToast({ title: res.message || '生成失败', icon: 'none' });
        }
      } catch (e) {
        console.error('生成文档失败:', e);
        uni.hideLoading();
        uni.showToast({ title: '生成失败', icon: 'none' });
      } finally {
        this.generating = false;
      }
    }
  }
};
</script>

<style scoped>
.generate-container {
  min-height: 100vh;
  background-color: #f5f7fa;
  padding: 20rpx;
  padding-bottom: 140rpx;
}

/* 区块样式 */
.template-section,
.input-section {
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
  margin-bottom: 20rpx;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 12rpx;
  font-size: 30rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 20rpx;
}

.title-icon {
  font-size: 36rpx;
}

/* 已选择模板 */
.selected-template {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20rpx;
  background: #f8f9fa;
  border-radius: 12rpx;
}

.template-info {
  display: flex;
  align-items: center;
  gap: 20rpx;
  flex: 1;
  min-width: 0;
}

.file-icon {
  font-size: 48rpx;
  width: 80rpx;
  height: 80rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12rpx;
  flex-shrink: 0;
}

.template-detail {
  flex: 1;
  min-width: 0;
}

.template-name {
  font-size: 30rpx;
  font-weight: 500;
  color: #333;
  display: block;
  margin-bottom: 8rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.template-tags {
  font-size: 24rpx;
  color: #999;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.change-btn {
  padding: 12rpx 24rpx;
  background: #007bff;
  border-radius: 8rpx;
}

.change-btn text {
  font-size: 26rpx;
  color: #fff;
}

/* 选择模板按钮 */
.select-template-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60rpx;
  border: 2rpx dashed #d9d9d9;
  border-radius: 12rpx;
  gap: 16rpx;
}

.select-icon {
  font-size: 48rpx;
  color: #999;
  font-weight: 300;
}

.select-text {
  font-size: 28rpx;
  color: #999;
}

/* 输入区域 */
.info-textarea {
  width: 100%;
  min-height: 400rpx;
  padding: 20rpx;
  border: 2rpx solid #e8e8e8;
  border-radius: 12rpx;
  font-size: 28rpx;
  line-height: 1.6;
  color: #333;
  box-sizing: border-box;
}

.input-tips {
  display: flex;
  align-items: center;
  gap: 8rpx;
  margin-top: 16rpx;
  padding: 16rpx;
  background: #e6f7ff;
  border-radius: 8rpx;
}

.tips-icon {
  font-size: 28rpx;
}

.tips-text {
  font-size: 26rpx;
  color: #007bff;
}

/* 生成按钮 */
.action-section {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  padding: 20rpx 40rpx 40rpx;
  background: #fff;
  box-shadow: 0 -4rpx 20rpx rgba(0, 0, 0, 0.08);
}

.generate-btn {
  padding: 28rpx 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12rpx;
  text-align: center;
}

.generate-btn.disabled {
  background: #d9d9d9;
}

.btn-text {
  font-size: 32rpx;
  color: #fff;
  font-weight: 500;
}

/* 模板选择弹窗 */
.template-selector {
  background: #fff;
  border-radius: 24rpx 24rpx 0 0;
  max-height: 70vh;
  display: flex;
  flex-direction: column;
}

.selector-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 30rpx;
  border-bottom: 2rpx solid #f0f0f0;
}

.selector-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
}

.selector-close {
  font-size: 40rpx;
  color: #999;
  padding: 0 10rpx;
}

.template-list {
  max-height: 50vh;
  padding: 20rpx;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80rpx 40rpx;
}

.empty-text {
  font-size: 30rpx;
  color: #333;
  margin-bottom: 10rpx;
}

.empty-subtext {
  font-size: 26rpx;
  color: #999;
}

.template-item {
  display: flex;
  align-items: center;
  gap: 20rpx;
  padding: 24rpx;
  border-radius: 12rpx;
  margin-bottom: 16rpx;
  background: #f8f9fa;
}

.template-item.selected {
  background: #e6f7ff;
  border: 2rpx solid #007bff;
}

.item-icon {
  font-size: 48rpx;
  width: 72rpx;
  height: 72rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
  border-radius: 12rpx;
  flex-shrink: 0;
}

.item-info {
  flex: 1;
  min-width: 0;
}

.item-name {
  font-size: 30rpx;
  color: #333;
  display: block;
  margin-bottom: 8rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-tags {
  font-size: 24rpx;
  color: #999;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.check-icon {
  width: 48rpx;
  height: 48rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #007bff;
  border-radius: 50%;
  flex-shrink: 0;
}

.check-icon text {
  font-size: 28rpx;
  color: #fff;
}

.selector-footer {
  padding: 20rpx 30rpx 40rpx;
  border-top: 2rpx solid #f0f0f0;
}

.manage-btn {
  padding: 24rpx 0;
  background: #f5f7fa;
  border-radius: 12rpx;
  text-align: center;
}

.manage-btn text {
  font-size: 30rpx;
  color: #666;
}
</style>
