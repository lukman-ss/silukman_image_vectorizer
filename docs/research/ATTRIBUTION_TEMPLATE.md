# Dataset Attribution Template

When adding a new real-world image to the evaluation dataset, you MUST include a proper attribution string in the dataset manifest. This ensures full compliance with open-source and open-data licenses (e.g., CC BY).

## Standard Template

Use the following format to populate the `attribution` field in the manifest:

```text
"{Title/Description}" by {Creator/Author}, licensed under {License}. Source: {Source URL}
```

### Examples

**Example 1: Wikimedia Commons (CC BY-SA)**
> "Python logo" by Python Software Foundation, licensed under CC BY-SA 4.0. Source: https://commons.wikimedia.org/wiki/File:Python-logo-notext.svg

**Example 2: Unsplash (Custom Free License)**
> "Abstract geometric architecture" by John Doe, licensed under Unsplash License. Source: https://unsplash.com/photos/xyz123

**Example 3: Self-Created (CC0)**
> "Sample testing vector" by Silukman Research Team, licensed under CC0. Source: Included in repository.

## Important Notes
- Always provide the full name of the license (e.g., "CC BY 4.0", not just "CC").
- If the author is unknown, use "Unknown Author" but only if the license explicitly permits this (e.g., Public Domain).
- Keep the attribution string in a single line without line breaks for JSON/CSV compatibility.
