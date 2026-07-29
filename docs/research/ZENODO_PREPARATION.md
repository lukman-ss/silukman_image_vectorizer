# Zenodo Archive Preparation Checklist

This checklist verifies that the repository is ready for automated Zenodo archiving via GitHub integration.

- [x] **Release Tag**: A stable tag (`v1.19.0`) has been created.
- [x] **Repository Visibility**: The repository is public.
- [x] **License**: Standard `LICENSE` (MIT) file is present in the root directory.
- [x] **CITATION.cff**: Formatted correctly following the CFF 1.2.0 schema.
- [x] **.zenodo.json**: Present and containing required metadata (title, description, creators, license, keywords). *Note: DOI field is intentionally omitted and must not be claimed until Zenodo mints it.*
- [x] **Changelog**: `CHANGELOG.md` is up to date with version history.
- [x] **Source Archive**: GitHub will automatically generate the `.tar.gz` and `.zip` upon tag release.
- [x] **Artifact Checksums**: The benchmark pipeline generates `SHA-256` checksums for outputs, and the dataset uses `dataset_manifest.json` for input tracking.
- [x] **README Citation**: The `README.md` includes an Academic and Research Use section with citation instructions.
- [x] **Version Consistency**: Version `1.19.0` is strictly synchronized across `pyproject.toml`, `CITATION.cff`, `.zenodo.json`, and `codemeta.json`.

**Conclusion**: The repository satisfies all technical and metadata requirements for Zenodo archiving. Proceed to trigger the release on GitHub once the benchmark datasets are fully merged.
