# v0.8.2 baseline import

The **entire immutable workspace** is preserved as the exact 75-file archive `reels-script-lab-universal-workspace-v0.8.2.zip` (SHA256 `893596a6888b78b1b6690654b8ece274e4b828e492171179240a9b357ca1d8d0`). The plugin-only ZIP hash is recorded in `baseline/v0.8.2.json`.

**Current status:** the GitHub migration branch is being prepared. Full source import is not complete until `verify_baseline.py --strict` returns PASS. The original workspace README is preserved **verbatim** at `docs/history/v0.8.2-workspace-README.md`, so the repository landing README does not overwrite it.

## Recommended one-upload approach (no local terminal)

1. Download the verified workspace ZIP from the ChatGPT conversation.
2. In GitHub, switch to the `import/v0.8.2-baseline` branch.
3. Open the **baseline/** folder and click **Add file → Upload files**.
4. Upload the ZIP **with exact filename** `v0.8.2-source.zip` (rename the downloaded `reels-script-lab-universal-workspace-v0.8.2.zip` before upload).
5. Commit upload to the import branch. The GitHub Action `Import verified baseline` checks the ZIP SHA256, restores all 75 original files, verifies protected originals and runs the regression suite, then commits imported source files.
6. Inspect the draft PR and compare the files before approving the merge.

If GitHub Actions cannot push (repo settings), the alternative is a local import:

```bash
git clone https://github.com/Vladpryanik11/reels-script-lab.git
cd reels-script-lab
git fetch origin
git switch import/v0.8.2-baseline
python scripts/import_baseline.py /path/to/reels-script-lab-universal-workspace-v0.8.2.zip
python scripts/verify_baseline.py --strict
python -m unittest discover -s tests -p 'test_*.py' -q
git add . && git commit -m "import: preserved v0.8.2 sources" && git push
```

**Never** declare successful import based on a script existing or archived 89/89 tests. Inspect actual GitHub files and workflow results.
