# Substack Image Extraction

Substack articles embed images via `substackcdn.com/image/fetch/` URLs with complex transformation parameters. These URLs contain `$` and `!` characters that break standard shell interpolation.

## Extraction recipe

```bash
# Method 1: Python regex (most reliable)
curl -sL "https://generativeprogrammer.com/p/some-article" | python3 -c "
import sys, re
html = sys.stdin.read()
imgs = re.findall(r'https://substackcdn\.com/image/fetch/[^\"\'>\)\s]+', html)
# Filter out small icons
for img in set(imgs):
    if 'favicon' in img or 'apple-touch' in img or 'twitter' in img:
        continue
    if 'w_40' in img or 'w_80' in img or 'w_120' in img:
        continue
    print(img)
"
```

## URL patterns

Substack serves responsive images at multiple widths. Pick the largest `w_NNNN` variant for print quality, or the unqualified URL for the original:

```
# Original (no width limit)
https://substackcdn.com/image/fetch/$s_!Ljr2!,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F...

# Width-limited variants (pick w_1456 for A4 print)
https://substackcdn.com/image/fetch/$s_!Ljr2!,w_1456,c_limit,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2F...
```

## Shell escaping

The `$s_!Ljr2!` pattern requires single-quoted curl commands or escaping each `$` as `\$`:

```bash
# WRONG: double quotes expand $s as a variable
curl -sL "...$s_!Ljr2!..."   # fails

# RIGHT: single quotes
curl -sL '...$s_!Ljr2!...'

# RIGHT: escaped dollars
curl -sL "...\$s_\!Ljr2\!..."
```

## Embedding in Kami HTML

When embedding Substack images into a Kami HTML template for Chrome Headless PDF rendering, use `file://` URLs pointing to locally downloaded files:

```html
<figure>
  <img src="file:///tmp/article_image.png" alt="Description">
  <figcaption>Caption text</figcaption>
</figure>
```

Note: `file://` URLs work with Chrome Headless but may fail with WeasyPrint depending on its security policy. For cross-renderer compatibility, use `http://localhost` with a temporary Python server, or inline as base64 data URIs.
