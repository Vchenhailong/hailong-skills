---
name: http-api-tester
description: HTTP API endpoint testing framework with call chain analysis, parameter dependency tracking, Mock support, automatic environment self-check, dependency installation, test data naming convention (AIT_/ait_), test data context acquisition, production environment protection, real-world data validation, image generation for file upload testing, and comprehensive test reports including author (hailong.chen) and AI model information. Enhanced report generation with JSON/Markdown/Web formats, scenario-based test counts, coverage rates, interactive visualization, and smart incremental updates. Invoke when user needs API interface testing, call chain analysis, or HTTP endpoint validation.
---

# HTTP API Tester

A comprehensive HTTP endpoint testing skill framework focused on **scenario-based testing** (where a call chain often contains multiple scenarios, and a scenario refers to a specific request-response business logic branch; one scenario equals one test case). It is neither unit testing nor isolated HTTP endpoint testing, but rather tests complete business workflows through API call chains. The skill automatically matches language stack mature testing frameworks to generate high-quality reports.

## When to Invoke

**MUST invoke this skill when:**

- User requests HTTP endpoint/API interface testing
- User needs to analyze API call chains and dependencies
- User wants to test RESTful APIs or HTTP services
- User requires parameter dependency tracking across API calls
- User needs Mock setup for third-party services in API testing
- User asks for API test coverage statistics and reporting
- User needs enhanced test reports with JSON/Markdown/Web formats
- User requires scenario-based test analysis and visualization
- User wants interactive test reports with search/filter capabilities

**DO NOT invoke for:**

- Unit testing of internal functions or classes
- Database direct access testing
- Frontend component testing
- Performance/load testing (use performance-expert instead)

## Quick Reference

For a detailed step-by-step guide of the testing workflow, refer to:

- **[procedure.md](procedure.md)**: Complete testing process steps
- **[reference/test-design.md](reference/test-design.md)**: Detailed test design methodology
- **[reference/report-format.md](reference/report-format.md)**: Comprehensive report format specifications
- **[reference/lang-support.md](reference/lang-support.md)**: Language stack support details
- **[reference/产物文件汇总清单.md](reference/产物文件汇总清单.md)**: Complete list of all required output files (code files, analysis documents, test reports, etc.)

## Core Testing Principles (MANDATORY)

### PRINCIPLE 1: Test Identity and Test Purpose

- Define test identity (who performs test)
- Define test purpose (what business behavior is validated)

### PRINCIPLE 2: Check Business Key Points in Response Body

- Assertions MUST validate response body field values (if applicable)
- HTTP status code assertions acceptable ONLY when response body is empty

### MANDATORY Enforcement

- All test cases MUST follow both core principles
- Test reports MUST include test identity and test purpose information
- Test reports MUST include assertion information for response body validation

## Testing Constraints (STRICT)

### REQUIRED Test Data Prefix

- **Non-real-world data validation test data** MUST use prefix "AIT*" or "ait*"
  - Examples: `AIT_test_user_001`, `AIT_order_12345`, `AIT_test_product_xyz`
  - Field types: username, name, product_name, title, description, etc.
- **Real-world data validation test data** does NOT require prefix
  - Examples: `test@example.com` (email format), `13800138000` (phone format)
- **Does NOT include application self-maintained id, uuid** (should be read from response body or obtained from database if necessary)

### Test Data Naming Convention

- ✅ Prefix test data with `AIT_` (e.g., `AIT_test_user_001`)
- ✅ Use UUID or timestamps for uniqueness
- ✅ Clean up test data after test execution
- ✅ Use Fixture mechanism to manage test data generation and cleanup
- ✅ Test data unified management, supporting Session-level sharing

### Non-Hardcoded Data Requirement

- ❌ **Prohibited**: Hardcoding non-static data in test code or reports
- ✅ **Recommended**: Use configuration files, environment variables, or data generation functions for dynamic data
- ✅ **Recommended**: Store test data in separate files
- ✅ **Recommended**: Use custom parameterization patterns for test cases with multiple data sets
- ❌ **Not Recommended**: Use test framework-provided parameterization patterns (e.g., pytest's @pytest.mark.parametrize)
- ✅ **Recommended**: Generate dynamic data at runtime for uniqueness (e.g., timestamps, UUIDs)
- ✅ **Recommended**: Read dynamic identifiers from API responses or database instead of hardcoding

## Test File Organization Requirements (MANDATORY)

**CRITICAL: Test files MUST be organized to support unified session execution**

### Mandatory Requirements

1. **Directory Structure**:
   - ✅ `testcases/`: Test case directory, organized by business modules/scenarios
   - ✅ `testcases/atomic/`: Atomic layer directory for single API endpoint tests (only called by business layer, not directly executed)
2. **Unified Execution Capability**: All test files MUST be executable in a single test session
3. **Core Business Module Principle**:
   - ✅ Test files SHOULD be organized by **core business module + business process** principle
   - ✅ Core business module is determined by: business purpose, final output, and business domain
   - ✅ When involving multiple modules, use the **core business module** as the main naming basis
4. **File Naming Rules**:
   - ✅ Atomic layer: Use business module name directly, e.g., `order.py` for single API endpoint tests (only called by business layer, not directly executed)
   - ✅ Business layer: Use `test_{core_module}.py` format, e.g., `test_order.py` for complete business flow tests
   - ✅ Must create a dedicated test file for the maximum dependency chain (longest chain with actual dependencies) identified in the system
   - ✅ Maximum dependency chain test file naming: `test_max_dependency_chain.py`
5. **Full Coverage Execution**: Single command MUST execute all tests across all files
6. **Session Completeness**: All test results MUST be collected in one session for unified report generation

## Core Capabilities

### Automatic HTTP Call Relationship Analysis

- Identify and record API call execution order
- Generate call chain relationship diagrams using Graph or Mermaid syntax
- Present static call chains with parameter passing visualization
- **Probe Code Documentation Requirements**: When generating call chain probe code, MUST include:
  1. **Core Design**: AST-based parsing approach, graph data structure, algorithm choices
  2. **Discovery Strategy**: How endpoints are discovered (route decorators, function signatures), dependency detection methods, entry point identification
  3. **Deduplication Strategy**: Path deduplication, cycle detection, filtering strategies for call chains
  4. **Limitations**: Hardcoded patterns, information that cannot be auto-inferred, design trade-offs

### Multi-Role Analysis

- Identify all business roles in the system (e.g., user, admin, customer service)
- Create role-endpoint mapping tables for each role
- Analyze cross-role business processes and dependencies
- Mark role-specific endpoints with priorities (CRITICAL level for admin endpoints)
- Include role coverage reports in analysis results

### Enhanced Report Generation

- **Multi-Format Support**: Generate JSON, Markdown, and Web format reports simultaneously
- **Interactive Visualization**: Use D3.js for web-based visualization with search/filter capabilities
- **Session-Based**: Generate unified reports after complete test session
- **Comprehensive Metadata**: Include test identity, purpose, assertions, and call chains

## Language Stack Support

The skill automatically detects the project's programming language stack and selects appropriate test framework:

- **Python**: pytest with Allure/pytest-html reports
- **Java**: TestNG with REST Assured and Allure reports
- **Node.js**: Jest with supertest and Allure reports
- **Go**: testing package with gotestsum and Allure reports
- **Rust**: cargo test with cargo2junit and Allure reports

For detailed language-specific configuration, see [reference/lang-support.md](reference/lang-support.md).

## Test Design Overview

### Scenario-Based Testing

- **One call chain contains multiple scenarios**
- **One scenario = One test case**
- **Scenario count**: Typically 4-7 times the number of API endpoints

### API Endpoint Relationship Analysis

- Analyze API endpoint relationships and dependencies before writing test cases
- Identify parameter dependencies between endpoints
- Generate call chain diagrams and relationship documentation
- **Implement static analysis probe using AST (Abstract Syntax Tree)** for precise code parsing
  - **AST is the MANDATORY method** for extracting API endpoint information from source code
  - Use language-specific AST parsers (Python: `ast` module, Java: `JavaParser`, Node.js: `@babel/parser`, Go: `go/ast`)
  - Extract endpoint definitions: HTTP methods, paths, parameters, authentication requirements
  - Build call graphs by analyzing function calls and dependencies between endpoints
  - Avoid regex-based parsing which is unreliable for complex code structures

For detailed test design guidelines, see [reference/test-design.md](reference/test-design.md).

## Report Generation Overview

### Template-Based Approach

- Separate data from presentation using pure frontend templates
- JSON data structure with standard schema
- Interactive visualization using D3.js
- Multi-format support (JSON, Markdown, Web)
- **Template files**: report.html (basic), report_enhanced.html (enhanced)
- **Assets directory**: Contains CSS, JavaScript libraries (D3.js), images, fonts

### Enhanced Report Requirements

- Call chain displayed as dedicated table header column
- Assertion information with detailed results
- Input/output parameters and metadata
- Interactive features (search, filter, expand/collapse)

### Template and Assets Management

- **MANDATORY**: Template files and assets directory MUST be copied to reports directory before report generation
- **Template structure**: Pure HTML/CSS/JavaScript files, no server-side processing required
- **Assets content**: Includes D3.js for visualization, styling CSS, and other required resources
- **Automatic copying**: The skill automatically copies template and assets files during report generation

For detailed report format specifications, see [reference/report-format.md](reference/report-format.md).

## Summary

HTTP API Tester is a comprehensive testing framework that focuses on scenario-based testing of complete business workflows through API call chains. It provides automatic language detection, environment self-check, call chain analysis, enhanced report generation, and supports multiple programming languages. The framework follows core testing principles that prioritize response body assertions and test identity/purpose definition. Test files are organized using a core business module principle with a clear directory structure, and reports are generated in multiple formats with interactive visualization.

| For detailed documentation, please refer to the reference documents in the `reference/` directory. | Aspect                       | Endpoint                                        | Call Chain                                          | Scenario |
| -------------------------------------------------------------------------------------------------- | ---------------------------- | ----------------------------------------------- | --------------------------------------------------- | -------- | ------ | -------- | ---------- | -------- |
| Scope                                                                                              | Single API operation         | Complete business workflow (multiple endpoints) | Specific business logic branch within call chain    |
| Example                                                                                            | POST /auth/register          | User registration flow (4 endpoints)            | Successful registration, invalid code, expired code |
| Testing                                                                                            | Unit-level integration       | End-to-end integration                          | Specific request-response path                      |
| Dependencies                                                                                       | None                         | Parameter dependencies between calls            | Defined inputs and expected outputs                 |
| Relationship                                                                                       | Building block of call chain | Contains multiple scenarios                     | One scenario = One test case                        |          | Aspect | Endpoint | Call Chain | Scenario |
| ------------                                                                                       | ---------------------------- | ----------------------------------------------- | --------------------------------------------------- |
| Scope                                                                                              | Single API operation         | Complete business workflow (multiple endpoints) | Specific business logic branch within call chain    |
| Example                                                                                            | POST /auth/register          | User registration flow (4 endpoints)            | Successful registration, invalid code, expired code |
| Testing                                                                                            | Unit-level integration       | End-to-end integration                          | Specific request-response path                      |
| Dependencies                                                                                       | None                         | Parameter dependencies between calls            | Defined inputs and expected outputs                 |
| Relationship                                                                                       | Building block of call chain | Contains multiple scenarios                     | One scenario = One test case                        |          | Aspect | Endpoint | Call Chain | Scenario |
| ------------                                                                                       | ---------------------------- | ----------------------------------------------- | --------------------------------------------------- |
| Scope                                                                                              | Single API operation         | Complete business workflow (multiple endpoints) | Specific business logic branch within call chain    |
| Example                                                                                            | POST /auth/register          | User registration flow (4 endpoints)            | Successful registration, invalid code, expired code |
| Testing                                                                                            | Unit-level integration       | End-to-end integration                          | Specific request-response path                      |
| Dependencies                                                                                       | None                         | Parameter dependencies between calls            | Defined inputs and expected outputs                 |
| Relationship                                                                                       | Building block of call chain | Contains multiple scenarios                     | One scenario = One test case                        |          | Aspect | Endpoint | Call Chain | Scenario |
| ------------                                                                                       | ---------------------------- | ----------------------------------------------- | --------------------------------------------------- |
| Scope                                                                                              | Single API operation         | Complete business workflow (multiple endpoints) | Specific business logic branch within call chain    |
| Example                                                                                            | POST /auth/register          | User registration flow (4 endpoints)            | Successful registration, invalid code, expired code |
| Testing                                                                                            | Unit-level integration       | End-to-end integration                          | Specific request-response path                      |
| Dependencies                                                                                       | None                         | Parameter dependencies between calls            | Defined inputs and expected outputs                 |
| Relationship                                                                                       | Building block of call chain | Contains multiple scenarios                     | One scenario = One test case                        |          | Aspect | Endpoint | Call Chain | Scenario |
| ------------                                                                                       | ---------------------------- | ----------------------------------------------- | --------------------------------------------------- |
| Scope                                                                                              | Single API operation         | Complete business workflow (multiple endpoints) | Specific business logic branch within call chain    |
| Example                                                                                            | POST /auth/register          | User registration flow (4 endpoints)            | Successful registration, invalid code, expired code |
| Testing                                                                                            | Unit-level integration       | End-to-end integration                          | Specific request-response path                      |
| Dependencies                                                                                       | None                         | Parameter dependencies between calls            | Defined inputs and expected outputs                 |
| Relationship                                                                                       | Building block of call chain | Contains multiple scenarios                     | One scenario = One test case                        |          | Aspect | Endpoint | Call Chain | Scenario |
| ------------                                                                                       | ---------------------------- | ----------------------------------------------- | --------------------------------------------------- |
| Scope                                                                                              | Single API operation         | Complete business workflow (multiple endpoints) | Specific business logic branch within call chain    |
| Example                                                                                            | POST /auth/register          | User registration flow (4 endpoints)            | Successful registration, invalid code, expired code |
| Testing                                                                                            | Unit-level integration       | End-to-end integration                          | Specific request-response path                      |
| Dependencies                                                                                       | None                         | Parameter dependencies between calls            | Defined inputs and expected outputs                 |
| Relationship                                                                                       | Building block of call chain | Contains multiple scenarios                     | One scenario = One test case                        |          | Aspect | Endpoint | Call Chain | Scenario |
| ------------                                                                                       | ---------------------------- | ----------------------------------------------- | --------------------------------------------------- |
| Scope                                                                                              | Single API operation         | Complete business workflow (multiple endpoints) | Specific business logic branch within call chain    |
| Example                                                                                            | POST /auth/register          | User registration flow (4 endpoints)            | Successful registration, invalid code, expired code |
| Testing                                                                                            | Unit-level integration       | End-to-end integration                          | Specific request-response path                      |
| Dependencies                                                                                       | None                         | Parameter dependencies between calls            | Defined inputs and expected outputs                 |
| Relationship                                                                                       | Building block of call chain | Contains multiple scenarios                     | One scenario = One test case                        |          | Aspect | Endpoint | Call Chain | Scenario |
| ------------                                                                                       | ---------------------------- | ----------------------------------------------- | --------------------------------------------------- |
| Scope                                                                                              | Single API operation         | Complete business workflow (multiple endpoints) | Specific business logic branch within call chain    |
| Example                                                                                            | POST /auth/register          | User registration flow (4 endpoints)            | Successful registration, invalid code, expired code |
| Testing                                                                                            | Unit-level integration       | End-to-end integration                          | Specific request-response path                      |
| Dependencies                                                                                       | None                         | Parameter dependencies between calls            | Defined inputs and expected outputs                 |
| Relationship                                                                                       | Building block of call chain | Contains multiple scenarios                     | One scenario = One test case                        |          | Aspect | Endpoint | Call Chain | Scenario |
| ------------                                                                                       | ---------------------------- | ----------------------------------------------- | --------------------------------------------------- |
| Scope                                                                                              | Single API operation         | Complete business workflow (multiple endpoints) | Specific business logic branch within call chain    |
| Example                                                                                            | POST /auth/register          | User registration flow (4 endpoints)            | Successful registration, invalid code, expired code |
| Testing                                                                                            | Unit-level integration       | End-to-end integration                          | Specific request-response path                      |
| Dependencies                                                                                       | None                         | Parameter dependencies between calls            | Defined inputs and expected outputs                 |
| Relationship                                                                                       | Building block of call chain | Contains multiple scenarios                     | One scenario = One test case                        |          | Aspect | Endpoint | Call Chain | Scenario |
| ------------                                                                                       | ---------------------------- | ----------------------------------------------- | --------------------------------------------------- |
| Scope                                                                                              | Single API operation         | Complete business workflow (multiple endpoints) | Specific business logic branch within call chain    |
| Example                                                                                            | POST /auth/register          | User registration flow (4 endpoints)            | Successful registration, invalid code, expired code |
| Testing                                                                                            | Unit-level integration       | End-to-end integration                          | Specific request-response path                      |
| Dependencies                                                                                       | None                         | Parameter dependencies between calls            | Defined inputs and expected outputs                 |
| Relationship                                                                                       | Building block of call chain | Contains multiple scenarios                     | One scenario = One test case                        |          | Aspect | Endpoint | Call Chain | Scenario |
| ------------                                                                                       | ---------------------------- | ----------------------------------------------- | --------------------------------------------------- |
| Scope                                                                                              | Single API operation         | Complete business workflow (multiple endpoints) | Specific business logic branch within call chain    |
| Example                                                                                            | POST /auth/register          | User registration flow (4 endpoints)            | Successful registration, invalid code, expired code |
| Testing                                                                                            | Unit-level integration       | End-to-end integration                          | Specific request-response path                      |
| Dependencies                                                                                       | None                         | Parameter dependencies between calls            | Defined inputs and expected outputs                 |
| Relationship                                                                                       | Building block of call chain | Contains multiple scenarios                     | One scenario = One test case                        |          | Aspect | Endpoint | Call Chain | Scenario |
| ------------                                                                                       | ---------------------------- | ----------------------------------------------- | --------------------------------------------------- |
| Scope                                                                                              | Single API operation         | Complete business workflow (multiple endpoints) | Specific business logic branch within call chain    |
| Example                                                                                            | POST /auth/register          | User registration flow (4 endpoints)            | Successful registration, invalid code, expired code |
| Testing                                                                                            | Unit-level integration       | End-to-end integration                          | Specific request-response path                      |
| Dependencies                                                                                       | None                         | Parameter dependencies between calls            | Defined inputs and expected outputs                 |
| Relationship                                                                                       | Building block of call chain | Contains multiple scenarios                     | One scenario = One test case                        |          | Aspect | Endpoint | Call Chain | Scenario |
| ------------                                                                                       | ---------------------------- | ----------------------------------------------- | --------------------------------------------------- |
| Scope                                                                                              | Single API operation         | Complete business workflow (multiple endpoints) | Specific business logic branch within call chain    |
| Example                                                                                            | POST /auth/register          | User registration flow (4 endpoints)            | Successful registration, invalid code, expired code |
| Testing                                                                                            | Unit-level integration       | End-to-end integration                          | Specific request-response path                      |
| Dependencies                                                                                       | None                         | Parameter dependencies between calls            | Defined inputs and expected outputs                 |
| Relationship                                                                                       | Building block of call chain | Contains multiple scenarios                     | One scenario = One test case                        |
