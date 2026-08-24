import type { Lang } from './ui';

export interface DiagramI18n {
  title: string;
  description: string;
}

/**
 * Optional labels for interactive diagrams attached to chapters.
 *
 * Index by chapter number, then by mermaid slot index. Used by
 * `InteractiveDiagrams.astro` when you wire React components to slots.
 */
const labels: Record<number, Record<number, { en: DiagramI18n; zh: DiagramI18n }>> = {
  // Example shape — fill in when you start wiring interactive diagrams:
  // 1: {
  //   0: {
  //     en: { title: 'Architecture overview', description: 'Drag to explore.' },
  //     zh: { title: '架构总览', description: '拖动节点进行探索。' },
  //   },
  // },
};

export function getDiagramLabels(
  chapterNumber: number,
  slotIndex: number,
  lang: Lang,
): DiagramI18n | undefined {
  return labels[chapterNumber]?.[slotIndex]?.[lang];
}
