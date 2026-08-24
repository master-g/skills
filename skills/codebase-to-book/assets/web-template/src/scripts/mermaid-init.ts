import mermaid from 'mermaid';

function getMermaidTheme(): 'default' | 'dark' {
  return document.documentElement.classList.contains('dark') ? 'dark' : 'default';
}

async function renderMermaid() {
  const theme = getMermaidTheme();
  mermaid.initialize({ startOnLoad: false, theme });

  // Reset already-rendered diagrams so they can be re-rendered with the new theme
  document.querySelectorAll('.mermaid[data-processed="true"]').forEach((el) => {
    el.removeAttribute('data-processed');
    const parent = el.parentElement;
    if (parent) {
      parent.querySelectorAll(':scope > svg').forEach((svg) => svg.remove());
    }
    (el as HTMLElement).style.display = '';
  });

  await mermaid.run({ querySelector: '.mermaid' });
}

document.addEventListener('DOMContentLoaded', renderMermaid);
window.addEventListener('theme-changed', renderMermaid);
