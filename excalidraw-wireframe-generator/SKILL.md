---
name: "excalidraw-wireframe-generator"
description: "Generates editable Excalidraw wireframes and diagrams using ui-ux-pro-max skills. Supports two modes: (1) Description-to-Excalidraw: Create wireframes from text descriptions; (2) Web-to-Excalidraw: Convert existing web pages (URL/screenshot) to Excalidraw wireframes. Invoke when users need to create or convert web interface wireframes."
---

# Web-to-Excalidraw Visualization Generation Skill

## 1. Skill Overview

**Skill Name**: excalidraw-wireframe-generator  
**Core Objective**: Generate editable Excalidraw visualization files (`.excalidraw`) using ui-ux-pro-max skills, focusing on creating clear, hand-drawn style wireframes and diagrams for web interfaces with high fidelity to original designs.  
**Design Approach**: Adopts "Total-Sub" design methodology, providing overall guidelines first and then detailed specifications for each aspect.

## 2. When to Call

**Call Timing**: This skill should be called immediately when users need to create Excalidraw wireframes or diagrams for web interfaces.

**Specific Scenarios Include**:

- Users need to create wireframes for web applications or mobile apps
- Users need to visualize web interface layouts and components
- Users need to create hand-drawn style diagrams for web design
- Users need to generate editable Excalidraw files from web design requirements
- Automatic update when frontend page files (HTML/CSS) are modified
- Automatic generation when users specify requirement documents with visual interaction content

**Trigger Conditions**:

### 2.1 Technical Trigger Conditions

- **Input Availability**: When users provide clear web design requirements, descriptions, sketches, or basic layout specifications
- **Format Support**: When input is in a supported format (text descriptions, basic diagrams, layout requirements)
- **Compatibility Need**: When users require maximum compatibility with Excalidraw editors (version 2)
- **Frontend File Changes**: When HTML or CSS files are modified, triggering automatic wireframe updates

### 2.2 Business Trigger Conditions

- **Design Review**: When preparing for design reviews or stakeholder presentations
- **Development Guidance**: When needing to provide visual guidance to development teams
- **User Research**: When creating wireframes for user testing or research purposes
- **Documentation**: When updating or creating design documentation

### 2.3 Tool Integration Trigger Conditions

- **Design Handoff**: When transitioning from design tools (Figma, Sketch, etc.) to development
- **Collaboration Need**: When requiring collaborative wireframe editing with team members
- **Version Control**: When needing to maintain version history of design iterations

### 2.4 Automatic Trigger Conditions

- **File System Monitoring**: When configured to monitor frontend directories, automatically trigger when HTML or CSS files are created, modified, or deleted
- **Change Detection**: When significant changes to layout, styling, or components are detected in frontend files
- **Batch Processing**: When multiple frontend files are modified in a short period, aggregate changes and trigger a single update
- **Scheduled Updates**: When configured to run at specific intervals to ensure wireframes stay synchronized with frontend changes
- **Requirement Document Specification**: When users explicitly specify a requirement document that contains visual interaction content
- **Requirement Document Changes**: When an existing specified requirement document is modified with new or updated visual interaction content
- **Visual Interaction Detection**: When requirement documents contain descriptions of user interfaces, layout specifications, or interaction flows that require visualization

### 2.5 Input Modes (Two Core Patterns)

This skill supports **two distinct input modes**. Identify the mode based on user input and apply the corresponding workflow.

#### Mode A: Description-to-Excalidraw (描述生成模式)

**Trigger Keywords**: "帮我画"、"设计一个"、"创建线框图"、"wireframe"、"布局"

**Input**: Text description of web interface requirements
**Example**:

```
用户: 帮我画一个登录页面，包含用户名、密码输入框和登录按钮
```

**Process**:

```
1. Parse user description
2. Identify components and layout
3. Generate Excalidraw elements
4. Apply hand-drawn style
5. Verify layout and bindings
6. Export .excalidraw file
```

---

#### Mode B: Web-to-Excalidraw (网页转换模式)

**Trigger Keywords**: "把这个网页"、"转换为线框图"、"转成 excalidraw"、"还原设计"

**Input**: Web URL, screenshot, or HTML/CSS files
**Example**:

```
用户: 把 https://example.com 转成 excalidraw 线框图
用户: 根据这个截图生成线框图
```

**Process**:

```
1. Capture web page (URL/screenshot)
2. Analyze layout structure
3. Extract components and relationships
4. Generate Excalidraw with high fidelity
5. Apply hand-drawn style (without changing layout)
6. Verify bindings and spacing
7. Export .excalidraw file
```

**Special Handling for Web Conversion**:

- Preserve original layout proportions
- Maintain component relationships
- Identify interactive elements (buttons, inputs, links)
- Highlight user flow connections

---

#### Mode Detection Flow

```
User Input
    │
    ├── Contains URL/screenshot? ──→ Mode B: Web-to-Excalidraw
    │
    └── Pure text description? ────→ Mode A: Description-to-Excalidraw
                                       │
                                       └── Ambiguous? ──→ Ask user to clarify
```

---

#### Quick Reference

| Mode  | Input Type          | Use Case              | Keywords           |
| ----- | ------------------- | --------------------- | ------------------ |
| **A** | Text description    | Design from scratch   | 帮我画、设计、创建 |
| **B** | URL/screenshot/HTML | Convert existing page | 转换、还原、转成   |

## 3. Core Design Principles

### 3.1 Overall Design Philosophy

The skill follows a "Total-Sub" design approach, ensuring consistent quality across all generated wireframes while maintaining detailed accuracy for each component.

### 3.2 Unified Drawing Language

- **Style**: Strictly use hand-drawn style for all elements, maintaining Excalidraw's characteristic sketch-like appearance
- **Version**: Always declare `version: 2` in output files to ensure maximum compatibility with Excalidraw editors
- **Consistency**: Maintain uniform line thickness, color palette, and annotation style across all wireframes

### 3.3 Color Principles

- **Clarity**: Use high-contrast color combinations to ensure text and elements are easily readable
- **Softness**: Prefer soft color tones that reduce eye strain during extended viewing
- **Accessibility**: Follow WCAG color contrast guidelines (minimum 4.5:1 for text/background)
- **Consistency**: Maintain a consistent color scheme throughout the wireframe
- **Purposeful Use**: Use color intentionally to distinguish components, highlight important information, and indicate interactions
- **Pattern Fill**: Use stripes as the default pattern for fill effects, ensuring consistency across wireframes

## 4. Detailed Implementation Requirements

### 4.1 Visual Elements

- **Fonts**: Accurately represent web page fonts, including font family, size, weight, and style
- **Text Spacing**:
  - **Line Spacing**: Faithfully reproduce original web page line heights (typically 1.2-1.5 times font size)
  - **Character Spacing**: Maintain original character spacing, avoiding excessive tightness or looseness
  - **Paragraph Spacing**: Clearly distinguish paragraphs with appropriate spacing (typically 1.5-2 times line height)
  - **Text-Element Spacing**: Ensure sufficient spacing between text and surrounding elements to avoid crowding
- **Colors**:
  - Faithfully reproduce original web page colors for backgrounds, text, and components
  - Adjust overly bright or saturated colors to softer tones while preserving color identity
  - Ensure text-background contrast meets accessibility standards
  - Use soft, muted color palette for annotations and secondary elements
- **Dimensions**: Maintain precise proportions and dimensions for all elements, with external wireframes having sufficient size to avoid squeezing or distortion of internal elements

### 4.2 Layout & Structure

- **Fidelity**: Faithfully reproduce web page layouts, including spacing, alignment, and positioning of all elements
- **Style Annotation**: Clearly annotate styles such as height, width, color values, and spacing
- **Component Types**: Accurately identify and represent component types (buttons, inputs, cards, etc.)
- **Region Information**: Clearly indicate region boundaries and content summaries
- **Content Schemata**:
  - Provide content placeholders that accurately reflect the type and structure of actual content
  - Ensure content examples are fully displayed within their respective regions without overflow or truncation
  - Use representative sample content that clearly illustrates the intended use of each region
- **Modal/Overlay Handling**:
  - For popups and modals, create independent wireframes showing the full modal content
  - Clearly indicate the modal's relationship to the main layout with arrows or annotations
  - Include all relevant modal content, including headers, body content, and action buttons

### 4.3 Module & Sub-module Drawing

- **Independence**: Draw each module and sub-module as an independent unit with clear boundaries
- **Hierarchy**: Clearly represent the hierarchical relationship between modules
- **Content Isolation**: Ensure content from different modules/sub-modules is clearly separated

### 4.4 Canvas Usage

- **Infinite Canvas Utilization**: Effectively leverage Excalidraw's infinite canvas space to avoid crowding and overlapping
- **Logical Grouping**: Organize related wireframes, components, and flows in logical areas on the canvas
- **Spacing**: Maintain sufficient white space between different elements, modules, and wireframes
- **Avoid Overlap**: Never overlap different wireframes or components in the same canvas area
- **Navigation Aids**: Use arrows, labels, or grouping to help users navigate between related elements on the canvas
- **Zoom Levels**: Design wireframes to be clearly visible at standard zoom levels, with appropriate spacing for readability

### 4.5 Layer Organization

- **Naming Convention**: Use descriptive layer names following the pattern `{section}-{component-type}` (e.g., `header-navigation`, `content-cards`)
- **Grouping**: Organize related elements into logical groups for easy selection and manipulation
- **Hierarchy**: Maintain a consistent layer hierarchy with backgrounds at the bottom and interactive elements at the top
- **Visibility Control**: Use layer visibility toggles for complex wireframes to allow focused viewing of specific sections

### 4.6 Component Reuse

- **Component Library**: Leverage Excalidraw's component library for standard UI elements
- **Custom Components**: Create and save custom components for project-specific elements
- **Naming**: Use clear, descriptive names for custom components (e.g., `primary-button`, `card-with-avatar`)
- **Consistency**: Ensure reused components maintain consistent styling across the wireframe

### 4.7 Responsive Design Handling

- **Multi-device Representation**: Use a grid system to display layouts for different screen sizes (mobile, tablet, desktop) in a single wireframe
- **Breakpoint Indicators**: Clearly mark responsive breakpoints with dashed lines and labels
- **Layout Adaptations**: Show how elements reflow, resize, or reposition at different breakpoints
- **Mobile-First Approach**: Prioritize mobile layout and clearly indicate how it scales up to larger screens

### 4.8 Interaction & Flow Diagrams

- **User Flows**: Use arrows and numbers to indicate user journey paths through the interface
- **State Transitions**: Represent different component states (hover, active, disabled) with side-by-side comparisons or annotated variants
- **Navigation Maps**: Create sitemaps or navigation flowcharts to show page relationships
- **Modal States**: Clearly indicate how modals, drawers, and overlays appear and interact with the main layout

### 4.9 Animation & Transition Representation

- **Motion Arrows**: Use curved arrows with motion lines to indicate animation direction
- **Duration Indicators**: Add time labels to animations (e.g., `0.3s ease-in-out`)
- **Transition Types**: Use standardized symbols for different transition types (fade, slide, scale, rotate)
- **State Change Visualization**: Show before/after states with transition indicators between them

### 4.10 Arrow & Connection Handling

- **Connected Arrows**: Ensure all arrows are properly connected to their respective shapes, so they move with the shapes when repositioned
- **Arrow Types**: Use appropriate arrow types (straight, curved, elbow) based on context
- **Consistent Styling**: Maintain consistent arrow styling (thickness, color) across the wireframe
- **Clear Direction**: Ensure arrow heads clearly indicate direction of flow or relationship
- **Avoid Overlap**: Ensure arrows do not overlap unnecessarily with other elements
- **Arrow Binding Verification**: All arrows must be bound to valid target elements. After generating, verify that no arrows are "floating" (disconnected). Use `bind_arrow()` or `connect()` functions to properly bind arrow start and end points to element edges.

### 4.11 Layout Helpers (Programmatic Positioning)

Use programmatic helpers to reduce manual positioning and ensure consistent spacing.

**Positioning Utilities**:

- `below(y, h, gap=15)` → Calculate Y position below an element
- `right_of(x, w, gap=10)` → Calculate X position to the right of an element
- `above(y, gap=10)` → Calculate Y position above an element
- `auto_labeled_rect(x, y, label, padding=10, fs=20, min_width=0, min_height=0)` → Auto-size rectangle based on text content

**Usage Example**:

```javascript
// Position element B directly below element A
const y2 = below((y = 100), (h = 60), (gap = 15)); // y2 = 175

// Position element C to the right of element B
const x3 = right_of((x = 50), (w = 200), (gap = 10)); // x3 = 260

// Auto-sized rectangle
const rect = auto_labeled_rect(
  0,
  0,
  "Submit Button",
  (padding = 10),
  (fs = 16),
  (min_width = 120),
);
```

**Benefits**:

- Eliminates manual coordinate calculation
- Ensures consistent spacing between elements
- Prevents accidental overlap from miscalculation

### 4.12 Layout Verification (Post-Generation Check)

After generating the wireframe, verify layout integrity to catch issues before export.

**Verification Checks**:

| Check                   | Purpose                                         | Fix When                            |
| ----------------------- | ----------------------------------------------- | ----------------------------------- |
| **Overlap Detection**   | Find elements that occupy the same space        | Adjust positions or sizes           |
| **Arrow Binding**       | Detect arrows not connected to valid targets    | Re-bind arrows using `bind_arrow()` |
| **Spacing Consistency** | Find inconsistent gaps between similar elements | Standardize spacing values          |

**Verification Process**:

```
1. Run overlap detection on all elements
2. Check each arrow for valid start/end bindings
3. Verify spacing between related elements matches
4. Report issues for correction before final export
```

**Example Repair Flow**:

```
generate wireframe → verify layout → detect issues → fix positions → re-verify → export
```

**Critical**: Never skip verification. Floating arrows and overlapping elements are the most common quality issues in generated wireframes.

### 4.13 Style Presets (Optional Extension)

借鉴自 AlanYu04，扩展风格预设能力：

| Preset     | Characteristics              | Use Case        |
| ---------- | ---------------------------- | --------------- |
| **Vivid**  | Bright fills, strong strokes | Marketing pages |
| **Clean**  | Minimal fills, light strokes | Documentation   |
| **Sketch** | Hand-drawn, rough edges      | Brainstorming   |

**Implementation**: Define style presets as YAML configuration files that specify default colors, stroke widths, and fill patterns. Apply the appropriate preset based on project context.

## 5. Input Definition

### 5.1 Input Format

- **Data Type**: Web design requirements, descriptions, sketches, or basic layout specifications
- **Source**: User-provided text descriptions, basic diagrams, or layout requirements

## 6. Output Definition

### 6.1 Output Format

- **File Type**: Excalidraw visualization file (`.excalidraw`)
- **Version**: `version: 2` (compatible with the latest Excalidraw editor)
- **Default File Path**: Project root directory `/wireframes`
- **Format**: JSON format, conforming to Excalidraw official specifications

### 6.2 Output Content Requirements

- **Clear Visualization**: Draw pages, windows, regions, and components as clearly as possible
- **Component Representation**: Draw components/controls such as lists, carousels, etc.; use brief text for degraded presentation
- **Independent Sub-pages**: Each sub-page or window should be an independent wireframe with serial numbers, arrows, and text indicating interaction sources
- **CSS Representation**: Indicate CSS properties for components and controls where possible
- **Animation Interaction**: If required, describe animation interactions with images or text in the corresponding location

### 6.3 Output Features

- **Hand-drawn Style**: All elements use Excalidraw's default hand-drawn effect
- **Clear Organization**: Elements are logically arranged and easy to understand
- **Editability**: Supports subsequent modification in the Excalidraw editor
- **Collaboration-friendly**: Suitable for multi-person collaborative work

### 6.4 Mandatory Element Fields (Critical)

**All generated Excalidraw elements (every item in the `elements` array) MUST include the following five critical fields**. Missing any of these will cause the `Failed to load Document` error when opening the file:

| Field          | Type           | Description                                               | Example     |
| -------------- | -------------- | --------------------------------------------------------- | ----------- |
| `version`      | number         | Element version number (start at 1, increment on changes) | `1`         |
| `versionNonce` | number         | Random integer for version tracking                       | `123456789` |
| `isDeleted`    | boolean        | Whether the element is deleted                            | `false`     |
| `seed`         | number         | Random integer for deterministic rendering                | `987654321` |
| `frameId`      | string \| null | ID of the frame this element belongs to, or null          | `null`      |

**Example of a complete element**:

```json
{
  "id": "abc123",
  "type": "rectangle",
  "x": 100,
  "y": 100,
  "width": 200,
  "height": 150,
  "backgroundColor": "#ffffff",
  "strokeColor": "#000000",
  "version": 1,
  "versionNonce": 123456789,
  "isDeleted": false,
  "seed": 987654321,
  "frameId": null
}
```

**Important Notes**:

- Do not rely on AI to generate truly random `versionNonce` and `seed` values; the numbers shown above are for illustration. For production, always apply post‑processing repair as described in section 8.6.
- The `version` field must be increased whenever the element is modified (for static generation, `1` is acceptable).

### 6.5 Post‑Processing Repair (Highly Recommended)

To guarantee field completeness and correctness, **always run the generated JSON through a repair step** before saving the `.excalidraw` file:

- **Preferred method**: Use Excalidraw’s official `restoreElements` function from `@excalidraw/excalidraw`. This automatically fills missing fields, migrates types, and ensures full compatibility.
- **Alternative method**: Use a custom script that iterates over all elements and adds default values for the five mandatory fields (and other required fields like `roundness`, `boundElements`, `index` if missing).

Example repair logic (pseudo‑code):

```
for each element in elements:
    if element.version is missing: element.version = 1
    if element.versionNonce is missing: element.versionNonce = randomInt(100000, 999999999)
    if element.isDeleted is missing: element.isDeleted = false
    if element.seed is missing: element.seed = randomInt(1000000, 999999999)
    if element.frameId is missing: element.frameId = null
```

## 7. Processing Rules

### 7.1 Core Execution Logic

1. **Understand User Requirements**: Analyze user input to determine the type of visualization needed
2. **Leverage UI/UX Skills**: Use ui-ux-pro-max skills if available; if not, automatically select alternative design approach
3. **Design Layout**: Plan the overall layout and structure of the wireframes
4. **Create Elements**: Draw Excalidraw elements including pages, windows, components, and controls
5. **Apply Style**: Ensure consistent hand-drawn style across all elements
6. **Add Annotations**: Include serial numbers, arrows, and text to indicate interactions
7. **Apply Mandatory Fields**: Ensure every element includes the five required fields (version, versionNonce, isDeleted, seed, frameId)
8. **Post‑Process Repair**: Run the generated data through `restoreElements` or a custom repair script
9. **Export**: Generate the final `.excalidraw` file in the `/wireframes` directory
10. **User Confirmation**: Inform user of completion and request feedback for adjustments or additional animation interactions

## 8. Execution Steps

### 8.1 Manual Trigger Flow

1. **Requirement Analysis**: Understand the user's web design visualization needs
2. **UI/UX Design**: Apply ui-ux-pro-max skills if available; if not, automatically select alternative design approach to create effective interface designs
3. **Layout Planning**: Design the overall structure and organization of wireframes
4. **Element Creation**: Generate Excalidraw elements (pages, windows, components, controls, etc.)
5. **Component Reuse**: Implement component reuse strategy and ensure consistent styling
6. **Annotation**: Add serial numbers, arrows, and text to indicate interactions and relationships
7. **CSS Representation**: Indicate CSS properties for components and controls
8. **Animation Description**: Add animation interaction descriptions if requested
9. **Mandatory Fields & Repair**: Inject the five required fields and run post‑processing repair (see section 6.5)
10. **Quality Check**: Verify wireframe against requirements, checking for:

- Accuracy of layout and proportions
- Clear annotation and labeling
- Proper layer organization
- Consistent styling across components
- Accessibility considerations
- All elements contain version, versionNonce, isDeleted, seed, frameId

11. **Export**: Generate the final `.excalidraw` file in the `/wireframes` directory
12. **User Notification**: Inform user of completion and request feedback

### 8.2 Automatic Trigger Flow (Frontend File Changes)

1. **Change Detection**: Identify modified HTML/CSS files and analyze changes
2. **Difference Analysis**: Compare current wireframe with updated frontend files to identify discrepancies
3. **Update Planning**: Determine which wireframe elements need modification based on detected changes
4. **Targeted Updates**: Make specific changes to wireframe elements affected by frontend modifications
5. **Component Reconciliation**: Ensure reused components are updated consistently
6. **Annotation Sync**: Update any affected annotations and style indicators
7. **CSS Representation Update**: Refresh CSS property indicators to match updated frontend styles
8. **Mandatory Field Maintenance**: Verify that updated elements still have the five required fields; regenerate missing ones if needed
9. **Quality Re-check**: Verify updated wireframe against modified frontend files, checking for:
   - Updated layout accuracy
   - Consistent styling with modified CSS
   - Properly updated annotations
   - Accessibility compliance
   - Field completeness
10. **Versioned Export**: Generate updated `.excalidraw` file with incremented version number
11. **Notification**: Inform relevant stakeholders of wireframe updates based on frontend changes

### 8.3 Automatic Trigger Flow (Requirement Document)

1. **Document Analysis**: Parse specified requirement document to identify visual interaction content
2. **Requirement Extraction**: Extract UI layout specifications, component requirements, and interaction flows
3. **Layout Design**: Create wireframe layout based on extracted requirements
4. **Element Generation**: Generate Excalidraw elements according to requirement specifications
5. **Component Implementation**: Create or reuse components as defined in requirements
6. **Annotation Creation**: Add annotations and style indicators based on requirement details
7. **CSS Property Mapping**: Indicate CSS properties as specified in requirements
8. **Interaction Flow Drawing**: Create user flow diagrams and state transitions as described
9. **Mandatory Fields & Repair**: Ensure all elements contain the five required fields and run repair scripts
10. **Quality Validation**: Verify wireframe against requirement document, checking for:

- Complete coverage of all visual interaction requirements
- Accurate representation of specified layouts and components
- Clear indication of interaction flows
- Accessibility compliance
- Field completeness

11. **Export & Notification**: Generate `.excalidraw` file and notify users of completed wireframe generation

## 9. Iteration & Update Strategy

### 9.1 Feedback Integration

- **Feedback Collection**: Gather structured feedback from users regarding wireframe accuracy and clarity
- **Change Prioritization**: Prioritize requested changes based on impact and alignment with requirements
- **Version Control**: Maintain version history by saving updated wireframes with incremented version numbers

### 9.2 Update Process

1. **Identify Changes**: Clearly document all requested modifications
2. **Implement Updates**: Make targeted changes to the wireframe, preserving existing structure where possible
3. **Mandatory Field Check**: After any update, re‑validate that all elements still have the five required fields; run repair script again if needed
4. **Quality Re-check**: Verify updated wireframe against original requirements and new feedback
5. **Version Documentation**: Document changes in a version log within the wireframe or accompanying documentation
6. **Final Review**: Conduct a final review to ensure all changes are properly implemented

## 10. Best Practices

### 10.1 Balancing Detail & Efficiency

- **Focus on Core Elements**: Prioritize drawing key interface elements over minor decorative details
- **Use Abbreviations**: Employ standardized abbreviations for common elements to speed up drawing
- **Leverage Templates**: Use pre-built templates for common page layouts
- **Batch Similar Elements**: Draw similar components in batches to maintain consistency and efficiency

### 10.2 Effective Annotation

- **Clear Labeling**: Use concise, descriptive labels for all components
- **Color Coding**: Use a consistent color scheme for annotations (e.g., blue for measurements, red for interactions)
- **Hierarchical Annotation**: Prioritize annotations based on importance, using different line weights or styles
- **Group Annotations**: Keep annotations near their associated elements for easy reference

### 10.3 Standardized Component Drawing

- **Button Styles**: Use consistent shapes and sizes for different button types (primary, secondary, tertiary)
- **Form Elements**: Maintain uniform spacing and alignment for form fields and labels
- **Navigation Menus**: Use consistent indentation and styling for nested navigation items
- **Card Components**: Follow a standard structure for cards (header, content, footer)
- **Icon Usage**: Use consistent icon styles and sizes across all components

## 11. Notes

- **Clarity**: Focus on creating clear, easy-to-understand wireframes
- **Hand-drawn Style**: Maintain Excalidraw's characteristic hand-drawn appearance
- **Editability**: Ensure all elements can be modified in the Excalidraw editor
- **User Focus**: Prioritize the user's specific requirements and preferences
- **CSS Representation**: Include relevant CSS properties for components where possible
- **Animation**: Describe animation interactions with images or text if requested
- **Field Completeness**: Never omit `version`, `versionNonce`, `isDeleted`, `seed`, `frameId` from any element – this is the most common cause of load errors.

## 12. Acceptance Criteria

- **Visual Quality**: Clear, well-organized wireframes with consistent hand-drawn style
- **Component Representation**: Components and controls are clearly drawn or described
- **Interaction Indication**: Interactions are clearly indicated with serial numbers, arrows, and text
- **CSS Representation**: CSS properties are indicated for components and controls where possible
- **Animation Description**: Animation interactions are described if requested
- **Editability**: Elements can be modified in the Excalidraw editor
- **Meeting Requirements**: The output matches the user's specified requirements
- **Compatibility**: File can be opened and edited in the latest Excalidraw editor
- **Layout Fidelity**: Accurate reproduction of original web page layout and proportions
- **Module Independence**: Clear separation and independent drawing of modules and sub-modules
- **Layer Organization**: Properly organized layers with descriptive naming
- **Component Reuse**: Effective use of component library and custom components
- **Responsive Design**: Clear representation of responsive layouts for different screen sizes
- **Color Accessibility**: Text-background contrast meets WCAG guidelines (minimum 4.5:1)
- **Soft Color Palette**: Use of clear, soft color tones that reduce eye strain and avoid reading difficulties
- **Consistent Coloring**: Maintained consistent color scheme throughout the wireframe
- **Text Spacing Accuracy**: Faithful reproduction of original web page line spacing, character spacing, and paragraph spacing
- **Adequate Text-Element Spacing**: Sufficient spacing between text and surrounding elements, avoiding crowding and ensuring readability
- **Overall Readability**: Text, background, and text-background color combinations are clear, soft, and easy to read
- **Content Display**: All content examples are fully displayed within their respective regions without overflow or truncation
- **Modal/Overlay Completeness**:
  - Popups and modals are independently drawn with full content display
  - Modal relationships to main layout are clearly indicated
  - All modal content (headers, body, action buttons) is included and fully visible
- **Canvas Utilization**:
  - Effective use of Excalidraw's infinite canvas space
  - No overlapping of different wireframes or components
  - Logical grouping of related elements
  - Sufficient white space between elements
  - Clear navigation between related elements on the canvas
- **Arrow & Connection Handling**:
  - Arrows are properly connected to their respective shapes
  - Arrows move with shapes when repositioned
  - Consistent arrow styling across the wireframe
  - Clear arrow direction indication
  - No unnecessary arrow overlap
  - **All arrows are bound to valid target elements** (no floating arrows)
- **Layout Verification**:
  - No overlapping elements detected
  - Spacing between related elements is consistent
  - Arrow bindings are verified after generation
  - Repair flow is applied before export
- **Pattern Fill Usage**:
  - Use stripes as the default pattern for fill effects
  - Maintain consistent stripe pattern across all wireframes
  - Ensure pattern fill enhances readability without causing visual clutter
- **Mandatory Field Presence**: Every element MUST contain `version`, `versionNonce`, `isDeleted`, `seed`, `frameId` with appropriate values – this is non-negotiable.

## 13. User Notification

Upon task completion, the system will:

1. Inform the user about the generated Excalidraw file in the `/wireframes` directory
2. Request user confirmation on whether adjustments are needed
3. Ask if additional animation interaction descriptions should be added
4. If animation interactions are requested, describe them with images or text in the corresponding locations
