export type Lang = 'en' | 'zh';

export function getStoredLang(): Lang | null {
  if (typeof localStorage === 'undefined') return null;
  const stored = localStorage.getItem('lang');
  if (stored === 'zh') return 'zh';
  if (stored === 'en') return 'en';
  return null;
}

export function setStoredLang(lang: Lang) {
  if (typeof localStorage === 'undefined') return;
  localStorage.setItem('lang', lang);
}

export function getTargetPath(currentPath: string, targetLang: Lang, baseUrl = '/'): string {
  const base = baseUrl.endsWith('/') ? baseUrl.slice(0, -1) : baseUrl;
  const afterBase = currentPath.startsWith(base) ? currentPath.slice(base.length) : currentPath;

  if (targetLang === 'zh') {
    if (afterBase.startsWith('/zh/') || afterBase === '/zh') return currentPath;
    return base + '/zh' + (afterBase || '/');
  }
  // targetLang === 'en'
  const stripped = afterBase.replace(/^\/zh(\/|$)/, '/') || '/';
  return (base + stripped) || '/';
}

export function toggleLang(current: Lang) {
  const target = current === 'zh' ? 'en' : 'zh';
  setStoredLang(target);
  window.location.href = getTargetPath(window.location.pathname, target, import.meta.env.BASE_URL);
}
