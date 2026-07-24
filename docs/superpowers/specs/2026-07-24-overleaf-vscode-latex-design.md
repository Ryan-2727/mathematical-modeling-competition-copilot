# Overleaf and VS Code LaTeX Compatibility Design

## Goal

Make every completed paper produced by the skill a portable LaTeX project that
compiles and previews without source edits in both:

- Overleaf with XeLaTeX selected; and
- VS Code with a TeX distribution and the LaTeX Workshop extension.

The compatibility contract applies to the delivered project, not only to a
standalone `main.tex` excerpt.

## Selected Approach

Use a bundled portable project template, a deterministic scaffolding script, and
a compatibility verifier. This is preferred over documentation-only guidance
because missing files and editor settings can be tested. A containerized TeX
environment is out of scope because it does not match Overleaf's execution model
and would add a second delivery path.

## Compatibility Baseline

- Use UTF-8 source files.
- Use XeLaTeX as the default engine.
- Use `latexmk` as the build driver.
- Use BibTeX as the default bibliography backend.
- Use `ctexart` and TeX-distributed Fandol fonts for Chinese papers.
- Use relative paths only.
- Do not require locally installed operating-system fonts.
- Permit a contest-provided class or style to replace the bundled document class,
  but preserve the same root-file, path, build, and verification contracts.
- Do not promise pdfLaTeX compatibility for Chinese papers.

## Portable Project Layout

The generated paper tree is:

```text
paper/
|-- main.tex
|-- references.bib
|-- .latexmkrc
|-- .vscode/
|   |-- settings.json
|   `-- extensions.json
|-- sections/
|   |-- abstract.tex
|   |-- problem.tex
|   |-- assumptions.tex
|   |-- model.tex
|   |-- results.tex
|   |-- evaluation.tex
|   `-- conclusion.tex
|-- figures/
`-- build/
```

`build/` is generated locally and is excluded from the portable source archive.
Overleaf compiles from `main.tex` at the paper-project root. VS Code writes local
artifacts to `build/`.

## Template Responsibilities

### `main.tex`

- Declare UTF-8 encoding, XeLaTeX, and the root file using editor directives.
- Load `ctexart` without operating-system font names.
- Keep figures, section inputs, and bibliography paths relative to `main.tex`.
- Enable SyncTeX through the build configuration.
- Use deterministic section inputs rather than generated include files.
- Use BibTeX with a portable fallback bibliography style when a Chinese GB/T 7714
  style is unavailable.
- Compile successfully with the bundled sample content.

### `.latexmkrc`

- Select XeLaTeX and fail on TeX errors.
- Use noninteractive, file-line-error output suitable for Overleaf logs and local
  diagnostics.
- Leave the output directory unset so Overleaf controls its own build location.
- Let the VS Code recipe provide its local `build/` output directory.

### `.vscode/settings.json`

- Define one named `latexmk (XeLaTeX)` recipe.
- Build on save with the root document.
- Write local output to `paper/build/`.
- Preview the PDF in a VS Code tab.
- Enable SyncTeX-compatible forward and inverse navigation.
- Clean only generated auxiliary files.

### `.vscode/extensions.json`

- Recommend `James-Yu.latex-workshop`.
- Do not require unrelated extensions.

## Scaffolding

Add `scripts/scaffold_latex_paper.py` to copy the bundled template into a target
project. The script must:

- refuse to overwrite nonempty paper sources unless `--force` is explicitly used;
- preserve UTF-8 and hidden configuration files;
- create the empty `figures/` and generated `build/` directories;
- report every created file; and
- return a nonzero status on partial or unsafe output.

Update `scripts/init_contest.py` to call the same scaffolding logic so new contest
projects receive the complete portable tree. Do not maintain a second embedded
copy of the template inside `init_contest.py`.

## Compatibility Verification

Add `scripts/verify_latex_compatibility.py`. It checks:

1. required project files and directories;
2. UTF-8 decoding;
3. XeLaTeX and root-document directives;
4. VS Code recipe, output directory, viewer, and extension recommendation;
5. absence of Windows drive paths, `file://` paths, home-directory paths, and
   explicit operating-system font dependencies;
6. existence of every statically referenced section and graphic;
7. bibliography file and backend consistency;
8. successful `latexmk` execution when the executable is available;
9. existence and nonzero size of the resulting PDF; and
10. fatal errors, undefined references, undefined citations, or missing files in
    the build log.

Static validation still runs when `latexmk` is unavailable, but the report status
must be `LIMITED`, not `PASS`. A completed paper may be claimed compatible only
after an actual compile succeeds.

Integrate the compatibility verifier into `verify_paper_delivery.py`. The delivery
gate fails when required compatibility files are missing or when the latest
compatibility report is not a compile-backed pass.

## User Workflows

### Overleaf

1. Upload the entire contents of `paper/` as one project.
2. Select `main.tex` as the main document.
3. Select XeLaTeX in project settings.
4. Recompile and use Overleaf's PDF preview.

The uploaded source includes `.latexmkrc`; `.vscode/` is inert on Overleaf.

### VS Code

1. Open the generated project folder.
2. Install a TeX distribution, `latexmk`, and the recommended LaTeX Workshop
   extension.
3. Open `paper/main.tex`.
4. Run the default `latexmk (XeLaTeX)` recipe or save the file.
5. Preview the generated PDF in the VS Code tab and use SyncTeX navigation.

## Error Handling

- Missing TeX tooling produces an explicit installation limitation rather than a
  false compatibility claim.
- Missing packages or fonts fail the compile and identify the first actionable log
  line.
- Missing references, citations, sections, and graphics fail verification.
- Existing user paper files are never overwritten silently.
- Contest-provided templates are preserved; only portable editor and build support
  is added around them.

## Tests

Add automated tests for:

- complete scaffold output, including hidden files;
- overwrite refusal and explicit force behavior;
- `init_contest.py` integration;
- rejection of absolute paths and local font names;
- rejection of missing section, graphic, bibliography, or VS Code settings;
- static validation when TeX is unavailable;
- real XeLaTeX/BibTeX compilation through `latexmk` when available;
- nonempty PDF generation; and
- delivery-gate integration.

Run the full existing test suite, the skill contract validator, the Skill Creator
validator, `git diff --check`, and one fresh template compile before completion.

## Documentation Changes

- Update `SKILL.md` so paper delivery requires the portable project tree and
  compile-backed compatibility verification.
- Expand `references/embedded/latex-paper-pipeline.md` with the exact Overleaf and
  VS Code workflows and troubleshooting order.
- Update English and Chinese repository READMEs with the same engine baseline and
  concise usage instructions.
- Keep detailed configuration in the bundled template and LaTeX pipeline reference
  rather than expanding the top-level Skill instructions.

## Acceptance Criteria

The change is accepted when:

- a fresh scaffold compiles to a nonempty PDF using `latexmk`;
- the same unmodified source tree contains valid Overleaf and VS Code build
  configuration;
- compilation does not depend on a user-specific path or operating-system font;
- every compatibility failure returns a nonzero exit code and an actionable report;
- all automated tests and validators pass; and
- the repository and installed skill copies match after synchronization.
