# skills

Personal agent skills maintained by [master-g](https://github.com/master-g).

The repository follows the Agent Skills directory convention. Each skill lives under `skills/<name>/` and contains a `SKILL.md` entry point.

## Install

List the available skills:

```sh
npx skills add master-g/skills --list
```

Install one skill globally:

```sh
npx skills add master-g/skills --skill <name> -g
```

Install every skill globally:

```sh
npx skills add master-g/skills --skill '*' -g
```

## Included skills

- `bootstrap-claude`: bootstrap and maintain project instructions and memory files.
- `codebase-to-book`: turn a codebase into a bilingual technical book.
- `disco-elysium-narrative`: write multi-voice Disco Elysium-style narratives.
- `effective-html`: create self-contained technical HTML artifacts.
- `makemake`: consolidate project commands into a documented Makefile.
- `send-to-obsidian`: capture and summarize material into an Obsidian inbox.
- `show-me-html`: create self-contained HTML explanations using a shadcn/ui-inspired design language.
- `storm`: research and write citation-grounded articles using the STORM method.
- `url-to-kami`: extract a URL and typeset it with the Kami design system.
- `wtf`: re-explain the previous message in clear, unambiguous Simplified Chinese.
- `x-to-markdown`: convert X posts, threads, and articles to Markdown.

## License

Original repository content is available under the MIT License. Bundled third-party assets retain the licenses and notices stored beside those assets.
