<template>
  <view class="pc-sidebar">
    <!-- 侧边栏头部 - Logo区域 -->
    <view class="sidebar-header">
      <image class="logo" :src="logoSrc" mode="aspectFit"></image>
      <text class="app-name">渡渡鸟知识库</text>
    </view>
    
    <!-- 导航菜单 -->
    <view class="sidebar-nav">
      <view 
        v-for="(item, index) in navItems" 
        :key="index"
        class="pc-nav-item"
        :class="{ active: isActive(item.pagePath) }"
        @tap="navigateTo(item.pagePath)"
      >
        <image class="pc-nav-icon" :src="isActive(item.pagePath) ? item.selectedIconPath : item.iconPath" mode="aspectFit"></image>
        <text class="pc-nav-text" :class="{ 'nav-active': isActive(item.pagePath) }">{{ item.text }}</text>
      </view>
    </view>
    
    <!-- 侧边栏底部 - 版权信息 -->
    <view class="sidebar-footer">
      <text class="footer-text">© 2025 渡渡鸟知识库</text>
    </view>
  </view>
</template>

<script>
import chatIcon from '@/static/images/chat.png'
import knowledgeIcon from '@/static/images/knowledge.png'
import extractionIcon from '@/static/images/extraction.png'
import logoImage from '@/static/images/logo.png'

export default {
  name: 'PcSidebar',
  data() {
    return {
      currentPath: '',
      // 导航菜单项，只包含主要功能
      navItems: [
        {
          pagePath: '/pages/knowledge-base/index',
          text: '知识库管理',
          iconPath: knowledgeIcon,
          selectedIconPath: knowledgeIcon
        },
        {
          pagePath: '/pages/bot-modules/bot-list/index',
          text: '智能对话',
          iconPath: chatIcon,
          selectedIconPath: chatIcon
        },
        {
          pagePath: '/pages/tools/index',
          text: '工具',
          iconPath: extractionIcon,
          selectedIconPath: extractionIcon
        }
      ],
      logoSrc: logoImage
    }
  },
  created() {
    // 获取当前页面路径
    this.getCurrentPagePath();
    
    // 监听页面切换事件
    uni.$on('pageChange', this.handlePageChange);
  },
  unmounted() {
    // 移除事件监听
    uni.$off('pageChange', this.handlePageChange);
  },
  methods: {
    // 获取当前页面路径
    getCurrentPagePath() {
      const pages = getCurrentPages();
      if (pages.length > 0) {
        const currentPage = pages[pages.length - 1];
        this.currentPath = `/${currentPage.route}`;
      }
    },
    
    // 处理页面切换事件
    handlePageChange(data) {
      if (data && data.path) {
        this.currentPath = data.path;
      }
    },
    
    // 导航到指定页面
    navigateTo(path) {
      if (this.currentPath === path) return;
      
      // 使用适当的导航方法
      if (path.startsWith('/pages/')) {
        uni.navigateTo({
          url: path,
          success: () => {
            this.currentPath = path;
          },
          fail: (err) => {
            // 尝试使用switchTab导航到tabBar页面
            uni.switchTab({
              url: path
            });
          }
        });
      }
    },
    
    // 检查当前页面是否激活
    isActive(pagePath) {
      // 处理智能对话页面的特殊情况
      if (pagePath === '/pages/bot-modules/bot-list/index') {
        // 直接检查当前路径是否以智能对话相关路径开头
        return this.currentPath.startsWith('/pages/bot-modules/') || 
               this.currentPath.startsWith('/pages/chat-modules/');
      }
      
      // 处理知识库详情页面的特殊情况
      if (pagePath === '/pages/knowledge-base/index' && 
          this.currentPath.startsWith('/pages/knowledge-base/')) {
        return true;
      }
      
      // 处理内容提取页面
      if (pagePath === '/pages/tools/index') {
        return this.currentPath.startsWith('/pages/tools/');
      }
      
      // 普通路径匹配
      return this.currentPath === pagePath;
    }
  }
}
</script>

<style>
.pc-sidebar {
  width: var(--sidebar-width);
  height: 100vh;
  background-color: #fff;
  border-right: 1px solid var(--border-color);
  box-shadow: 2rpx 0 10rpx rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
  position: fixed;
  left: 0;
  top: 0;
  z-index: 100;
  transition: transform 0.3s ease;
}

/* 在小屏幕上隐藏侧边栏 */
@media (max-width: 767px) {
  .pc-sidebar {
    transform: translateX(-100%);
  }
}

.sidebar-header {
  padding: 30rpx 20rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  border-bottom: 1px solid var(--border-color);
}

.logo {
  width: 100rpx;
  height: 100rpx;
  margin-bottom: 10rpx;
}

.app-name {
  font-size: 28rpx;
  font-weight: bold;
  color: var(--primary-color);
}

.sidebar-nav {
  flex: 1;
  padding: 20rpx 0;
  overflow-y: auto;
}

.pc-nav-item {
  display: flex;
  align-items: center;
  padding: 20rpx 30rpx;
  cursor: pointer;
  transition: all 0.3s;
}

.pc-nav-item:hover {
  background-color: #f5f7fa;
}

.pc-nav-item.active {
  background-color: #e7f3fe;
  border-left: 4rpx solid var(--primary-color);
}

.pc-nav-icon {
  width: 40rpx;
  height: 40rpx;
  margin-right: 15rpx;
  opacity: 0.6;
}

.active .pc-nav-icon {
  opacity: 1;
}

.pc-nav-text {
  font-size: 28rpx;
  color: #333;
}

.nav-active {
  color: var(--primary-color) !important;
  font-weight: 500;
}

.sidebar-footer {
  padding: 20rpx;
  border-top: 1px solid var(--border-color);
  text-align: center;
}

.footer-text {
  font-size: 22rpx;
  color: #999;
}

.sender-avatar {
  width: 40rpx;
  height: 40rpx;
  border-radius: 50%;
  margin-right: 10rpx;
}
</style> 