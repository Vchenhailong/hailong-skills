[:cn: 中文](./README.md) | [:us: English](./README.en.md)

- Demo: Math Teaching Content Video

<img width="480" height="270" alt="image" src="https://github.com/user-attachments/assets/19336ef0-f97c-47f8-98dc-f367d0f7e236" />

- Demo: Two-Column Layout Design (with free-body diagram examples)

<img width="480" height="270" alt="Two-column layout demo" src="https://github.com/user-attachments/assets/aa09fc78-1579-4b11-8a49-a7eff932e895" />

- Demo: Three-Column Layout Design (Note: AI struggles to draw physically correct circuit diagrams)

<img width="480" height="270" alt="三栏排版布局设计示意-AI很难绘制出正确的物理电路图"  src="https://github.com/user-attachments/assets/0911e55d-289e-4078-8d16-6539bc9ea67d" />

# ManimAnimationGenerator Skill Pack

> Manim scaffolding specialized for math/physics knowledge animation generation, built around three core principles: the **Seven-Stage Teaching Path**, the **Absolute Red Line of Layout**, and **Semantic Relevance as the Sole Standard**.
> Includes **pre-placement validation + post-placement verification** dual-layer layout protection and **force-point selection guidelines**.

## Skill Positioning

This skill receives a user's course knowledge objective from any AI model, automatically analyzes the content structure, and generates human-readable teaching content Markdown alongside a corresponding course structure JSON. An AI-driven `manim` rendering engine then outputs knowledge-point animation videos.

Three core objectives:
A. Eliminate most manim programming work
B. Address manim's key weakness — automatically handle layout, content scaling, content animation, subtitle processing, and duration control
C. Rapidly and stably generate manim videos through content-driven AI, helping users focus purely on content (though human-AI collaborative debugging of graphics is unavoidable)

Decision impact: The skill itself has been validated and tested, but LLM capabilities may reduce robustness and cause alignment drift. First-tier models are recommended.

**Core deliverables:**

- **Teaching Draft Markdown** (`主题_course.md`) — Human-readable only, includes teaching stages, intuitive explanations, counter-intuitive clarifications; each atomic unit annotated with manually authored duration (minutes), no technical fields
- **Course Structure JSON** (`courses/主题_content.json`) — Machine-readable, includes type/duration/animation actions and other program fields
- **Manim Scene Code** (`.py`) — Animation logic for rendering
- **MP4 Video** (final output)

**Workflow:** User inputs task objective → AI fully automated generation of Markdown teaching draft + JSON → User reviews and confirms each item → Fully automated code generation → Rendered output

## Directory Structure

### Root Directory

- SKILL.md — Main skill document (the sole entry point read by AI)
- README.md — This file (package structure overview)
- README.en.md — English version of this file

### references/ — Reference specifications (15 specialized documents)

| File                      | Content                                                                  |
| ------------------------- | ------------------------------------------------------------------------ |
| animation.md              | Animation principles and naming conventions                              |
| builtin_knowledge.md      | Built-in knowledge base content                                          |
| json_schema.md            | Course structure JSON validation schema (includes duration calculation)  |
| layout.md                 | Zone layout specifications (content/graphics/subtitle)                   |
| subtitle_scroller.md      | Subtitle display and animation specifications                            |
| layout_concept.html       | Layout concept visual documentation                                      |
| math_latex.md             | Math LaTeX specifications (MathTex vs Tex)                               |
| pedagogy_path.md          | Teaching path design (memorization → understanding → application)        |
| physics.md                | Physics drawing primitives (includes force-point selection guidelines)   |
| netlist.md                | Circuit diagram design approach (key integration: Icapy library/netlist) |
| project_structure.md      | Project directory structure specifications                               |
| quality_acceptance.md     | Acceptance criteria and quality gates                                    |
| rendering.md              | Rendering configuration (1080p60/720p30/4k)                              |
| textbook_sources.md       | Textbook knowledge source coverage list                                  |
| tts_guide.md              | TTS pronunciation mapping (LaTeX+Unicode → Chinese)                      |
| verification_checklist.md | Verification checklist (5 gates)                                         |
| workflow.md               | User-AI collaborative workflow                                           |

### scripts/ — Executable scripts and modules

| File/Directory                        | Content                                                                                                        |
| ------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| animation/subtitle_scroller.py        | Subtitle scroll manager (pre-computed scroll system + max_duration ratio scaling)                              |
| layout/constants.py                   | ZoneConstants layout constants definition                                                                      |
| layout/engine.py                      | Layout engine entry point                                                                                      |
| layout/scene_base.py                  | LayoutScene base class (includes validate_layout / \_precheck_mobject / place_two_column / place_three_column) |
| layout/optimizer.py                   | Layout optimizer (3-round fallback chain: scale_font → wrap_content → split_atom)                              |
| layout/zones/base.py                  | ZoneBase base class                                                                                            |
| layout/zones/main_content_zone.py     | Main content zone (text + formulas)                                                                            |
| layout/zones/graphics_zone.py         | Graphics zone (geometry + physics primitives)                                                                  |
| layout/zones/subtitle_zone.py         | Subtitle zone (bottom pad, no decorative bar)                                                                  |
| validation/course_schema_validator.py | JSON structure validation (duration match ±3s tolerance)                                                       |
| physics_graphics.py                   | Physics primitive factory functions (create_force_arrow / create_car / create_inclined_plane etc.)             |
| tex_tools.py                          | LaTeX processing tools (TTS/Unicode/validation/subscripts)                                                     |
| subtitle_splitter.py                  | Subtitle splitting (max_chars line breaking)                                                                   |
| split_atom.py                         | Formula atom splitting (operand/operator parsing)                                                              |
| visual_actions.py                     | Visual action definitions (fade/slide/highlight etc.)                                                          |
| validate_layout.py                    | Layout validation entry script                                                                                 |
| validate_course_contents.py           | Course content validation script                                                                               |

### templates/ — Code templates and configuration

| File                      | Content                        |
| ------------------------- | ------------------------------ |
| course_template.json      | Course structure JSON template |
| layout_test_template.json | Layout test template           |
| manim.cfg                 | Manim global configuration     |

### examples/ — Examples

| File                          | Content                                |
| ----------------------------- | -------------------------------------- |
| matrix_course_example.json    | Course JSON example                    |
| matrix_scene.py               | Corresponding Manim scene code example |
| run_example.sh                | Run command example                    |
| run_example_specification.txt | Example specification                  |

## Core File Quick Reference

| Task                                                                    | File                                                                                                          |
| ----------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| AI reads skill specification                                            | `SKILL.md`                                                                                                    |
| Layout base class (mandatory)                                           | `scripts/layout/scene_base.py` → `LayoutScene`                                                                |
| Pre-placement validation (auto-adjust width/height)                     | `scripts/layout/scene_base.py` → `_precheck_mobject()`                                                        |
| Two-column layout (built-in pre-check + verification dual protection)   | `scripts/layout/scene_base.py` → `place_two_column()`                                                         |
| Three-column layout (all columns include pre-check)                     | `scripts/layout/scene_base.py` → `place_three_column()`                                                       |
| Layout optimizer (3-round fallback chain)                               | `scripts/layout/optimizer.py` → `LayoutOptimizer`                                                             |
| Line-breaking strategy (Text CJK line-split / MathTex breakpoint split) | `scripts/layout/optimizer.py` → `_apply_wrap()` / `_wrap_text_object()` / `_wrap_math_object()`               |
| Layout validation (9 violation types + semantic exemption)              | `scripts/layout/scene_base.py` → `validate_layout()` (includes 13 pattern-based semantic relevance inference) |
| Overlap whitelist (13 patterns, semantic relevance inference)           | `scripts/layout/scene_base.py` → `ALLOWED_PATTERNS` (zero-config auto exemption)                              |
| Physics primitive factory                                               | `scripts/physics_graphics.py` → `create_force_arrow()` / `create_car()` / etc.                                |
| Force-point guidelines                                                  | `references/physics.md` → §15.1.1 (G/N/f/F/T action point quick reference + error reference)                  |
| Subtitle scrolling (pre-computed + ratio scaling)                       | `scripts/animation/subtitle_scroller.py`                                                                      |
| Layout constants (zone boundaries)                                      | `scripts/layout/constants.py` → `ZoneConstants`                                                               |
| LaTeX → Unicode conversion                                              | `scripts/tex_tools.py` → `latex_to_unicode()`                                                                 |
| TTS pronunciation mapping                                               | `scripts/tex_tools.py` → `math_symbols_to_speech()`                                                           |

## Core Principles (see SKILL.md for details)

1. **Seven-Stage Teaching Path** — Each knowledge atom is designed with a seven-stage narrative flow: activate prior knowledge → intuitive experience → definition → operation → counter-intuitive clarification → application → summary, ensuring teaching completeness
2. **Absolute Red Line of Layout** — All layouts must use LayoutScene base class + VGroup.arrange(); hardcoded coordinates are forbidden (M1–M6 mandatory / F1–F7 prohibited)
3. **Dual-Layer Layout Protection** — **Pre-placement validation** (`_precheck_mobject`: pre-measure width/height per object before placement, auto line-wrap/scale/scale_to_fit) + **Post-placement verification** (`validate_layout` + 3-round fallback chain)
4. **Semantic Relevance as Sole Standard** — Overlap judgment: semantically related → allowed; semantically unrelated → forbidden (13 predefined patterns, zero-config inference)
5. **Programmatic Layout Validation** — `validate_layout()` detects 9 violation types in milliseconds (overflow/encroachment/overlap/out-of-bounds/stacking/column-width/spacing/fill-rate/center-of-gravity shift), zero rendering dependency
6. **Free-Body Diagram Drawing Guidelines** — Based on correct mechanical analysis results and standardized engineering drawings, all force vector action points must accurately land on the actual force application points of the受力 object (see physics.md §15.1.1)
7. **5 Acceptance Gates** — JSON validation(G1) → Layout preview(G2) → validate_layout programmatic layout(G3) → Math/physical correctness(G4) → Render verification + manual review(G5)

## Dependencies

- Python ≥ 3.10
- Manim (Community Edition)
- Fonts: Source Han Sans / Noto Sans CJK (subtitle Chinese)
