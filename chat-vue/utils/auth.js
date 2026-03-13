/**
 * 认证与权限管理工具
 */

import api, { BASE_URL } from './api.js';
import { safeGetStorage, safeSetStorage } from './platform-adapter.js';

// 需要登录才能访问的页面路径列表
const authRequiredPages = [
  '/pages/knowledge-base/index',
  '/pages/knowledge-base/detail',
  '/pages/chat-modules/chat/index',
  '/pages/bot-modules/bot-list/index',
  '/pages/tools/index',
  '/pages/organization/index',
  '/pages/organization/detail'
];

/**
 * 检查页面是否需要登录
 * @param {String} path 页面路径
 * @returns {Boolean} 是否需要登录
 */
export function isAuthRequired(path) {
  return authRequiredPages.some(page => path.startsWith(page));
}

/**
 * 检查用户是否已登录
 * @returns {Boolean} 是否已登录
 */
export function isLoggedIn() {
  const token = safeGetStorage('token');
  const userInfoStr = safeGetStorage('userInfo');
  
  if (!token || !userInfoStr) {
    return false;
  }
  
  try {
    const userInfo = typeof userInfoStr === 'string' ? JSON.parse(userInfoStr) : userInfoStr;
    
    // 基本验证：确保用户信息包含必要字段
    if (!userInfo || !userInfo.id || !userInfo.email) {
      return false;
    }
    
    return true;
  } catch (e) {
    console.error('解析用户信息失败:', e);
    return false;
  }
}

/**
 * 获取当前用户信息
 * @returns {Object|null} 用户信息对象，未登录时返回null
 */
export function getCurrentUser() {
  const userInfoStr = safeGetStorage('userInfo');
  
  if (!userInfoStr) {
    return null;
  }
  
  try {
    return typeof userInfoStr === 'string' ? JSON.parse(userInfoStr) : userInfoStr;
  } catch (e) {
    console.error('解析用户信息失败:', e);
    return null;
  }
}

/**
 * 验证token有效性
 * @returns {Promise} 验证结果Promise
 */
export function verifyToken() {
  return new Promise((resolve, reject) => {
    const token = safeGetStorage('token');
    
    if (!token) {
      resolve(false);
      return;
    }
    
    
    // 直接使用请求头中带token的方式验证
    uni.request({
      url: `${BASE_URL}/auth/verify-token`,
      method: 'POST',
      header: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      success: function(res) {
        if (res.statusCode === 200 && res.data && (res.data.code === '0000' || res.data.code === 'SUCCESS')) {
          // 验证成功，更新用户信息
          const userData = res.data.data;
          
          if (!userData || !userData.email) {
            console.error('返回的用户数据无效');
            // 清除无效的token和用户信息
            uni.removeStorageSync('userInfo');
            uni.removeStorageSync('token');
            resolve(false);
            return;
          }
          
          // 保存到本地存储
          safeSetStorage('userInfo', JSON.stringify(userData));
          
          // 触发全局事件
          uni.$emit('userInfoUpdated', userData);
          
          resolve(true);
        } else {
          // 验证失败，清除用户信息
          uni.removeStorageSync('userInfo');
          uni.removeStorageSync('token');
          resolve(false);
        }
      },
      fail: function(err) {
        console.error('验证token请求失败:', err);
        // 请求失败也应该清除token
        uni.removeStorageSync('userInfo');
        uni.removeStorageSync('token');
        
        // 显示错误提示
        uni.showToast({
          title: '服务暂时不可用，请稍后再试',
          icon: 'none',
          duration: 2000
        });
        
        // 如果是网络错误，可能是服务器不可用，应该重定向到登录页
        setTimeout(() => {
          // 检查当前页面是否是登录页
          const pages = getCurrentPages();
          if (pages.length > 0) {
            const currentPage = pages[pages.length - 1];
            const path = `/${currentPage.route}`;
            
            // 如果不是登录页，则重定向到登录页
            if (!path.includes('/pages/user/login/')) {
              // 保存当前路径，登录后可以跳回
              safeSetStorage('redirectUrl', path);
              
              uni.reLaunch({
                url: '/pages/user/login/index'
              });
            }
          }
        }, 1500);
        
        // 返回验证失败
        resolve(false);
      }
    });
  });
}

/**
 * 跳转到登录页面
 */
export function redirectToLogin() {
  // 保存当前页面路径，以便登录后返回
  const pages = getCurrentPages();
  if (pages.length > 0) {
    const currentPage = pages[pages.length - 1];
    const path = `/${currentPage.route}`;
    
    // 检查是否是知识库详情页
    if (path === '/pages/knowledge-base/detail') {
      // 获取页面参数
      const options = currentPage.options || {};
      
      // 如果没有知识库ID，则重定向到知识库列表页
      if (!options.id) {
        safeSetStorage('redirectUrl', '/pages/knowledge-base/index');
      } else {
        // 有ID参数，保存完整路径
        const fullPath = `${path}?id=${options.id}`;
        safeSetStorage('redirectUrl', fullPath);
      }
    } else {
      // 其他页面，正常保存路径
      safeSetStorage('redirectUrl', path);
    }
  }
  
  // 跳转到登录页
  uni.reLaunch({
    url: '/pages/user/login/index'
  });
}

/**
 * 退出登录
 */
export function logout() {
  // 设置标志，表示正在退出登录
  uni.setStorageSync('isLoggingOut', 'true');
  
  // 清除用户数据
  uni.removeStorageSync('token');
  uni.removeStorageSync('userInfo');
  uni.removeStorageSync('token_backup');
  
  // 触发全局事件
  uni.$emit('userInfoUpdated', null);
  
  // 直接跳转到登录页
  uni.reLaunch({
    url: '/pages/user/login/index',
    complete: () => {
      // 清除退出标志，确保在页面跳转完成后再清除
      setTimeout(() => {
        uni.removeStorageSync('isLoggingOut');
      }, 500);
    }
  });
}

// 默认导出所有认证相关函数
export default {
  isAuthRequired,
  isLoggedIn,
  getCurrentUser,
  verifyToken,
  redirectToLogin,
  logout
};
