<template>
  <view class="container">
    <!-- 固定头部 -->
    <view class="header">
      <view class="back-btn" @click="goBack">
        <text class="iconfont icon-back"></text>
      </view>
      <view class="title">{{ isEditing ? '编辑机器人' : '创建机器人' }}</view>
      <view class="save-btn" @click="saveBot">
        <text>保存</text>
      </view>
    </view>
    
    <!-- 修改滚动视图，解决H5模拟器溢出问题 -->
    <scroll-view 
      scroll-y 
      class="form-scroll-view"
      :style="{ height: calcScrollHeight }"
      show-scrollbar="false"
      enable-back-to-top="true"
    >
      <view class="form-container">
        <view class="form-item">
          <text class="form-label">机器人名称 <text class="required">*</text></text>
          <input 
            type="text" 
            v-model="botForm.name" 
            placeholder="请输入机器人名称" 
            class="form-input" 
            maxlength="50"
          />
        </view>
        
        <view class="form-item">
          <text class="form-label">描述</text>
          <textarea
            v-model="botForm.description"
            placeholder="请输入机器人描述"
            class="form-textarea"
            maxlength="500"
            :style="{ height: textareaHeight }"
          ></textarea>
        </view>
        
        <view class="form-item">
          <text class="form-label">系统提示词</text>
          <textarea
            v-model="botForm.system_prompt"
            placeholder="输入系统提示词"
            class="form-textarea"
            maxlength="1000"
            :style="{ height: textareaHeight }"
          ></textarea>
        </view>
        
        <view class="form-item">
          <text class="form-label">模型</text>
          <view class="fixed-model-wrapper">
            <text class="fixed-model-name">qwen2:7b</text>
          </view>
        </view>
        
        <view class="form-item">
          <text class="form-label">可见性</text>
          <view class="switch-container">
            <text>私有</text>
            <switch 
              :checked="botForm.is_public" 
              @change="onVisibilityChange" 
              color="#007AFF"
              style="transform: scale(0.8);"
            />
            <text>公开</text>
          </view>
        </view>
        
        <view class="form-item">
          <text class="form-label">关联知识库</text>
          <view class="kb-selector">
            <view 
              v-for="kb in knowledgeBases" 
              :key="kb.id"
              :class="['kb-item', { 'selected': isKbSelected(kb.id) }]"
              @click="toggleKbSelection(kb.id)"
            >
              <text class="kb-name">{{ kb.name }}</text>
              <text class="iconfont" :class="isKbSelected(kb.id) ? 'icon-check' : ''"></text>
            </view>
            
            <view class="no-kb" v-if="knowledgeBases.length === 0">
              <text>暂无可用知识库</text>
            </view>
          </view>
        </view>
        
        <!-- 增加底部安全区域填充 -->
        <view class="safe-area-placeholder" :class="{'xiaomi-extra-padding': isXiaomi, 'h5-extra-padding': isH5}"></view>
      </view>
    </scroll-view>
  </view>
</template>

<script>
import api from '@/utils/api.js';

export default {
  data() {
    return {
      isEditing: false,
      botId: null,
      botForm: {
        name: '',
        description: '',
        system_prompt: '',
        model_name: 'qwen2-7b',
        is_public: false,
        kb_ids: []
      },
      knowledgeBases: [],
      scrollViewHeight: 'auto',
      textareaHeight: '80rpx',
      isXiaomi: false,
      isH5: false,
      headerHeight: 44 // 默认头部高度
    }
  },
  computed: {
    // 计算滚动视图高度，针对H5环境特殊处理
    calcScrollHeight() {
      // 在H5环境中，使用固定高度减去头部高度
      if (this.isH5) {
        return 'calc(100vh - ' + this.headerHeight + 'px)';
      }
      return this.scrollViewHeight;
    }
  },
  onLoad(options) {
    if (options.botId) {
      this.botId = options.botId;
      this.isEditing = true;
      this.loadBotInfo();
    }
    
    // 加载知识库列表
    this.loadKnowledgeBases();
    
    // 检测环境和设备类型
    this.checkDeviceType();
    
    // #ifdef H5
    this.isH5 = true;
    // #endif
    
    // 设置滚动视图高度和文本域高度
    this.setViewHeight();
  },
  onReady() {
    // 确保在页面渲染完成后再次计算高度
    setTimeout(() => {
      this.setViewHeight();
    }, 100);
  },
  methods: {
    // 检测设备类型
    checkDeviceType() {
      try {
        const systemInfo = uni.getSystemInfoSync();
        const brand = systemInfo.brand && systemInfo.brand.toLowerCase();
        this.isXiaomi = brand && brand.indexOf('xiaomi') !== -1;
        
        // 获取头部高度
        this.headerHeight = uni.upx2px(90);
      } catch (e) {
        console.error('获取设备信息失败:', e);
      }
    },
    
    // 设置滚动视图高度和文本域高度
    setViewHeight() {
      try {
        const systemInfo = uni.getSystemInfoSync();
        const screenHeight = systemInfo.screenHeight;
        const windowHeight = systemInfo.windowHeight;
        
        // 计算安全区域
        const safeAreaInsets = systemInfo.safeAreaInsets || {};
        const safeAreaBottom = safeAreaInsets.bottom || 0;
        
        // 计算头部高度（rpx转px）
        const headerHeight = uni.upx2px(90);
        
        // 计算滚动视图高度
        let scrollHeight = windowHeight - headerHeight;
        
        // 小米手机特殊处理
        if (this.isXiaomi) {
          scrollHeight -= uni.upx2px(40); // 增加减去的空间，确保不会溢出
        }
        
        // H5环境特殊处理
        if (this.isH5) {
          // H5环境使用计算属性中的高度计算方式
          // 这里不需要设置scrollViewHeight
        } else {
          // 非H5环境设置滚动视图高度
          this.scrollViewHeight = scrollHeight + 'px';
        }
        
        // 根据屏幕高度动态设置文本域高度
        if (screenHeight < 600) {
          this.textareaHeight = '60rpx';
        } else if (screenHeight < 700) {
          this.textareaHeight = '80rpx';
        } else {
          this.textareaHeight = '100rpx';
        }
      } catch (e) {
        console.error('设置视图高度失败:', e);
      }
    },
    
    // 加载机器人信息
    async loadBotInfo() {
      try {
        const response = await api.get(`/llm/bots/${this.botId}`);
        if (response.code === 'SUCCESS') {
          const botInfo = response.data || {};
          
          // 设置表单数据（确保 kb_ids 中的 ID 都是数字类型）
          this.botForm = {
            name: botInfo.name || '',
            description: botInfo.description || '',
            system_prompt: botInfo.system_prompt || '',
            model_name: botInfo.model_name || this.botForm.model_name,
            is_public: botInfo.is_public || false,
            kb_ids: (botInfo.kb_ids || []).map(id => Number(id)) // 统一转换为数字类型
          };
          
        } else {
          uni.showToast({
            title: '获取机器人信息失败',
            icon: 'none'
          });
        }
      } catch (error) {
        console.error('加载机器人信息出错:', error);
        uni.showToast({
          title: '加载机器人信息失败',
          icon: 'none'
        });
      }
    },
    
    // 加载知识库列表
    async loadKnowledgeBases() {
      try {
        const response = await api.get('/llm/knowledge-bases');
        if (response.code === 'SUCCESS') {
          // 确保知识库 ID 都是数字类型
          const kbs = response.data.knowledge_bases || [];
          this.knowledgeBases = kbs.map(kb => ({
            ...kb,
            id: Number(kb.id) // 统一转换为数字类型
          }));
          
        } else {
          uni.showToast({
            title: '获取知识库列表失败',
            icon: 'none'
          });
        }
      } catch (error) {
        console.error('加载知识库列表出错:', error);
        uni.showToast({
          title: '加载知识库列表失败',
          icon: 'none'
        });
      }
    },
    
    // 保存机器人
    async saveBot() {
      if (!this.botForm.name.trim()) {
        uni.showToast({
          title: '请输入机器人名称',
          icon: 'none'
        });
        return;
      }
      
      try {
        const botData = {
          name: this.botForm.name,
          description: this.botForm.description,
          system_prompt: this.botForm.system_prompt,
          model_name: this.botForm.model_name,
          is_public: this.botForm.is_public,
          kb_ids: this.botForm.kb_ids
        };
        
        let response;
        
        if (this.isEditing) {
          // 更新机器人
          response = await api.put(`/llm/bots/${this.botId}`, botData);
        } else {
          // 创建新机器人
          response = await api.post('/llm/bots', botData);
        }
        
        if (response.code === 'SUCCESS') {
          uni.showToast({
            title: this.isEditing ? '更新成功' : '创建成功',
            icon: 'success'
          });
          
          // 返回上一页
          setTimeout(() => {
            uni.navigateBack();
          }, 1500);
        } else {
          uni.showToast({
            title: response.message || '操作失败',
            icon: 'none'
          });
        }
      } catch (error) {
        console.error('保存机器人失败:', error);
        uni.showToast({
          title: '操作失败',
          icon: 'none'
        });
      }
    },
    
    // 可见性变化
    onVisibilityChange(e) {
      this.botForm.is_public = e.detail.value;
    },
    
    // 检查知识库是否被选中
    isKbSelected(kbId) {
      const isSelected = this.botForm.kb_ids.includes(kbId);
      
      // 调试日志：检查匹配情况
      if (!isSelected && this.botForm.kb_ids.length > 0) {
        // 尝试类型转换匹配
        const hasMatch = this.botForm.kb_ids.some(id => {
          return id == kbId || String(id) === String(kbId);
        });
        if (hasMatch) {
          console.warn('类型不匹配！kb_ids:', this.botForm.kb_ids, '检查的 kbId:', kbId, 'kbId类型:', typeof kbId);
        }
      }
      
      return isSelected;
    },
    
    // 切换知识库选择状态
    toggleKbSelection(kbId) {
      const index = this.botForm.kb_ids.indexOf(kbId);
      if (index === -1) {
        // 添加
        this.botForm.kb_ids.push(kbId);
      } else {
        // 移除
        this.botForm.kb_ids.splice(index, 1);
      }
    },
    
    // 返回上一页
    goBack() {
      uni.navigateBack();
    }
  }
}
</script>

<style lang="scss">
/* 页面容器 */
.container {
  width: 100%;
  height: 100vh;
  background-color: #f5f5f5;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
  overflow: hidden;
  position: relative;
}

/* 固定头部 */
.header {
  width: 100%;
  height: 90rpx;
  background-color: #fff;
  display: flex;
  align-items: center;
  padding: 0 20rpx;
  border-bottom: 1rpx solid #eee;
  flex-shrink: 0;
  z-index: 10;
}

.back-btn {
  padding: 10rpx;
}

.title {
  flex: 1;
  text-align: center;
  font-size: 32rpx;
  font-weight: bold;
}

.save-btn {
  padding: 10rpx 20rpx;
}

/* 滚动视图 - 关键修改 */
.form-scroll-view {
  flex: 1;
  width: 100%;
  position: relative;
  z-index: 1;
  overflow: auto !important;
  -webkit-overflow-scrolling: touch; /* 增强iOS滚动体验 */
}

/* 表单容器 */
.form-container {
  background-color: #fff;
  padding: 15rpx;
  width: 100%;
  box-sizing: border-box;
}

/* 表单项 */
.form-item {
  margin-bottom: 15rpx;
}

/* 输入框 */
.form-input {
  width: 100%;
  height: 60rpx;
  background-color: #f5f5f5;
  border-radius: 8rpx;
  padding: 0 15rpx;
  font-size: 26rpx;
  color: #333;
  box-sizing: border-box;
  
  &.disabled-input {
    background-color: #f0f0f0;
    color: #999;
    display: flex;
    align-items: center;
  }
}

/* 文本域 - 减小高度 */
.form-textarea {
  width: 100%;
  background-color: #f5f5f5;
  border-radius: 8rpx;
  padding: 10rpx;
  font-size: 26rpx;
  color: #333;
  box-sizing: border-box;
  min-height: 60rpx;
}

/* 表单标签 */
.form-label {
  display: block;
  font-size: 26rpx;
  color: #333;
  margin-bottom: 6rpx;
  
  .required {
    color: #ff4d4f;
  }
}

/* 开关容器 */
.switch-container {
  display: flex;
  align-items: center;
  height: 45rpx;
  
  text {
    font-size: 26rpx;
    color: #666;
    margin: 0 15rpx;
  }
}

/* 知识库选择器 */
.kb-selector {
  .kb-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8rpx;
    background-color: #f5f5f5;
    border-radius: 6rpx;
    margin-bottom: 6rpx;
    
    &.selected {
      background-color: #e6f7ff;
      border: 1rpx solid #91d5ff;
    }
    
    .kb-name {
      font-size: 26rpx;
      color: #333;
      flex: 1;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    
    .iconfont {
      font-size: 28rpx;
      color: #1890ff;
      margin-left: 8rpx;
    }
  }
  
  .no-kb {
    padding: 10rpx 0;
    text-align: center;
    
    text {
      font-size: 26rpx;
      color: #999;
    }
  }
}

/* 安全区域填充 */
.safe-area-placeholder {
  height: 100rpx;
  padding-bottom: constant(safe-area-inset-bottom);
  padding-bottom: env(safe-area-inset-bottom);
}

/* 隐藏滚动条但允许滚动 */
::-webkit-scrollbar {
  display: none;
  width: 0 !important;
  height: 0 !important;
  -webkit-appearance: none;
  background: transparent;
}

/* 小米手机特殊处理 */
.xiaomi-extra-padding {
  padding-bottom: 50rpx !important;
}

/* H5环境特殊处理 */
.h5-extra-padding {
  padding-bottom: 100rpx !important;
}

/* 适配超小屏幕 */
@media screen and (max-height: 500px) {
  .form-textarea {
    height: 50rpx !important;
  }
  
  .form-item {
    margin-bottom: 10rpx;
  }
  
  .form-label {
    font-size: 24rpx;
    margin-bottom: 4rpx;
  }
  
  .form-input {
    height: 50rpx;
    font-size: 24rpx;
  }
  
  .kb-selector .kb-item {
    padding: 6rpx;
  }
  
  .safe-area-placeholder {
    height: 60rpx;
  }
}

/* 适配小屏幕 */
@media screen and (max-height: 600px) {
  .form-item {
    margin-bottom: 12rpx;
  }
  
  .safe-area-placeholder {
    height: 80rpx;
  }
}

/* 固定模型名称样式 - 使用完全不同的类名 */
.fixed-model-wrapper {
  background-color: #f5f5f5;
  padding: 20rpx;
  border-radius: 8rpx;
  width: 100%;
  box-sizing: border-box;
}

.fixed-model-name {
  font-size: 28rpx;
  color: #666;
  display: inline-block;
}
</style>
