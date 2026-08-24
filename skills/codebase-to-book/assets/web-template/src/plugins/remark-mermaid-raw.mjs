/**
 * Remark plugin: replaces ```mermaid code blocks with anchor placeholders.
 * A client-side script teleports interactive React components into these slots.
 * Each slot gets a sequential data-diagram-index attribute.
 * The original mermaid source is preserved inside a <pre class="mermaid"> tag
 * so that static diagrams can be rendered by Mermaid.js when no interactive
 * component is mapped to the slot.
 */
function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

export default function remarkMermaidRaw() {
  return (tree) => {
    let diagramCounter = 0;

    function walkTree(node) {
      if (!node.children) return;

      for (let i = 0; i < node.children.length; i++) {
        const child = node.children[i];
        if (child.type === 'code' && child.lang === 'mermaid') {
          const index = diagramCounter++;
          const source = child.value || '';
          node.children[i] = {
            type: 'html',
            value: `<div class="diagram-slot" data-diagram-index="${index}"><pre class="mermaid">${escapeHtml(source)}</pre></div>`,
          };
        } else {
          walkTree(child);
        }
      }
    }

    walkTree(tree);
  };
}
