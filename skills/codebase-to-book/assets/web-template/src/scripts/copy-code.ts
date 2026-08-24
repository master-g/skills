// Add copy buttons to all code blocks
const lang = document.documentElement.dataset.lang === 'zh' ? 'zh' : 'en';
const labels = {
  en: { copy: 'Copy', copied: 'Copied!', failed: 'Failed' },
  zh: { copy: '复制', copied: '已复制！', failed: '失败' },
}[lang];

document.querySelectorAll('pre:not(.mermaid)').forEach((pre) => {
  const wrapper = document.createElement('div');
  wrapper.className = 'code-block-wrapper';
  pre.parentNode?.insertBefore(wrapper, pre);
  wrapper.appendChild(pre);

  const btn = document.createElement('button');
  btn.className = 'copy-button';
  btn.textContent = labels.copy;
  btn.addEventListener('click', async () => {
    const code = pre.querySelector('code')?.textContent || pre.textContent || '';
    try {
      await navigator.clipboard.writeText(code);
      btn.textContent = labels.copied;
      setTimeout(() => { btn.textContent = labels.copy; }, 2000);
    } catch {
      btn.textContent = labels.failed;
      setTimeout(() => { btn.textContent = labels.copy; }, 2000);
    }
  });
  wrapper.appendChild(btn);
});
