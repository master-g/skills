export type Lang = 'en' | 'zh';

export const ui = {
  en: {
    siteTitle: '__PROJECT_NAME__ from Source',
    siteTagline: 'A reverse-engineered architecture book.',
    heroDescription: 'Architecture, patterns, and internals — distilled from the source.',
    startReading: 'Start reading',
    tableOfContents: 'Table of contents',
    previous: 'Previous',
    next: 'Next',
    onThisPage: 'On this page',
    focusModeLabel: 'Focus mode — hide sidebars',
    toggleNav: 'Toggle navigation',
    copy: 'Copy',
    copied: 'Copied!',
    copyFailed: 'Failed',
    darkModeToggle: 'Toggle dark mode',
    langToggle: 'Switch language',
    part: 'Part',
    githubUrl: '',
    disclaimer: 'Independent educational analysis. Code blocks are pseudocode that illustrates patterns — no verbatim source.',
  },
  zh: {
    siteTitle: '__PROJECT_NAME__ 源码解析',
    siteTagline: '一本逆向工程的架构书。',
    heroDescription: '从源码中提炼出的架构、模式与内部原理。',
    startReading: '开始阅读',
    tableOfContents: '目录',
    previous: '上一章',
    next: '下一章',
    onThisPage: '本页目录',
    focusModeLabel: '专注模式 — 隐藏侧边栏',
    toggleNav: '切换导航',
    copy: '复制',
    copied: '已复制！',
    copyFailed: '失败',
    darkModeToggle: '切换深色模式',
    langToggle: '切换语言',
    part: '第',
    githubUrl: '',
    disclaimer: '独立教育性分析。代码块均为说明模式的伪代码，不含原始源码。',
  },
} as const;

export function t(lang: Lang, key: keyof typeof ui.en): string {
  return ui[lang][key] ?? ui.en[key];
}
