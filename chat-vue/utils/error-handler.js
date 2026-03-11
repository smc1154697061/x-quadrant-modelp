/**
 * 全局错误处理程序
 * 捕获并处理未处理的错误和Promise拒绝
 */

import { normalizeError } from './platform-adapter.js';

/**
 * 初始化全局错误处理器
 */
export function setupGlobalErrorHandler() {
  // 全局未捕获的Promise拒绝处理
  if (typeof window !== 'undefined') {
    // H5环境
    window.addEventListener('unhandledrejection', function(event) {
      console.error('[未处理的Promise拒绝]', event.reason);
    });

    // 全局错误处理
    window.addEventListener('error', function(event) {
      console.error('[全局错误]', event.error);
    });
  }
  
  // 微信小程序环境
  // #ifdef MP-WEIXIN
  if (typeof wx !== 'undefined') {
    try {
      // 监听脚本错误
      wx.onError((error) => {
        console.error('[微信错误]', error);
      });
      
      // 监听未处理的Promise错误
      wx.onUnhandledRejection((res) => {
        console.error('[未处理的Promise]', res.reason);
      });
      
    } catch (err) {
      console.error('[初始化] 设置微信错误处理程序时出错', err);
    }
  }
  // #endif
  
  // App环境
  // #ifdef APP-PLUS
  if (typeof plus !== 'undefined') {
    try {
      plus.globalEvent.addEventListener('error', function(error) {
        console.error('[App错误]', error);
      });
      
    } catch (err) {
      console.error('[初始化] 设置App错误处理程序时出错', err);
    }
  }
  // #endif
}

/**
 * 统一处理错误
 * @param {Error|Object|string} error - 错误对象或消息
 */
function handleError(error) {
  // 首先标准化错误对象
  const normalizedError = normalizeError(error);
  
  // 1. 确定错误类型和消息
  let errorType = normalizedError.name || 'Unknown';
  let errorMessage = normalizedError.message || '未知错误';
  
  // 2. 错误分类和严重程度评估
  const isCritical = errorType.includes('Fatal') || 
                     errorMessage.includes('memory') || 
                     errorMessage.includes('crash');
  
  // 3. 记录错误
  console.group('[错误监控] 错误详情');
  console.error(`类型: ${errorType}`);
  console.error(`消息: ${errorMessage}`);
  console.error(`严重度: ${isCritical ? '严重' : '一般'}`);
  console.error(`时间: ${new Date().toISOString()}`);
  if (normalizedError.stack) {
    console.error(`堆栈: ${normalizedError.stack}`);
  }
  console.groupEnd();
  
  // 4. 处理严重错误 - 可以添加上报逻辑
  if (isCritical) {
    // 这里可以添加错误上报代码
  }
  
  // 5. 对于特定错误，可以尝试恢复或给用户提示
  // 避免过多提示打扰用户体验，只对影响功能的错误提示
  if (errorMessage.includes('network') || 
      errorMessage.includes('timeout') || 
      errorMessage.includes('offline')) {
    
    // 网络相关错误，提示用户
    uni.showToast({
      title: '网络连接异常，请检查网络后重试',
      icon: 'none'
    });
  } else if (isCritical) {
    // 严重错误，提供重启应用的建议
    uni.showModal({
      title: '应用遇到问题',
      content: '请尝试刷新页面或重启应用',
      showCancel: false
    });
  }
  // 其他一般错误静默处理，不打扰用户
}

// 处理API调用错误
export function handleApiError(error, context = '') {
  // 首先标准化错误对象，确保跨平台一致性
  const normalizedError = normalizeError(error);
  
  // 提取错误消息
  const errorMessage = normalizedError.message || normalizedError.msg || normalizedError.errMsg || '未知错误';
  
  // 打印详细错误信息到控制台
  console.error(`[API错误${context ? ' - ' + context : ''}]`, normalizedError);
  console.error('错误消息:', errorMessage);
  
  // 错误通知
  try {
    uni.showToast({
      title: `操作失败: ${errorMessage.slice(0, 50)}${errorMessage.length > 50 ? '...' : ''}`,
      icon: 'none',
      duration: 3000
    });
  } catch (e) {
    console.error('[错误处理] 显示错误提示失败:', e);
    
    // 尝试使用更基础的方式显示错误
    try {
      alert(`操作失败: ${errorMessage}`);
    } catch (innerE) {
      console.error('[错误处理] 备用错误提示也失败:', innerE);
    }
  }
  
  return errorMessage;
}

export default {
  setupGlobalErrorHandler,
  handleApiError
}; 