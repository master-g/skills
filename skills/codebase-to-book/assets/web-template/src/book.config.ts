export type Lang = 'en' | 'zh';

export interface PartConfig {
  number: number;
  title: string;
  titleZh: string;
  epigraph: string;
  epigraphZh: string;
  chapters: number[];
}

export interface ChapterConfig {
  number: number;
  slug: string;
  title: string;
  titleZh: string;
  description: string;
  descriptionZh: string;
}

/**
 * Source of truth for book structure.
 *
 * Populate `parts` and `chapters` after Phase 3 (Structure) of the analysis.
 * Slugs must match the markdown filenames in `book/` and `book-zh/`
 * (slug `ch01-foo` ↔ `ch01-foo.md`).
 *
 * Example shape:
 *   parts:    [{ number: 1, title: 'Foundations', titleZh: '基础',
 *               epigraph: '...', epigraphZh: '...', chapters: [1, 2] }]
 *   chapters: [{ number: 1, slug: 'ch01-intro', title: 'Intro', titleZh: '导论',
 *               description: '...', descriptionZh: '...' }]
 */
export const parts: PartConfig[] = [];

export const chapters: ChapterConfig[] = [];

export function getPartForChapter(chapterNumber: number): PartConfig | undefined {
  return parts.find(p => p.chapters.includes(chapterNumber));
}

export function getChapterNumber(slug: string): number {
  const match = slug.match(/^ch(\d+)/);
  return match ? parseInt(match[1], 10) : 0;
}

export function getAdjacentChapters(chapterNumber: number) {
  const idx = chapters.findIndex(c => c.number === chapterNumber);
  return {
    prev: idx > 0 ? chapters[idx - 1] : null,
    next: idx < chapters.length - 1 ? chapters[idx + 1] : null,
  };
}

export function isFirstChapterOfPart(chapterNumber: number): boolean {
  return parts.some(p => p.chapters[0] === chapterNumber);
}

export function getPartTitle(part: PartConfig, lang: Lang) {
  return lang === 'zh' ? part.titleZh : part.title;
}

export function getPartEpigraph(part: PartConfig, lang: Lang) {
  return lang === 'zh' ? part.epigraphZh : part.epigraph;
}

export function getChapterTitle(ch: ChapterConfig, lang: Lang) {
  return lang === 'zh' ? ch.titleZh : ch.title;
}

export function getChapterDescription(ch: ChapterConfig, lang: Lang) {
  return lang === 'zh' ? ch.descriptionZh : ch.description;
}
