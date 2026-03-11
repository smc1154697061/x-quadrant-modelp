<script>
	// 导入安全存储函数 - 所有平台通用
	import { safeGetStorage, safeSetStorage } from './utils/platform-adapter.js';
	import { verifyToken, isAuthRequired } from './utils/auth.js';
	
	// 微信小程序环境特定的处理
	// #ifdef MP-WEIXIN
	import { setupGlobalErrorHandler } from './utils/error-handler.js';

	try {
		// 初始化微信小程序错误处理
		setupGlobalErrorHandler();
	} catch (err) {
		console.error('[应用初始化] 微信小程序错误处理设置失败:', err);
	}
	// #endif

	export default {
		data() {
			return {
				isPc: false, // 是否为PC端
				windowWidth: 0, // 窗口宽度
				userInfo: null // 用户信息
			}
		},
		globalData: {
			userInfo: null,
			isLoggedIn: false,
			isPc: false,
			navBarHeight: 44,
			statusBarHeight: 20
		},
		onLaunch: function() {
			// #ifdef MP-WEIXIN
			// 设置微信小程序特定选项
			if (typeof wx !== 'undefined') {
				try {
					// 关闭框架警告 - 仅在真机环境尝试调用
					if (typeof wx.setInnerAudioOption === 'function') {
						// 检查是否在开发者工具中
						const systemInfo = wx.getSystemInfoSync();
						const isDevTools = systemInfo.platform === 'devtools';
						
						if (!isDevTools) {
							// 只在真机上调用此API
							wx.setInnerAudioOption({
								obeyMuteSwitch: false
							}).catch(err => {
								console.warn('[音频设置] 设置音频选项失败，但不影响使用:', err);
							});
						}
					}
					
					// 打开调试
					if (typeof wx.setEnableDebug === 'function') {
						wx.setEnableDebug({
							enableDebug: true
						}).catch(err => {
							console.warn('[调试设置] 启用调试失败，但不影响使用:', err);
						});
					}
				} catch (err) {
					console.error('[应用初始化] 微信小程序特定设置失败:', err);
				}
			}
			// #endif
			
			// 强制验证token有效性
			this.validateTokenOnStartup()
			// 初始化加载用户信息
			this.loadUserInfo()
			// 设置请求拦截器
			this.setupRequestInterceptor()
			// 检测设备类型
			this.checkDeviceType()
			// 设置导航栏高度
			this.setNavBarHeight()
			
			// 监听用户信息更新事件
			uni.$on('userInfoUpdated', this.handleUserInfoUpdated)
		},
		onShow: function() {
			// 触发全局onShow事件
			uni.$emit('onShow')
		},
		onHide: function() {
			console.log('App Hide');
			// App隐藏
		},
		onError: function(err) {
			console.error('[应用错误]', err);
		},
		onUnhandledRejection: function(err) {
			console.error('[未处理的Promise拒绝]', err);
		},
		destroyed() {
			// 移除事件监听
			// #ifdef H5
			window.removeEventListener('resize', this.handleResize)
			// #endif
			uni.$off('userInfoUpdated', this.handleUserInfoUpdated)
		},
		methods: {
			// 验证Token有效性
			validateTokenOnStartup() {
				const token = safeGetStorage('token');
				if (token) {
					// 使用静态导入的verifyToken函数
					verifyToken().then(valid => {
						if (!valid) {
							uni.removeStorageSync('token');
							uni.removeStorageSync('token_backup');
							uni.removeStorageSync('userInfo');
							
							// 更新全局状态
							this.userInfo = null;
							if (getApp()) {
								getApp().globalData = getApp().globalData || {};
								getApp().globalData.userInfo = null;
								getApp().globalData.isLoggedIn = false;
							}
							
							// 获取当前页面路径
							const pages = getCurrentPages();
							if (pages.length > 0) {
								const currentPage = pages[pages.length - 1];
								const path = `/${currentPage.route}`;
								
								// 检查当前页面是否需要登录
								if (isAuthRequired(path)) {
									// 保存当前路径，登录后可以跳回
									safeSetStorage('redirectUrl', path);
									
									uni.reLaunch({
										url: '/pages/user/login/index'
									});
								}
							}
						} else {
							// 更新全局状态
							if (getApp()) {
								getApp().globalData = getApp().globalData || {};
								getApp().globalData.isLoggedIn = true;
							}
						}
					}).catch(err => {
						console.error('验证token时出错:', err);
						// 出错时也应清除token
						uni.removeStorageSync('token');
						uni.removeStorageSync('token_backup');
						uni.removeStorageSync('userInfo');
						
						// 更新全局状态
						this.userInfo = null;
						if (getApp()) {
							getApp().globalData = getApp().globalData || {};
							getApp().globalData.userInfo = null;
							getApp().globalData.isLoggedIn = false;
						}
						
						// 显示错误提示
						uni.showToast({
							title: '服务暂时不可用，请稍后再试',
							icon: 'none',
							duration: 2000
						});
						
						// 获取当前页面路径
						const pages = getCurrentPages();
						if (pages.length > 0) {
							const currentPage = pages[pages.length - 1];
							const path = `/${currentPage.route}`;
							
							// 检查当前页面是否需要登录
							if (isAuthRequired(path)) {
								// 保存当前路径，登录后可以跳回
								safeSetStorage('redirectUrl', path);
								
								// 延迟跳转，让用户有时间看到提示
								setTimeout(() => {
									uni.reLaunch({
										url: '/pages/user/login/index'
									});
								}, 1500);
							}
						}
					});
				} else {
					// 获取当前页面路径，检查是否需要登录
					const pages = getCurrentPages();
					if (pages.length > 0) {
						const currentPage = pages[pages.length - 1];
						const path = `/${currentPage.route}`;
						
						// 检查当前页面是否需要登录
						if (isAuthRequired(path)) {
							// 保存当前路径，登录后可以跳回
							safeSetStorage('redirectUrl', path);
							
							uni.reLaunch({
								url: '/pages/user/login/index'
							});
						}
					}
				}
			},
			// 加载用户信息
			loadUserInfo() {
				try {
					// 从本地存储获取token和用户信息
					const token = safeGetStorage('token')
					const userInfoStr = safeGetStorage('userInfo')
					
					// 解析用户信息
					let userInfo = null
					if (userInfoStr) {
						try {
							userInfo = typeof userInfoStr === 'string' ? JSON.parse(userInfoStr) : userInfoStr
						} catch (e) {
							console.error('解析用户信息失败:', e)
							userInfo = null
						}
					}
					
					// 设置用户信息
					this.userInfo = userInfo
					
					// 设置全局状态
					const app = getApp()
					if (app) {
						app.globalData = app.globalData || {}
						app.globalData.userInfo = userInfo
						app.globalData.isLoggedIn = !!userInfo
					}
				} catch (error) {
					console.error('加载用户信息时发生错误:', error)
					this.clearUserInfo()
				}
			},
			
			// 清除用户信息
			clearUserInfo() {
				// 清除本地存储
				uni.removeStorageSync('token')
				uni.removeStorageSync('token_backup')
				uni.removeStorageSync('userInfo')
				
				// 清除内存中的用户信息
				this.userInfo = null
				
				// 更新全局状态
				const app = getApp()
				if (app) {
					app.globalData = app.globalData || {}
					app.globalData.userInfo = null
					app.globalData.isLoggedIn = false
				}
			},
			
			// 处理用户信息更新事件
			handleUserInfoUpdated(userData) {
				if (userData) {
					// 更新用户信息
					this.userInfo = userData
					
					// 更新全局状态
					const app = getApp()
					if (app) {
						app.globalData = app.globalData || {}
						app.globalData.userInfo = userData
						app.globalData.isLoggedIn = true
					}
				} else {
					// 清除用户信息
					this.clearUserInfo()
				}
			},
			
			// 设置请求拦截器
			setupRequestInterceptor() {
				// 添加请求拦截器
				uni.addInterceptor('request', {
					success: (res) => {
						// 处理401未授权状态码
						if (res.statusCode === 401) {
							// 清除本地存储的用户信息和token
							uni.removeStorageSync('userInfo');
							uni.removeStorageSync('token');
							
							// 更新全局状态
							this.userInfo = null;
							
							// 显示提示
							uni.showToast({
								title: '登录已过期，请重新登录',
								icon: 'none',
								duration: 2000
							});
							
							// 跳转到登录页
							setTimeout(() => {
								uni.reLaunch({
									url: '/pages/user/login/index'
								});
							}, 1000);
							
							// 返回修改后的响应
							return {
								...res,
								data: {
									code: 'UNAUTHORIZED',
									message: '登录已过期，请重新登录',
									data: null
								}
							};
						}
						
						return res;
					}
				});
			},
			
			// 检测设备类型
			checkDeviceType() {
				uni.getSystemInfo({
					success: (res) => {
						this.windowWidth = res.windowWidth;
						// 判断是否为PC端（宽度大于等于768px）
						this.isPc = res.windowWidth >= 768;
						
						// 设置全局状态
						const app = getApp();
						if (app) {
							app.globalData = app.globalData || {};
							app.globalData.isPc = this.isPc;
							app.globalData.windowWidth = this.windowWidth;
							app.globalData.systemInfo = res;
						}
						
						// 监听窗口大小变化（仅在H5环境下有效）
						// #ifdef H5
						window.addEventListener('resize', this.handleResize);
						// #endif
					}
				});
			},
			
			// 处理窗口大小变化
			handleResize() {
				// #ifdef H5
				const newWidth = window.innerWidth
				
				// 判断是否为PC端（宽度大于等于768px）
				const newIsPc = newWidth >= 768
				
				// 如果设备类型发生变化，更新状态
				if (this.isPc !== newIsPc) {
					this.isPc = newIsPc
					this.windowWidth = newWidth
					
					// 更新全局状态
					const app = getApp()
					if (app) {
						app.globalData = app.globalData || {}
						app.globalData.isPc = this.isPc
						app.globalData.windowWidth = this.windowWidth
						
						// 触发全局事件
						uni.$emit('deviceTypeChanged', { isPc: this.isPc, windowWidth: this.windowWidth })
					}
				}
				// #endif
			},
			
			// 设置导航栏高度
			setNavBarHeight() {
				try {
					// 先声明一次，避免重复声明报错
					let statusBarHeight = 20;
					// #ifdef MP-WEIXIN
					const windowInfo = wx.getWindowInfo();
					const appBaseInfo = wx.getAppBaseInfo();
					statusBarHeight = appBaseInfo.statusBarHeight || 20;
					// #endif
					
					// #ifndef MP-WEIXIN
					const systemInfo = uni.getSystemInfoSync();
					statusBarHeight = systemInfo.statusBarHeight || 20;
					// #endif
					
					// 不同平台的导航栏高度
					let navBarHeight = 44; // 默认值
					
					// #ifdef MP-WEIXIN
					navBarHeight = 48;
					// #endif
					
					// #ifdef MP-ALIPAY
					navBarHeight = 45;
					// #endif
					
					// #ifdef APP-PLUS
					navBarHeight = 44;
					// #endif
					
					// 总高度 = 状态栏高度 + 导航栏高度
					const totalNavHeight = statusBarHeight + navBarHeight;
					
					// 设置全局状态
					const app = getApp();
					if (app) {
						app.globalData = app.globalData || {};
						app.globalData.statusBarHeight = statusBarHeight;
						app.globalData.navBarHeight = navBarHeight;
						app.globalData.totalNavHeight = totalNavHeight;
					}
				} catch (error) {
					console.error('设置导航栏高度失败:', error);
				}
			}
		}
	}
</script>

<style>
	/**
	 * 应用全局样式
	 */

	/* 页面通用样式 */
	page {
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans',
			'Helvetica Neue', sans-serif;
		font-size: 28rpx;
		line-height: 1.5;
		color: #333;
		background-color: #f5f7fa;
		box-sizing: border-box;
		-webkit-font-smoothing: antialiased;
		-moz-osx-font-smoothing: grayscale;
		
		/* 全局CSS变量 */
		--status-bar-height: 0px;
		--nav-bar-height: 44px;
		--safe-area-bottom: 0px;
		--tab-bar-height: 50px;
		--sidebar-width: 220px;
		--window-height: 100vh;
		--window-width: 100vw;
		--mobile-content-height: calc(100vh - var(--nav-bar-height) - var(--tab-bar-height) - var(--safe-area-bottom));
		--pc-content-height: calc(100vh - var(--nav-bar-height));
		--content-height: var(--mobile-content-height); /* 默认使用移动端高度 */
		--tab-bar-bottom: var(--safe-area-bottom);
		--is-pc: 0; /* 默认为移动端 */
		
		/* 颜色方案 */
		--primary-color: #007bff;
		--secondary-color: #6c757d;
		--success-color: #4caf50;
		--danger-color: #f44336;
		--warning-color: #ff9800;
		--info-color: #2196F3;
		--light-color: #f8f9fa;
		--dark-color: #343a40;
		--border-color: #e0e0e0;
		--text-color: #333333;
		--background-color: #f5f7fa;
		
		/* 页面内容宽度限制 */
		--content-max-width: 1200px;
		
		height: 100%;
		width: 100%;
		padding-top: 0 !important;  /* 重要：防止顶部空白区域 */
	}

	/* 移除默认边距 */
	view, text, navigator, button, image {
		margin: 0;
		padding: 0;
		box-sizing: border-box;
	}

	/* 按钮通用样式 */
	button {
		padding: 0;
		margin: 0;
		border-radius: 8rpx;
		border: none;
		line-height: 1;
		background: none;
		position: relative;
		font-size: 28rpx;
		border-radius: 8rpx;
		background-color: #f8f9fa;
		color: #333;
		border: 1rpx solid #ddd;
		padding: 16rpx 30rpx;
		transition: all 0.3s ease;
		height: auto;
		box-shadow: 0 2rpx 4rpx rgba(0, 0, 0, 0.05);
		display: flex;
		align-items: center;
		justify-content: center;
		box-sizing: border-box;
	}

	button::after {
		border: none;
	}

	/* 超链接样式 */
	a {
		color: var(--primary-color);
		text-decoration: none;
	}

	a:hover {
		text-decoration: underline;
	}

	/* 禁用元素样式 */
	.disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	/* 文本框样式 */
	input, textarea {
		border: 1rpx solid #ddd;
		border-radius: 8rpx;
		padding: 20rpx;
		font-size: 28rpx;
	}

	input:focus, textarea:focus {
		border-color: var(--primary-color);
		outline: none;
	}

	/* 滚动区域样式 */
	.scroll-view {
		width: 100%;
		height: 100%;
	}

	/* 图标基础样式 */
	.icon {
		width: 32rpx;
		height: 32rpx;
	}

	/* 卡片样式 */
	.card {
		background-color: #fff;
		border-radius: 12rpx;
		box-shadow: 0 2rpx 10rpx rgba(0, 0, 0, 0.05);
		margin-bottom: 20rpx;
		overflow: hidden;
	}

	.card-header {
		padding: 20rpx;
		border-bottom: 1rpx solid #f0f0f0;
		font-weight: bold;
	}

	.card-body {
		padding: 20rpx;
	}

	.card-footer {
		padding: 20rpx;
		border-top: 1rpx solid #f0f0f0;
	}

	/* 常用辅助类 */
	.text-center {
		text-align: center;
	}

	.text-right {
		text-align: right;
	}

	.text-left {
		text-align: left;
	}

	.flex {
		display: flex;
	}

	.flex-column {
		flex-direction: column;
	}

	.justify-center {
		justify-content: center;
	}

	.align-center {
		align-items: center;
	}

	.space-between {
		justify-content: space-between;
	}

	.flex-wrap {
		flex-wrap: wrap;
	}

	.flex-1 {
		flex: 1;
	}

	.mt-10 {
		margin-top: 10rpx;
	}

	.mt-20 {
		margin-top: 20rpx;
	}

	.mb-10 {
		margin-bottom: 10rpx;
	}

	.mb-20 {
		margin-bottom: 20rpx;
	}

	.ml-10 {
		margin-left: 10rpx;
	}

	.ml-20 {
		margin-left: 20rpx;
	}

	.mr-10 {
		margin-right: 10rpx;
	}

	.mr-20 {
		margin-right: 20rpx;
	}

	.p-10 {
		padding: 10rpx;
	}

	.p-20 {
		padding: 20rpx;
	}

	/* 隐藏滚动条但允许滚动 */
	::-webkit-scrollbar {
		display: none;
		width: 0 !important;
		height: 0 !important;
		-webkit-appearance: none;
		background: transparent;
	}

	/* 通用样式 */
	.container {
		padding: 20rpx;
		height: 100%;
		display: flex;
		flex-direction: column;
	}
	
	/* App容器样式 */
	.app-container {
		height: 100%;
		width: 100%;
		display: flex;
		flex-direction: column;
	}
	
	/* 页面内容区域 - 移动端 */
	.page-content-mobile {
		flex: 1;
		height: var(--mobile-content-height);
		overflow-y: auto;
		position: relative;
		box-sizing: border-box;
	}
	
	/* 页面内容区域 - PC端 */
	.page-content-pc {
		flex: 1;
		height: var(--pc-content-height);
		overflow-y: auto;
		position: relative;
		box-sizing: border-box;
	}
	
	/* PC端布局 */
	.pc-layout {
		display: flex;
		width: 100%;
		height: 100%;
	}
	
	/* PC端侧边栏 */
	.pc-sidebar {
		width: var(--sidebar-width);
		height: 100%;
		background-color: #fff;
		border-right: 1px solid var(--border-color);
		box-shadow: 2rpx 0 10rpx rgba(0, 0, 0, 0.05);
		overflow-y: auto;
		padding: 20rpx 0;
		box-sizing: border-box;
		position: fixed;
		left: 0;
		top: 0;
		z-index: 100;
	}
	
	/* PC端内容区 */
	.pc-content {
		flex: 1;
		margin-left: var(--sidebar-width);
		box-sizing: border-box;
	}
	
	/* PC侧边栏导航项 */
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
		margin-right: 15rpx;
		font-size: 36rpx;
	}
	
	.pc-nav-text {
		font-size: 28rpx;
	}
	
	/* 主要按钮 */
	button[type="primary"],
	.primary-btn,
	.send-button,
	.extract-button {
		background-color: var(--primary-color);
		color: white;
		border: none;
	}
	
	/* 小型按钮 */
	button.small-btn,
	.example-btn,
	.copy-btn,
	.clear-btn,
	.history-btn,
	.delete-btn {
		font-size: 24rpx;
		padding: 8rpx 20rpx;
		line-height: 1;
		border-radius: 30rpx;
		height: 58rpx;
	}
	
	/* 危险操作按钮 */
	button.danger-btn,
	.delete-btn {
		background-color: #f8d7da;
		color: #721c24;
		border: 1rpx solid #f5c6cb;
	}
	
	/* 信息型按钮 */
	button.info-btn,
	.use-btn {
		background-color: #e7f3fe;
		color: #0c5460;
		border: 1rpx solid #d1ecf1;
	}
	
	/* 活跃时样式 */
	button[type="primary"]:not([disabled]):active,
	.primary-btn:not([disabled]):active,
	.send-button:not([disabled]):active,
	.extract-button:not([disabled]):active {
		background-color: #0056b3;
		transform: translateY(2rpx);
	}
	
	/* 禁用状态 */
	button[disabled] {
		background-color: #e9ecef;
		color: #6c757d;
		cursor: not-allowed;
	}

	/* PC端响应式布局 */
	@media screen and (min-width: 768px) {
		page {
			--content-height: var(--pc-content-height); /* PC端使用PC高度变量 */
		}
		
		.chat-container,
		.knowledge-container,
		.extraction-container {
			max-width: 100% !important; /* 修改为100%，因为我们会通过侧边栏布局控制宽度 */
			width: 100% !important;
			margin: 0;
			box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.1);
			border-radius: 20rpx;
			background-color: #fff;
			padding: 40rpx !important;
			box-sizing: border-box;
		}
		
		/* PC端按钮尺寸控制 */
		button {
			height: 72rpx;
			line-height: 1;
			display: flex;
			align-items: center;
			justify-content: center;
		}
		
		/* 主要按钮在PC端的特殊样式 */
		button[type="primary"],
		.primary-btn,
		.send-button,
		.extract-button {
			height: 72rpx;
			min-width: 140rpx;
			padding: 0 30rpx;
		}
		
		/* PC端按钮悬停效果 */
		button:not([disabled]):hover,
		.primary-btn:not([disabled]):hover,
		.send-button:not([disabled]):hover,
		.extract-button:not([disabled]):hover {
			filter: brightness(1.05);
			box-shadow: 0 4rpx 8rpx rgba(0, 0, 0, 0.1);
		}
		
		button:hover {
			opacity: 0.8;
		}
		
		button[type="primary"]:not([disabled]):hover,
		.primary-btn:not([disabled]):hover,
		.send-button:not([disabled]):hover,
		.extract-button:not([disabled]):hover {
			background-color: #0069d9;
		}
		
		button.danger-btn:not([disabled]):hover,
		.delete-btn:not([disabled]):hover {
			background-color: #f1b0b7;
		}
		
		button.info-btn:not([disabled]):hover,
		.use-btn:not([disabled]):hover {
			background-color: #d1ecf1;
		}
	}

	/* 导航栏样式 */
	.nav-active {
		color: var(--primary-color) !important;
	}

	/* 底部版权信息样式 */
	.footer-text {
		font-size: 24rpx;
		color: #999;
		text-align: center;
		padding: 30rpx 0;
	}
	
	/* 固定导航栏底部安全区域 */
	.safe-area-bottom {
		padding-bottom: constant(safe-area-inset-bottom);
		padding-bottom: env(safe-area-inset-bottom);
	}
	
	/* TabBar样式修正 - 仅移动端显示 */
	.uni-tabbar {
		height: calc(var(--tab-bar-height) + var(--safe-area-bottom)) !important;
		padding-bottom: var(--safe-area-bottom) !important;
	}
	
	/* PC端隐藏TabBar */
	@media screen and (min-width: 768px) {
		.uni-tabbar {
			display: none !important;
		}
	}

	/* 隐藏原生导航栏 */
	.uni-page-head {
		display: none !important;
	}
	
	/* 隐藏uni-app自带的导航栏 */
	uni-page-head, .uni-page-head-phantom {
		display: none !important;
		height: 0 !important;
		padding: 0 !important;
		margin: 0 !important;
	}

	/* 确保移动端图片正确渲染 */
	image {
		will-change: transform;
		transform: translateZ(0);
		backface-visibility: hidden;
		-webkit-backface-visibility: hidden;
		z-index: 1;
	}

	/* 修复移动端点击后图片消失问题 */
	.tab-btn image, .mobile-tab-bar image, .tabs image {
		z-index: 20 !important;
		position: relative !important;
		opacity: 1 !important;
		will-change: transform !important;
		transform: translateZ(0) !important;
		-webkit-transform: translateZ(0) !important;
		backface-visibility: hidden !important;
		-webkit-backface-visibility: hidden !important;
		perspective: 1000 !important;
		-webkit-perspective: 1000 !important;
		pointer-events: auto !important;
		visibility: visible !important;
		display: block !important;
	}

	/* 确保所有tab中的图片都能正确显示 */
	.mobile-tab-bar .tab-item image {
		z-index: 30 !important;
		opacity: 1 !important;
		visibility: visible !important;
		display: block !important;
		transform: translateZ(0) !important;
	}

	/* 防止点击时的触摸穿透问题 */
	.mobile-tab-bar, .tabs, .tab-btn {
		touch-action: manipulation !important;
		-webkit-touch-callout: none !important;
		-webkit-user-select: none !important;
		user-select: none !important;
	}

	/* 修复点击闪烁问题 */
	.mobile-tab-bar .tab-item:active {
		opacity: 1 !important;
	}

	.mobile-tab-bar .tab-item:active image {
		opacity: 1 !important;
		visibility: visible !important;
	}

	/* 禁用移动端点击反馈 */
	.mobile-tab-bar .tab-item, 
	.mobile-tab-bar .tab-icon,
	.tabs .tab-btn {
		-webkit-tap-highlight-color: transparent !important;
	}
</style>
