import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import Router from './router.js'

describe('Router', () => {
  let mockUni

  beforeEach(() => {
    // Mock uni 对象
    mockUni = {
      navigateBack: vi.fn(),
      switchTab: vi.fn(),
      reLaunch: vi.fn(),
      navigateTo: vi.fn(),
    }
    global.uni = mockUni
    global.getCurrentPages = vi.fn()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('navigateBack', () => {
    it('当页面栈有多页时，应该调用 uni.navigateBack', () => {
      // 模拟页面栈有两页
      global.getCurrentPages.mockReturnValue([
        { route: 'pages/tools/index' },
        { route: 'pages/tools/watermark/index' },
      ])

      // 模拟 navigateBack 成功
      mockUni.navigateBack.mockImplementation(({ success }) => {
        success && success()
      })

      Router.navigateBack()

      expect(mockUni.navigateBack).toHaveBeenCalledWith({
        delta: 1,
        success: expect.any(Function),
        fail: expect.any(Function),
      })
    })

    it('当页面栈只有一页时，应该直接执行 fallback', () => {
      // 模拟页面栈只有一页（刷新后的情况）
      global.getCurrentPages.mockReturnValue([
        { route: 'pages/tools/watermark/index' },
      ])

      // 模拟 switchTab 成功
      mockUni.switchTab.mockImplementation(({ success }) => {
        success && success()
      })

      Router.navigateBack()

      // 不应该调用 navigateBack
      expect(mockUni.navigateBack).not.toHaveBeenCalled()
      // 应该调用 switchTab 跳转到 tools 首页
      expect(mockUni.switchTab).toHaveBeenCalledWith({
        url: '/pages/tools/index',
        success: expect.any(Function),
        fail: expect.any(Function),
      })
    })

    it('当页面栈为空时，应该直接执行 fallback', () => {
      // 模拟页面栈为空
      global.getCurrentPages.mockReturnValue([])

      mockUni.switchTab.mockImplementation(({ success }) => {
        success && success()
      })

      Router.navigateBack()

      expect(mockUni.navigateBack).not.toHaveBeenCalled()
      expect(mockUni.switchTab).toHaveBeenCalled()
    })

    it('当 navigateBack 失败时，应该执行 fallback', () => {
      global.getCurrentPages.mockReturnValue([
        { route: 'pages/tools/index' },
        { route: 'pages/tools/watermark/index' },
      ])

      // 模拟 navigateBack 失败
      mockUni.navigateBack.mockImplementation(({ fail }) => {
        fail && fail(new Error('navigateBack failed'))
      })

      mockUni.switchTab.mockImplementation(({ success }) => {
        success && success()
      })

      Router.navigateBack()

      expect(mockUni.switchTab).toHaveBeenCalledWith({
        url: '/pages/tools/index',
        success: expect.any(Function),
        fail: expect.any(Function),
      })
    })

    it('应该支持自定义 fallbackUrl', () => {
      global.getCurrentPages.mockReturnValue([
        { route: 'pages/tools/watermark/index' },
      ])

      mockUni.switchTab.mockImplementation(({ success }) => {
        success && success()
      })

      const customFallback = '/pages/custom/page'
      Router.navigateBack(1, { fallbackUrl: customFallback })

      expect(mockUni.switchTab).toHaveBeenCalledWith({
        url: customFallback,
        success: expect.any(Function),
        fail: expect.any(Function),
      })
    })

    it('当 useSmartFallback 为 false 时，不应该自动判断 fallback', () => {
      global.getCurrentPages.mockReturnValue([
        { route: 'pages/tools/watermark/index' },
      ])

      Router.navigateBack(1, { useSmartFallback: false })

      // 不应该调用 switchTab，因为没有指定 fallbackUrl
      expect(mockUni.switchTab).not.toHaveBeenCalled()
    })

    it('当 switchTab 失败时，应该尝试 reLaunch', () => {
      global.getCurrentPages.mockReturnValue([
        { route: 'pages/tools/watermark/index' },
      ])

      // 模拟 switchTab 失败
      mockUni.switchTab.mockImplementation(({ fail }) => {
        fail && fail(new Error('switchTab failed'))
      })

      mockUni.reLaunch.mockImplementation(({ success }) => {
        success && success()
      })

      Router.navigateBack()

      expect(mockUni.reLaunch).toHaveBeenCalledWith({
        url: '/pages/tools/index',
        success: expect.any(Function),
        fail: expect.any(Function),
      })
    })
  })

  describe('_getFallbackUrlByCurrentPage', () => {
    it('tools 页面应该返回到 tools/index', () => {
      global.getCurrentPages.mockReturnValue([
        { route: 'pages/tools/watermark/index' },
      ])

      const result = Router._getFallbackUrlByCurrentPage()

      expect(result).toBe('/pages/tools/index')
    })

    it('extraction 页面应该返回到 tools/index', () => {
      global.getCurrentPages.mockReturnValue([
        { route: 'pages/tools/extraction/index' },
      ])

      const result = Router._getFallbackUrlByCurrentPage()

      expect(result).toBe('/pages/tools/index')
    })

    it('smart-template 页面应该返回到 tools/index', () => {
      global.getCurrentPages.mockReturnValue([
        { route: 'pages/tools/smart-template/index' },
      ])

      const result = Router._getFallbackUrlByCurrentPage()

      expect(result).toBe('/pages/tools/index')
    })

    it('template-manage 页面应该返回到 tools/index', () => {
      global.getCurrentPages.mockReturnValue([
        { route: 'pages/tools/template-manage/index' },
      ])

      const result = Router._getFallbackUrlByCurrentPage()

      expect(result).toBe('/pages/tools/index')
    })

    it('chat-modules 页面应该返回到 bot-list/index', () => {
      global.getCurrentPages.mockReturnValue([
        { route: 'pages/chat-modules/chat/index' },
      ])

      const result = Router._getFallbackUrlByCurrentPage()

      expect(result).toBe('/pages/bot-modules/bot-list/index')
    })

    it('knowledge-base/detail 页面应该返回到 knowledge-base/index', () => {
      global.getCurrentPages.mockReturnValue([
        { route: 'pages/knowledge-base/detail' },
      ])

      const result = Router._getFallbackUrlByCurrentPage()

      expect(result).toBe('/pages/knowledge-base/index')
    })

    it('bot-detail 页面应该返回到 bot-list/index', () => {
      global.getCurrentPages.mockReturnValue([
        { route: 'pages/bot-modules/bot-detail/index' },
      ])

      const result = Router._getFallbackUrlByCurrentPage()

      expect(result).toBe('/pages/bot-modules/bot-list/index')
    })

    it('edit-bot 页面应该返回到 bot-list/index', () => {
      global.getCurrentPages.mockReturnValue([
        { route: 'pages/bot-modules/edit-bot/index' },
      ])

      const result = Router._getFallbackUrlByCurrentPage()

      expect(result).toBe('/pages/bot-modules/bot-list/index')
    })

    it('未知页面应该返回 null', () => {
      global.getCurrentPages.mockReturnValue([
        { route: 'pages/unknown/page' },
      ])

      const result = Router._getFallbackUrlByCurrentPage()

      expect(result).toBeNull()
    })

    it('页面栈为空时应该返回 null', () => {
      global.getCurrentPages.mockReturnValue([])

      const result = Router._getFallbackUrlByCurrentPage()

      expect(result).toBeNull()
    })

    it('页面栈为 null 时应该返回 null', () => {
      global.getCurrentPages.mockReturnValue(null)

      const result = Router._getFallbackUrlByCurrentPage()

      expect(result).toBeNull()
    })
  })

  describe('其他导航方法', () => {
    it('navigateTo 应该调用 uni.navigateTo', () => {
      mockUni.navigateTo = vi.fn().mockImplementation(({ success }) => {
        success && success()
      })
      global.uni.navigateTo = mockUni.navigateTo

      Router.navigateTo('/pages/test/index', { id: 1 })

      expect(mockUni.navigateTo).toHaveBeenCalled()
    })

    it('redirectTo 应该调用 uni.redirectTo', () => {
      mockUni.redirectTo = vi.fn().mockImplementation(({ success }) => {
        success && success()
      })
      global.uni.redirectTo = mockUni.redirectTo

      Router.redirectTo('/pages/test/index')

      expect(mockUni.redirectTo).toHaveBeenCalled()
    })

    it('reLaunch 应该调用 uni.reLaunch', () => {
      mockUni.reLaunch = vi.fn().mockImplementation(({ success }) => {
        success && success()
      })
      global.uni.reLaunch = mockUni.reLaunch

      Router.reLaunch('/pages/test/index')

      expect(mockUni.reLaunch).toHaveBeenCalled()
    })

    it('switchTab 应该调用 uni.switchTab', () => {
      mockUni.switchTab = vi.fn().mockImplementation(({ success }) => {
        success && success()
      })
      global.uni.switchTab = mockUni.switchTab

      Router.switchTab('/pages/index/index')

      expect(mockUni.switchTab).toHaveBeenCalled()
    })
  })
})
