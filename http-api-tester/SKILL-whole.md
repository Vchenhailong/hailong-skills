---
name: http-api-tester
description: HTTP API endpoint testing framework with call chain analysis, parameter dependency tracking, Mock support, automatic environment self-check, dependency installation, test data naming convention (AIT_/ait_), test data context acquisition, production environment protection, real-world data validation, image generation for file upload testing, multi-role analysis, and comprehensive test reports including author (hailong.chen) and AI model information. Enhanced report generation with JSON/Markdown/Web formats, scenario-based test counts, coverage rates, interactive visualization, and smart incremental updates. Invoke when user needs API interface testing, call chain analysis, multi-role analysis, or HTTP endpoint validation.
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
- User needs multi-role analysis and cross-role business flow testing

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

## Automatic Programming Language Detection

**Priority Language Detection:**
This skill automatically detects the project's programming language stack when invoked, prioritizing backend languages for API testing.

**Detection Methods:**
- ✅ **Feature File Analysis**: Checks for language-specific configuration files
  - `pyproject.toml` or `requirements.txt` → Python
  - `pom.xml` or `build.gradle` → Java
  - `package.json` → Node.js
  - `go.mod` → Go
  - `Cargo.toml` → Rust
- ✅ **Project Structure Analysis**: Analyzes directory structure and file extensions
- ✅ **Backend Language Priority**: Prioritizes backend languages for API testing
- ✅ **Mixed Language Handling**: Automatically selects backend language in mixed projects

**Language Detection Results:**
- **Auto Framework Selection**: Automatically selects appropriate test framework (pytest/TestNG/Jest/testing/cargo test)
- **Auto Dependency Setup**: Automatically configures language-specific dependencies
- **Auto Report Metadata**: Automatically fills `language_stack` field in reports

**Supported Language Stacks:**
- Python (pytest)
- Java (TestNG)
- Node.js (Jest)
- Go (testing)
- Rust (cargo test)

## Environment Self-Check and Installation

**Automatic Environment Validation:**
This skill includes a comprehensive environment self-check and installation system that automatically verifies all required dependencies before running tests.

**Features:**
- ✅ **Language Stack Detection**: Automatically detects project's programming language stack (Python/Java/Node.js/Go/Rust) and selects appropriate test framework
- ✅ **Version Check**: Validates language version is installed (Python 3.8+, Java 8+, Node.js 14+, Go 1.18+, Rust 1.65+)
- ✅ **Package Verification**: Checks all required packages and versions for detected language stack
- ✅ **Command-Line Tool Detection**: Verifies Allure and other tools are available with color-coded status
- ✅ **Automatic Installation**: Provides one-command installation for missing dependencies using appropriate package manager
- ✅ **Clear Reporting**: Shows detailed status of each dependency
- ✅ **Cross-Platform Support**: Works on Linux, macOS, and Windows
- 🔧 **Platform Detection Priority**: MUST detect operating system and platform characteristics FIRST before any environment checks
  - Identify target platform (Windows/Linux/macOS)
  - Understand platform-specific command-line tool behaviors (e.g., .BAT files on Windows require shell=True)
  - Use platform-specific path separators and environment variable formats
  - Handle platform-specific package managers and installation methods
  - Adapt subprocess execution parameters based on platform (shell=True for Windows batch files, etc.)
- 🟡 **Priority Installation**: Uses language-specific package managers (uv/pip for Python, Maven/Gradle for Java, npm/yarn for Node.js, go mod for Go, cargo for Rust)
- 📋 **Dependency Management**: Requires consistent dependency management file for detected language stack
- 🔒 **Compatibility**: Ensures all dependencies are compatible versions

**Required Dependencies:**

Dependencies are automatically determined based on detected language stack:

**Python Stack (pytest):**
- Python 3.8+ (3.10+, 3.11+ recommended)
- pytest >= 7.4.0
- pytest-asyncio >= 0.21.0
- pytest-cov >= 4.1.0
- pytest-html >= 3.2.0
- allure-pytest >= 2.13.0
- requests >= 2.31.0
- httpx >= 0.24.0
- responses >= 0.23.0
- aioresponses >= 0.7.0
- pydantic >= 2.0.0
- Allure (command-line tool) - Optional but recommended

**Java Stack (TestNG):**
- Java 8+ (Java 11+ recommended)
- TestNG >= 7.0.0
- REST Assured >= 5.0.0
- Allure TestNG >= 2.13.0
- JUnit >= 5.0.0
- Maven/Gradle (build tool)
- Allure (command-line tool) - Optional but recommended

**Node.js Stack (Jest):**
- Node.js 14+ (Node.js 16+ recommended)
- Jest >= 27.0.0
- @types/jest >= 27.0.0
- supertest >= 6.0.0
- axios >= 1.0.0
- jest-html-reporters >= 3.0.0
- allure-jest >= 2.0.0
- Allure (command-line tool) - Optional but recommended

**Go Stack (testing):**
- Go 1.18+ (Go 1.20+ recommended)
- gotestsum >= 1.8.0
- go-junit-report >= 2.0.0
- Allure Go >= 2.0.0
- Allure (command-line tool) - Optional but recommended

**Rust Stack (cargo test):**
- Rust 1.65+ (Rust 1.70+ recommended)
- cargo2junit >= 0.4.0
- Allure Rust >= 0.1.0
- Allure (command-line tool) - Optional but recommended

**Color-Coded Status Indicators:**
- ✅ **Green**: Dependency is installed and available
- 🟡 **Orange**: Dependency is missing but can be auto-installed
- 🔴 **Red**: Dependency is required but cannot be auto-installed (manual intervention needed)

## Core Capabilities

**Automatic HTTP Call Relationship Analysis:**
- Identify and record API call execution order
- Generate call chain relationship diagrams using Graph or Mermaid syntax
- Present static call chains with parameter passing visualization

**Multi-role Analysis:**
- Identify different user roles in the system
- Analyze role-specific API endpoints and access permissions
- Generate role-specific call chains and cross-role business flows
- Detect cross-role dependencies and interactions
- Validate role permission boundaries and coverage
- Provide comprehensive role analysis reports

## Core Testing Principles (MANDATORY)

**PRINCIPLE 1: Test Identity and Test Purpose**

- Define test identity (who performs test)
- Define test purpose (what business behavior is validated)

**PRINCIPLE 2: Check Business Key Points in Response Body**

- Assertions MUST validate response body field values (if applicable)
- HTTP status code assertions acceptable ONLY when response body is empty

**MANDATORY Enforcement**

- All test cases MUST follow both core principles
- Test reports MUST include test identity and test purpose information
- Test reports MUST include assertion information for response body validation

## Testing Constraints (STRICT)

**REQUIRED Test Data Prefix:**
- **Non-real-world data validation test data** MUST use prefix "AIT_" or "ait_"
- This applies to: usernames, product names, test business logic data, etc.
- **Does NOT include application self-maintained id, uuid** (such as id, uuid, etc. should only be read from response body, or obtained by querying corresponding data from database when necessary)
- **Real-world data validation test data** does NOT require prefix
- This applies to: validating real email formats, real phone number formats, real ID card formats, etc.
- Purpose: Easy identification and cleanup of test data, while allowing real-world data format validation

**Distinction Criteria:**
- **Requires AIT_ prefix**: Used for testing business logic, creating test objects, mock data
  - Examples: `AIT_test_user_001`, `AIT_order_12345`, `AIT_test_product_xyz`
  - Field types: username, name, product_name, title, description, etc.
- **Does NOT require AIT_ prefix**: Used for validating real-world data formats
  - Examples: `test@example.com` (validate email format), `13800138000` (validate phone format), `110101199001011234` (validate ID card format)
  - Field types: email, phone, phone_no, phone_number, mobile_no, mobile_number, Tel, Telephone, id_card, id_number, social_security, ssn, etc. (case-insensitive for compatibility)

**Application Self-Maintained Fields Handling:**
- **id, uuid, etc. fields**: Only read from response body, or obtained by querying corresponding data from database when necessary
- **date, time, datetime, timestamp, etc. fields**: Application self-maintained
  - If writing: Generate according to type rules
  - If reading: Only read from response body, or obtained by querying corresponding data from database when necessary

**Fallback Strategy for Unmentioned Fields:**

For test data fields not mentioned in `REAL_WORLD_DATA_FIELDS` and `SELF_MAINTAINED_FIELDS` lists, apply the following fallback strategy:

**Rule Priority:**
1. **REAL_WORLD_DATA_FIELDS** (highest priority)
2. **SELF_MAINTAINED_FIELDS** (medium priority)
3. **Fallback strategy** (lowest priority)

**Fallback Strategy:**
- **For unmentioned fields**: Application self-maintained
  - **If writing**: Get value based on business type inferred from field name
    - Type-related fields (type, enum, status, state, etc.): Use business-specific values
    - User-related fields (user, customer, client, etc.): Use `AIT_{field}_001`
    - Order-related fields (order, transaction, payment, etc.): Use `AIT_{field}_001`
    - Product-related fields (product, item, goods, etc.): Use `AIT_{field}_001`
    - Default: Use `AIT_{field}_001`
  - **If reading**: Only read from response body, or obtained by querying corresponding data from database when necessary

This fallback strategy applies to all language stacks:

- **Python (pytest)**: Implement in `TestDataValidator` class
- **Java (TestNG)**: Implement in `TestDataValidator` class
- **Node.js (Jest)**: Implement in `TestDataValidator` class
- **Go (testing)**: Implement in `TestDataValidator` function
- **Rust (cargo test)**: Implement in `TestDataValidator` struct

## Test Framework Selection

**PREREQUISITE: Test framework and report tools are selected based on detected language stack. The following sections show available options for each supported language stack.**

**Python Environment:**
- **pytest** (Primary recommendation)
  - Mature ecosystem
  - Powerful fixtures
  - Excellent plugins (pytest-asyncio, pytest-cov, pytest-html)
  - Support for async testing

**Java Environment:**
- **TestNG** (Primary recommendation)
  - Robust testing framework
  - Parallel execution support
  - Good integration with REST Assured

**Java Report Tools:**
- **Allure TestNG** (Primary): Rich interactive reports with timeline, steps, attachments
- **ExtentReports**: Comprehensive HTML reports with charts and screenshots
- **JUnit HTML**: Simple, lightweight HTML reports

**Node.js Environment:**
- **Jest** (Primary recommendation)
  - Zero configuration setup
  - Built-in assertions and mocking
  - Excellent TypeScript support
  - Parallel test execution
- **Mocha** (Alternative)
  - Flexible and extensible
  - Rich plugin ecosystem
  - Good for custom test runners

**Node.js Report Tools:**
- **Jest HTML Reporter**: Built-in HTML reports with coverage
- **Mochawesome**: Beautiful HTML reports with charts and screenshots
- **Allure Jest**: Rich interactive reports with timeline and attachments

**Go Environment:**
- **testing** (Built-in package)
  - Standard library support
  - Table-driven tests
  - Benchmark support
  - Race condition detection

**Go Report Tools:**
- **gotestsum**: JUnit XML output with colored console output
- **go-junit-report**: JUnit XML format for CI/CD integration
- **Allure Go**: Rich interactive reports with timeline and attachments

**Rust Environment:**
- **cargo test** (Built-in)
  - Integrated with Cargo
  - Thread-safe execution
  - Benchmark support
  - Documentation tests

**Rust Report Tools:**
- **cargo2junit**: JUnit XML format for CI/CD integration
- **Allure Rust**: Rich interactive reports with timeline and attachments

## Test Scenario Definition (MANDATORY)

**CRITICAL: Understanding What a Test Scenario Is**

**Definition:**
- **A test scenario refers to a specific request-response business logic branch**, NOT a single HTTP endpoint
- A scenario represents a specific business logic path through the call chain
- Each scenario is a specific test case with defined inputs and expected outputs
- **One call chain often contains multiple scenarios**
- **One scenario = One test case**

**Example Scenario:**
```
Call Chain: User Registration Flow
├── POST /auth/send-verify-code (send verification code)
├── POST /auth/register (register with code)
├── POST /auth/token (login to get token)
└── GET /auth/me (get user profile)

Scenarios within this call chain:
├── Scenario 1: Successful user registration (all API calls succeed)
├── Scenario 2: Registration with invalid verification code (register API returns error)
├── Scenario 3: Registration with expired code (register API returns error)
└── Scenario 4: Registration with duplicate username (register API returns error)
```

**Key Distinctions:**
- ❌ **Scenario ≠ Single HTTP endpoint** (e.g., POST /auth/register is NOT a scenario)
- ❌ **Scenario ≠ Complete call chain** (e.g., the entire user registration flow is a call chain, not a single scenario)
- ✅ **Scenario = Specific business logic branch** (e.g., successful registration, invalid code, expired code are different scenarios)
- ✅ **One call chain often contains multiple scenarios**
- ✅ **One scenario = One test case**
- ✅ **Each scenario represents a specific request-response path with defined inputs and expected outputs**

**Why This Definition Matters:**
1. **Test Coverage**: Ensures complete business workflows are tested, not just individual endpoints
2. **Parameter Dependencies**: Captures data flow between related API calls
3. **Business Logic**: Validates end-to-end business processes
4. **Integration Testing**: Tests how endpoints work together as a system

**Scenario vs. Endpoint:**
| Aspect       | Endpoint                     | Call Chain                                      | Scenario                                            |
| ------------ | ---------------------------- | ----------------------------------------------- | --------------------------------------------------- |
| Scope        | Single API operation         | Complete business workflow (multiple endpoints) | Specific business logic branch within call chain    |
| Example      | POST /auth/register          | User registration flow (4 endpoints)            | Successful registration, invalid code, expired code |
| Testing      | Unit-level integration       | End-to-end integration                          | Specific request-response path                      |
| Dependencies | None                         | Parameter dependencies between calls            | Defined inputs and expected outputs                 |
| Relationship | Building block of call chain | Contains multiple scenarios                     | One scenario = One test case                        |

**Mandatory Requirement:**
- Test design MUST be based on scenarios (specific business logic branches), not individual endpoints
- Each scenario identified in call chain analysis must have corresponding test cases
- Test dimensions (positive business scenarios, errors, edge cases, security) apply to EACH scenario
- **CRITICAL**: Positive business scenarios MUST be covered (not just happy path, but all normal business logic branches)
- **IMPORTANT**: Scenario count is typically 4-7 times the number of API endpoints. When the ratio is lower than this range, you MUST repeatedly check for uncovered scenarios and complete all scenarios until you are certain that all scenarios have been covered.

## API Endpoint Relationship Analysis Before Test Design (MANDATORY)

**CRITICAL: Analyze Endpoint Relationships BEFORE Writing Test Cases**

Before implementing any test cases, you MUST:
1. Analyze API endpoint relationships and dependencies
2. Identify parameter dependencies between endpoints
3. Generate call chain diagrams
4. Output relationship documentation
5. Implement static analysis probe file
6. Then design test cases based on this analysis

**Mandatory Output File Naming (in test framework standard analysis directory):**
- `call_chain_analysis.md`: Complete call chain analysis document with endpoint relationships
- `dependency_analysis.md`: Parameter dependency analysis between endpoints
- `call_chain_diagram.md`: Mermaid diagram for call chain visualization

**Static Analysis Probe Requirements:**
- **File Path**: Must be implemented in `scripts/` directory of the project root
- **File Name**: `call_chain_probe.py` (Python), `CallChainProbe.java` (Java), `call-chain-probe.js` (Node.js), `call_chain_probe.go` (Go), `call_chain_probe.rs` (Rust)
- **Functionality**: Static analysis probe that automatically:
  - Scans source code for API endpoint definitions
  - Identifies endpoint relationships and dependencies
  - Generates call chain analysis data
  - Validates call chain integrity
  - Detects potential dependency issues
  - Exports analysis results to standard format
- **Implementation**: Must use language-specific static analysis libraries and follow project coding standards
- **Output**: Generate structured data compatible with call chain analysis documentation

**Default Analysis Directories by Language Stack:**
- **Python (pytest)**：`tests/analysis/`
- **Java (TestNG)**：`src/test/analysis/`
- **Node.js (Jest)**：`tests/analysis/` or `__tests__/analysis/`
- **Go (testing)**：`tests/analysis/` or same directory as test files
- **Rust (cargo test)**：`tests/analysis/` or `src/analysis/`

**Why This Approach:**
- Ensures comprehensive test coverage of endpoint interactions
- Prevents missing critical integration scenarios
- Identifies potential data flow issues early
- Provides clear documentation of system behavior
- Makes test design more systematic and thorough

**Analysis Workflow:**

**CRITICAL: Detect and Report Coverage Gaps**

After generating test case definitions, you MUST perform a self-check to identify any gaps between call chain analysis and test case design.

**Why This Step:**
- Ensures comprehensive test coverage
- Prevents missing critical integration scenarios
- Identifies untested endpoints and dependencies
- Provides actionable recommendations for test case supplementation
- Validates completeness of test design

**MANDATORY REQUIREMENT:**
When coverage gaps are detected, you MUST supplement test cases BEFORE proceeding to test execution. This is a blocking requirement to ensure test completeness.

**Gap Detection Logic:**

1. **Longest Dependency Chain Coverage** (CRITICAL):
   - ✅ Complete coverage of the maximum dependency chain
   - ✅ Functional coverage of each node in the maximum dependency chain
   - ✅ Validation of dependencies between nodes in the maximum dependency chain
   - ✅ Data consistency validation in the maximum dependency chain
   - ✅ Static analysis probe validation of chain integrity
2. **Business Process Coverage**:
   - Call chain coverage: Ensure all call chains have corresponding tests
   - Scenario coverage: Verify all business scenarios are covered
   - Data consistency coverage: Complete process data consistency validation
   - Parameter validation coverage for each chain node
   - Error handling coverage for each chain node
   - Business return code coverage for each chain node (when no return code, response body structure must be covered)
   - Static analysis probe validation of business process flow
3. **General Coverage**:
   - Dependency coverage: Verify all parameter mappings are tested
   - Error scenario coverage: Verify error cases for all endpoints (including HTTP status codes and business return codes, if applicable)
   - Edge case coverage: Verify boundary value and edge case tests
   - Security scenario coverage: Verify authentication and authorization tests
   - Static analysis probe detection of potential issues

**Gap Severity Levels:**
- **CRITICAL**:
  - ✅ Untested maximum dependency chain (longest chain with actual dependencies)
  - ✅ Critical nodes in the maximum dependency chain (POST/DELETE)
  - ✅ Untested call chains, critical endpoints (POST/DELETE)
- **HIGH**: Untested endpoints with high business impact, error scenarios, security scenarios
- **MEDIUM**: Untested dependencies, edge cases, boundary values
- **LOW**: Untested optional features or minor scenarios

**MANDATORY Actions When Gaps Detected:**
1. **Review Gap Report**: Carefully review coverage gap report
2. **Prioritize Gaps**: Address CRITICAL and HIGH severity gaps first
3. **Supplement Test Cases**: Create test cases for identified gaps
4. **Re-run Analysis**: After supplementing, re-run gap detection to verify coverage
5. **Update Documentation**: Update test case definitions and documentation
6. **Blocking Requirement**: Cannot proceed to test execution until CRITICAL and HIGH gaps are addressed

**Test Case Design Framework:**

**PREREQUISITE: Test case call paths MUST be explicitly based on call chain analysis results and static analysis probe validation.**

**MANDATORY: Scenario Coverage Matching**
- HTTP scenario test cases MUST be designed based on call chain analysis scenarios
- **CRITICAL: Call chain analysis provides framework (which endpoints and scenarios to test)**
- **CRITICAL: Static analysis probe provides validation and integrity checks**
- **CRITICAL: Test dimensions (edge cases, error scenarios, security scenarios) apply to EACH call chain scenario**
- If scenario test cases are fewer than call chain analysis results, MUST continue implementing to match
- All existing test cases must be maintained while supplementing missing scenarios
- Test case design MUST be validated against static analysis probe results

**Test Dimensions Applied to Each Call Chain Scenario:**
For EACH scenario identified in call chain analysis, MUST cover:
1. Happy path (successful scenarios)
2. Error cases (HTTP status codes and business return codes, if applicable)
3. Edge cases (boundary values, empty inputs)
4. Security scenarios (authentication, authorization)
5. Data validation scenarios

**Relationship:**
- Call chain analysis = Framework (WHAT to test - endpoints and scenarios)
- Test dimensions = Coverage (HOW to test - edge cases, errors, security)
- Both are complementary, NOT mutually exclusive

**Test Case Design Principles:**
- ✅ Adopt "atomic layer + business layer" layered design pattern, but atomic layer cannot be used as test cases, instead it is organized and called by business layer
- ✅ Must use the **maximum dependency chain** (longest chain with actual dependencies) identified in the system as the core test design basis
- ✅ Design complete business process tests based on call chain analysis, including parameter validation and error handling for each call chain node
- ✅ Test case call paths follow call chains identified in API endpoint relationship analysis
- ✅ Each call chain from analysis must have corresponding test cases
- ✅ Maximum dependency chain test coverage must reach 100%
- ✅ Test cases must validate parameter dependencies identified in analysis
- ✅ Test execution order: Normal main flow first, then other business branch flows, finally exception flows of each chain node
- ✅ Test execution order respects call sequence defined in analysis

**Test Case Metadata Requirements:**
- Test titles: Must be descriptive and clearly indicate what is being tested
- Test descriptions: Must explain test purpose, test data, and expected behavior
- Test titles and descriptions MUST be displayed in HTML report headers for all tests
- File name: Test case file name (NOT file name of object under test) must be captured and included in reports
- Class method name: Test method identifier must be captured and included in reports
- Input parameters: Request parameters sent to API endpoints must be recorded
- Output parameters: Response parameters received from API endpoints must be recorded
- Assertion information: Each assertion step in test case must be recorded in "assertion info" table column
  - **CRITICAL: Assertions MUST NOT be limited to HTTP status codes only**
  - **CRITICAL: Assertions MUST validate key information in response body** (e.g., specific field values, business return codes, information descriptions)
  - Exception: If response body is empty or does not contain these fields, HTTP status code assertions are acceptable
  - Assertion details include: assertion type, expected value, actual value, assertion result
  - Passed assertions displayed in normal font color
  - Failed assertions displayed in red font color for clear identification
  - Assertion information MUST be visible in main report table, NOT in test case details
- Metadata MUST be captured and included in generated reports

**Test Data Naming Convention:**
- ✅ Prefix test data with `AIT_` (e.g., `AIT_test_user_001`)
- ✅ Use UUID or timestamps for uniqueness
- ✅ Clean up test data after test execution
- ✅ Use Fixture mechanism to manage test data generation and cleanup
- ✅ Test data unified management, supporting Session-level sharing

## Test File Organization Requirements (MANDATORY)

**CRITICAL: Test files MUST be organized to support unified session execution**

**Mandatory Requirements:**
1. **Directory Structure**:
   - ✅ `testcases/`: Test case directory, organized by business modules/scenarios
   - ✅ `testcases/atomic/`: Atomic layer directory for single API endpoint tests
2. **Unified Execution Capability**: All test files MUST be executable in a single test session
3. **Core Business Module Principle**:
   - ✅ Test files SHOULD be organized by **core business module + business process** principle
   - ✅ Core business module is determined by: business purpose, final output, and business domain
   - ✅ When involving multiple modules, use the **core business module** as the main naming basis
4. **File Naming Rules**:
   - ✅ Atomic layer: Use business module name directly, e.g., `order.py` for single API endpoint tests
   - ✅ Business layer: Use `test_{core_module}.py` format, e.g., `test_order.py` for complete business flow tests
   - ✅ Must create a dedicated test file for the maximum dependency chain (longest chain with actual dependencies) identified in the system
   - ✅ Maximum dependency chain test file naming: `test_max_dependency_chain.py`
5. **Full Coverage Execution**: Single command MUST execute all tests across all files
6. **Session Completeness**: All test results MUST be collected in one session for unified report generation

**Implementation Examples:**

**Python (pytest):**
```python
# tests/conftest.py
import pytest

# Scenario markers
pytest.mark.scenario_user_registration = pytest.mark.scenario_user_registration
pytest.mark.scenario_order_creation = pytest.mark.scenario_order_creation
```

**Execution Commands:**
- Run all tests: `pytest tests/ -v`
- Run specific scenario: `pytest tests/ -m scenario_user_registration`

**Java (TestNG):**
```xml
<!-- testng.xml -->
<suite name="AllScenarios">
    <test name="AllTests">
        <packages>
            <package name="com.example.tests.*"/>
        </packages>
    </test>
</suite>
```

**Execution Commands:**
- Run all tests: `mvn test` or `gradle test`

**Node.js (Jest):**
```javascript
// jest.config.js
module.exports = {
    testMatch: [
        '**/tests/**/*.test.js',
        '**/tests/**/*.spec.js'
    ]
};
```

**Execution Commands:**
- Run all tests: `jest`

**Go (testing):**
```go
//go:build auth
// +build auth

package auth_test

func TestLogin(t *testing.T) {
}
```

**Execution Commands:**
- Run all tests: `go test ./...`
- Run specific tag: `go test -tags=auth ./...`

**Rust (cargo test):**
```rust
#[cfg(test)]
mod auth_tests {
    use super::*;

    #[test]
    fn test_login() {
    }
}
```

**Execution Commands:**
- Run all tests: `cargo test`
- Run specific test: `cargo test auth`

**Blocking Requirement:**
- Test files MUST be organized before test execution begins
- Cannot proceed to test execution if unified execution capability is not established
- This is a prerequisite for generating complete session reports

## Test Execution Workflow

**Phase 0: Static Analysis Validation**
- Run static analysis probe from `scripts/` directory to validate call chain integrity
- Generate pre-test call chain analysis report
- Identify potential dependency issues before test execution
- Block test execution if CRITICAL issues are detected

**Phase 1: Test Discovery**
- Scan test files following framework conventions
- Identify test cases and fixtures
- Build test execution plan based on static analysis results

**Phase 2: Test Execution**
- Execute tests in dependency order validated by static analysis
- Capture call chains and dependencies
- Record test results and metrics
- Validate real-time execution against static analysis predictions

**Phase 3: Result Validation**
- Verify response status codes and business return codes (if applicable)
- Validate response schemas
- Check business logic correctness
- Compare execution results with static analysis predictions

**Phase 4: Report Generation (Post-Session Unified Generation)**
- **Unified Report Generation**: All test execution reports are generated AFTER complete test session finishes
- **Session Completion Requirement**: Reports are only generated once all test cases in session have been executed
- **Comprehensive Data Collection**: Gather execution results, coverage statistics, call chains, and assertion information from entire test session
- **Static Analysis Integration**: Include static analysis probe results in the unified report
- **Single Report Generation**: Generate unified reports containing complete test session results rather than individual test reports
- **One Complete Data File Per Session**: Each test session generates and only generates one complete data file containing all test results for that session, not multiple scattered data files
- **Full Data File**: The generated data file must contain all test results for the session (passed, failed, skipped), not partial data files
- **Non-Incremental Updates**: Each test session regenerates a complete data file, not adding new data on top of old files
- **Coverage Statistics Calculation**: Calculate overall session coverage based on all executed tests
- **Failed Tests Summary**: Compile and identify all failed tests and issues from the complete session
- **Static Analysis Findings**: Include static analysis probe findings and recommendations
- **Report Consolidation**: Merge results from multiple test files/scenarios into unified session report

**Phase 5: Report Validation (MANDATORY)**
- Validate report completeness and correctness
- Verify all required report elements are present
- Ensure call chain is displayed as a table header column
- Check test metadata completeness

**Report Validation Requirements:**
This is a mandatory final step to ensure test reports meet all quality standards before delivery.

**Validation Check Items:**

1. **Table Header Information Validation**
   - ✅ Test title is displayed in report header
   - ✅ Test description is displayed in report header
   - ✅ File name (test case file name, NOT file name of object under test) is included in the report
   - ✅ Class method name is included in the report
   - ✅ Call chain is displayed as a dedicated table header column (NOT in test case details)
   - ✅ Assertion information is displayed as a dedicated table header column "assertion info"
   - ✅ Failed assertions are displayed in red font color for easy identification

2. **Call Chain Validation**
   - ✅ Each test has a corresponding call chain displayed in the "call chain" table column
   - ✅ Call chain diagrams correctly show endpoint relationships
   - ✅ Parameter dependencies are clearly marked in the call chain
   - ✅ Call chain is visible in the main report table, not hidden in test case details

3. **Assertion Information Validation**
   - ✅ Each assertion step in test case is recorded in the "assertion info" table column
   - ✅ Assertion details include: assertion type, expected value, actual value, assertion result
   - ✅ Passed assertions are displayed in normal font color
   - ✅ Failed assertions are displayed in red font color for clear identification
   - ✅ Assertion information is visible in the main report table, not hidden in test case details

4. **Input/Output Parameters Validation**
   - ✅ Request parameters are recorded in the report
   - ✅ Response parameters are recorded in the report
   - ✅ Parameter passing relationships are clearly documented
   - ✅ Parameter values are displayed in the report

5. **Metadata Validation**
    - ✅ Test execution time is recorded
    - ✅ Test status is correctly displayed
    - ✅ Assertion results are detailed and accurate
    - ✅ All required metadata is captured and included
    - ✅ File name refers to test case file name, not file name of object under test
    - ✅ Assertion information is properly formatted with failed assertions in red

**Validation Result Handling:**
- **PASS**: Report meets all requirements, can be output normally
- **WARNING**: Some information is missing but report can still be output (warning information recorded)
- **FAIL**: Critical information is missing, requires supplementation or fixes before regenerating report
  - **CRITICAL: User Notification for FAIL**: When validation fails, MUST explicitly inform user with:
    - Detailed failure reason and which validation items failed
    - Specific missing or incorrect information
    - **Prompt for automatic fix**: Explicitly inform user that they can request automatic fix for the validation failures
  - User can review failure information and decide whether to request automatic fix

**Blocking Requirement:**
- Reports with CRITICAL or HIGH severity validation failures cannot be delivered
- Must fix validation issues and regenerate reports before proceeding
- User must be informed of the blocking nature and can request automatic fix

**Intelligent Report Generation:**
- Auto-detect Allure runtime environment
- Priority: Allure > HTML > Terminal & Console
- Generate comprehensive test reports with call chain diagrams
- Include response body assertions validation results
- Track concurrent execution statistics

**Report Detection and Generation Flow:**
**PREREQUISITE: Report generation method is determined based on detected language stack.**

**Technical Implementation Considerations:**
The following requirements (call chain, assertion information, file name, etc.) are defined as quality standards for test reports. However, actual implementation depends on capabilities of selected report tools. When standard report tools (Allure, pytest-html, Jest HTML Reporter, etc.) cannot fully meet these requirements, following approaches should be considered:

1. **Custom Report Generator Development**: Develop custom report generators for each language stack to ensure full compliance with all requirements
2. **Post-Processing Enhancement**: Use standard report tools for base report generation, then apply post-processing scripts to add custom content
3. **Requirement Adaptation**: Adjust specific display requirements to match capabilities of available report tools while maintaining information completeness

**Priority Approach**: Custom report generator development is recommended for full compliance with all report requirements.

1. Check if external report tools are available (Allure, coverage tools, etc.)
2. If available: Generate reports using language-specific external tools
   - Python: allure-pytest, pytest-cov
   - Java: Allure TestNG, JaCoCo
   - Node.js: allure-jest, istanbul/nyc
   - Go: Allure Go, go tool cover
   - Rust: Allure Rust, tarpaulin/cargo-tarpaulin
3. If unavailable: Generate HTML reports using language-specific HTML reporters
   - Python: pytest-html
   - Java: JUnit HTML or ExtentReports
   - Node.js: Jest HTML Reporter or Mochawesome
   - Go: gotestsum with HTML output
   - Rust: cargo2junit with HTML conversion
4. All external processes run in non-blocking background mode
5. Always generate summary output in terminal & console

**Important Notes on Non-Blocking Behavior:**
1. **Test execution never waits for external processes**: Tests complete and exit immediately
2. **External processes run in background**: All external application processes (report generation, coverage tools, etc.) run asynchronously
3. **Session-End Report Generation**: Report generation processes are initiated only after the entire test session completes, not during individual test execution
4. **Automatic fallback**: If external processes fail or are unavailable, alternative methods are used
5. **No process blocking**: Neither test process nor application process is blocked by external processes
6. **Unified Session Reports**: All reports are generated as complete session summaries rather than individual test reports

**Required Report Elements:**
- Test execution summary (total, passed, failed, skipped)
- Response body assertion results (validated parameters and values)
- Coverage statistics (endpoints covered, scenarios covered)
- Call chain displayed as a dedicated table header column "call chain" for all tests (both passed and failed) - MUST be visible in main report table, NOT in test case details
- Assertion information displayed as a dedicated table header column "assertion info" for all tests - MUST be visible in main report table, NOT in test case details
  - Each assertion step in test case must be recorded
  - Assertion details include: assertion type, expected value, actual value, assertion result
  - Passed assertions displayed in normal font color
  - Failed assertions displayed in red font color for clear identification
- Parameter dependency documentation
- Input/output parameters (request parameters, response parameters, parameter values)
- File name (test case file name, NOT file name of object under test)
- Class method name (test method identifier)
- Business value tracking reports
- Concurrent execution metrics (threads used, execution time)
- Detailed failure logs with stack traces
- Response body attachments for failed tests
- Test titles and descriptions (displayed in HTML report headers for all tests)

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

For detailed report format specifications, see [reference/report-format.md](reference/report-format.md)

**Implementation Note:**
The above requirements define the quality standards for test reports. Actual implementation may require custom report generators or post-processing scripts to achieve full compliance with these standards, especially for:
- Custom table header columns ("call chain", "assertion info")
- Assertion step details in table format
- Red font color for failed assertions
- File name and class method name in main report table

**Report Formats:**
- Allure HTML report (interactive, preferred)
- HTML report (fallback, human-readable)
- JSON report (machine-readable)
- Terminal & Console output (quick summary)

**Enhanced Report Requirements:**
- **Three Report Files**: Must generate JSON, Markdown, and Web format reports simultaneously
- **Data File Generation Principles**: Follow one complete data file per session, full data file, and non-incremental update principles (see Phase 4: Report Generation)
- **JSON Enhancement**: Must include scenario-based test counts, call chains, coverage rates, pass rates, and assertion details
- **Markdown Content**: Must include test file paths, call chain information, class method details, and input/output parameters
- **Web Visualization**: 
  - MUST implement interactive visualization using D3.js or similar libraries (no technical or environmental restrictions)
  - Default priority: Use D3.js for web-based visualization
  - Display all enhanced content with interactive features (search, filter, expand/collapse)
  - Support viewing actual tested API full paths, request details, and response details
- **Content Incremental Updates**: Smart overwrite mode - same scenario test cases overwrite update while preserving history traces, with change highlighting and version traceability
- **User Experience**: Appropriate styling, correct interactions, elegant visual design, responsive layout
- **File Standards**: Report file paths and naming follow test framework default behavior

## Template-Based Report Generation

### Architecture Overview

The report generation uses a **template-based approach** that separates data from presentation:

1. **Template (Pure Frontend)**: 
   - Single HTML file with embedded CSS and JavaScript
   - Language-agnostic - works with any backend
   - Loads JSON data dynamically via browser fetch API
   - No server-side processing required
   - Template files: report.html (basic template), report_enhanced.html (enhanced template)
   - **MANDATORY**: Template file(s) and assets directory MUST be copied to reports directory

2. **Data (JSON Format)**:
   - Standardized JSON structure defined by JSON Schema
   - Generated by language-specific test frameworks
   - Contains all test results, call chains, coverage stats
   - Language-agnostic format
   - Schema file: report_data_schema.json

3. **Assets (Supporting Files)**:
    - Contains CSS, JavaScript libraries (D3.js), images, fonts
    - Required for proper template rendering and visualization
    - **MANDATORY**: Assets directory MUST be copied to reports directory along with template file

4. **Adapters (Optional)**:
    - Provide convenience functions for generating standard JSON
   - Convert framework-specific formats to standard JSON
   - Auto-fill metadata (timestamps, language stack versions)
   - Validate data against JSON Schema
   - Adapter files: python_adapter.py, java_adapter.java, nodejs_adapter.js, go_adapter.go

### Template Usage

**IMPORTANT: Template and Assets Copy Requirement**

**MANDATORY**: The template file(s) (report.html or report_enhanced.html) and assets directory MUST be copied to reports directory before report generation. This is a critical requirement for the template-based report system to function properly.

**Option 1: Direct JSON Loading (Recommended)**

1. **Copy Template and Assets (MANDATORY)**: **MUST copy** template file(s) and assets directory to reports directory
2. Place template and JSON in same directory (EXAMPLE):
   ```
   reports/
   ├── report.html           # Basic template file (optional)
   ├── report_enhanced.html  # Enhanced template file (optional, recommended)
   ├── assets/               # Assets directory (MUST be copied)
   └── report.json          # Generated by test framework
   ```
3. Open `report.html` or `report_enhanced.html` in browser
   - Template automatically loads `report.json` and renders
   - No server required

**Option 2: URL Parameter Loading (EXAMPLE)**

1. **Copy Template and Assets (MANDATORY)**: **MUST copy** template file(s) and assets directory to reports directory
2. Specify JSON file via URL parameter (EXAMPLE):
   ```
   report.html?data=python_report.json
   report.html?data=java_report.json
   report.html?data=custom_data.json
   report_enhanced.html?data=custom_data.json
   ```

**Template Description:**
- `report.html`: Basic template with basic test report display functionality
- `report_enhanced.html`: Enhanced template with rich interactive visualization features (recommended to use)

### JSON Data Structure Requirements

**Mandatory Fields:**

- `report_metadata`: Report metadata (author, AI model, language stack, timestamps (format: "YYYY-MM-DD HH:MM:SS"), statistics)
  - `total_analyzed_scenarios`: Total number of scenarios analyzed (from call chain analysis, one call chain often contains multiple scenarios)
  - `total_test_cases`: Total number of test cases to be executed (total number of test cases)
  - `total_http_endpoint`: Total number of HTTP endpoints (number of endpoints)
  - `passed_scenarios`: Number of passed scenarios (all test cases in scenario passed)
  - `failed_scenarios`: Number of failed scenarios (any test case in scenario failed)
  - `skipped_scenarios`: Number of skipped scenarios (scenario not executed)
  - `scenario_pass_rate`: Scenario pass rate (= passed scenarios / (passed scenarios + failed scenarios + skipped scenarios) × 100%)
  - `passed`: Number of passed test cases
  - `failed`: Number of failed test cases
  - `skipped`: Number of skipped test cases (means test execution did not run this test case, e.g., due to dependency failure or skip)
  - `pass_rate`: Pass rate (= passed / total test cases × 100%)
  - `total_exc_tests`: Number of executed test cases (= passed + failed, excludes skipped)
  - `total_exc_endpoint`: Number of tested endpoints (number of endpoints covered by test execution)
- `test_results`: Array of test results with detailed information (detailed information for each test case, including request parameters, response parameters, assertion details, etc.)
- `call_chains`: Array of API call chain visualizations (array of API call chain visualizations for each scenario)
  - Each chain must include `calls` array with detailed call information:
    - `method`: HTTP method (GET/POST/PUT/DELETE/PATCH)
    - `endpoint`: API endpoint path
    - `status_code`: HTTP status code
    - `request_headers`: Request headers object
    - `request_body`: Request body object
    - `response_headers`: Response headers object
    - `response_body`: Response body object
    - `execution_time`: Execution time in seconds
- `coverage_stats`: Coverage statistics (endpoint, scenario, call chain)
  - `endpoint_coverage`: Endpoint coverage (= endpoints_covered / endpoints_total × 100%)
  - `endpoints_covered`: Number of tested endpoints
  - `endpoints_total`: Total number of endpoints
  - `scenario_coverage`: Scenario coverage (= scenarios_covered / total_analyzed_scenarios × 100%)
  - `scenarios_covered`: Number of tested scenarios (one call chain often contains multiple scenarios)
  - `total_analyzed_scenarios`: Total number of analyzed scenarios
  - `call_chain_coverage`: Call chain coverage (= call_chains_covered / call_chains_total × 100%)
  - `call_chains_covered`: Number of tested call chains
  - `call_chains_total`: Total number of call chains (one call chain often contains multiple scenarios)
- `scenarios`: Scenario-based test groupings
  - Each scenario must include `tests` array with test results
  - `test_count`: Number of test cases in this scenario
  - `passed_count`: Number of passed tests in this scenario
  - `failed_count`: Number of failed tests in this scenario

**Complete Schema:**
See `report_data_schema.json` for complete JSON Schema definition with all field types and constraints.

### Language Stack Implementation Requirements

**Python (pytest):**

MUST generate JSON file with the following structure (EXAMPLE):

```json
{
  "report_metadata": {
    "author": "hailong.chen",
    "ai_model": "GLM-4.7",
    "language_stack": "Python 3.11+",
    "test_framework": "pytest",
    "generated_at": "2024-01-21 10:30:00",
    "total_analyzed_scenarios": 8,
    "total_test_cases": 6,
    "total_exc_tests": 5,
    "total_http_endpoint": 28,
    "total_exc_endpoint": 10,
    "passed": 4,
    "failed": 1,
    "skipped": 1,
    "pass_rate": 80.0,
    "total_execution_time": 45.23,
    "project_name": "freedom"
  },
  "test_results": [...],
  "call_chains": [
    {
      "chain_id": "user_registration",
      "chain_name": "用户注册流程",
      "endpoints": [
        "POST /auth/send-verify-code",
        "POST /auth/register",
        "POST /auth/token",
        "GET /auth/me"
      ],
      "description": "用户发送验证码、注册、登录并获取个人信息",
      "calls": [
        {
          "method": "POST",
          "endpoint": "/auth/send-verify-code",
          "status_code": 200,
          "request_headers": {},
          "request_body": {},
          "response_headers": {},
          "response_body": {},
          "execution_time": 0.38
        },
        ...
      ]
    }
  ],
  "coverage_stats": {
    "endpoint_coverage": 35.7,
    "total_exc_endpoint": 10,
    "total_http_endpoint": 28,
    "scenario_coverage": 62.5,
    "scenarios_covered": 5,
    "total_analyzed_scenarios": 8,
    "scenarios_passed": 4,
    "scenarios_failed": 1,
    "scenarios_skipped": 0,
    "scenario_pass_rate": 80.0,
    "call_chain_coverage": 62.5,
    "call_chains_covered": 5,
    "call_chains_total": 8
  },
  "scenarios": {
    "user_registration": {
      "chain_name": "用户注册流程",
      "description": "用户发送验证码、注册、登录并获取个人信息",
      "endpoints": [
        "POST /auth/send-verify-code",
        "POST /auth/register",
        "POST /auth/token",
        "GET /auth/me"
      ],
      "test_count": 2,
      "passed_count": 2,
      "failed_count": 0,
      "tests": [...]
    }
  }
}
```

**Java (TestNG):**

MUST generate JSON file with the same structure as Python, adjusting `language_stack` and `test_framework` fields accordingly (EXAMPLE).

**Node.js (Jest):**

MUST generate JSON file with the same structure as Python, adjusting `language_stack` and `test_framework` fields accordingly (EXAMPLE).

**Go (testing):**

MUST generate JSON file with the same structure as Python, adjusting `language_stack` and `test_framework` fields accordingly (EXAMPLE).

**Rust (cargo test):**

MUST generate JSON file with the same structure as Python, adjusting `language_stack` and `test_framework` fields accordingly (EXAMPLE).

### Optional Adapters

Optional adapters are provided for convenience:
- `python_adapter.py`: Python convenience functions
- `java_adapter.java`: Java convenience functions
- `nodejs_adapter.js`: Node.js convenience functions
- `go_adapter.go`: Go convenience functions

**Note**: Adapters are optional. You can generate JSON manually following the schema without using adapters.

### Report Generation Workflow

1. **Execute Tests**: Run tests using appropriate framework (pytest/TestNG/Jest/etc.)
2. **Generate JSON**: Convert test results to standard JSON format
3. **Copy Template and Assets (MANDATORY)**: **MUST copy** template file (report.html) and assets directory to reports directory - this is a mandatory step for report generation
4. **Save JSON**: Save JSON data as `report.json` in reports directory
   - Follow data file generation principles (one complete data file per session, full data file, non-incremental updates)
5. **Open Report**: Open `report.html` in browser to view interactive visualization

### Enhanced Report Requirements

**Three Report Files**: Must generate JSON, Markdown, and Web format reports simultaneously

**JSON Enhancement**: Must include scenario-based test counts, call chains, coverage rates, pass rates, assertion details, and project name

**Markdown Content**: Must include test file paths, call chain information, class method details, and input/output parameters

**Web Visualization**: 
- MUST implement interactive visualization using D3.js or similar libraries (no technical or environmental restrictions)
- Default priority: Use D3.js for web-based visualization
- Display all enhanced content with interactive features (search, filter, expand/collapse)
- Support viewing actual tested API full paths, request details, and response details
- Use template-based approach - template is language-agnostic pure HTML/CSS/JavaScript
- Template loads JSON data dynamically via JavaScript fetch API
- No backend processing required - template runs entirely in browser

**Content Incremental Updates**: Smart overwrite mode - same scenario test cases overwrite update while preserving history traces, with change highlighting and version traceability

**User Experience**: Appropriate styling, correct interactions, elegant visual design, responsive layout

**File Standards**: Report file paths and naming follow test framework default behavior

### Mandatory Enhanced Report Content (CRITICAL)

In addition to existing requirements, following 9 items MUST be verified and included:

1. **File Name**: Test case file name (NOT file name of object under test)
2. **Class and Method Name**: Test method identifier for traceability
3. **Test Result**: Clear indication of success/failure/skipped status
4. **Call Chain**: 
   - Must display complete scenario chain
   - Must support viewing actual tested API full paths
   - Must support viewing request details (method, URL, headers, body)
   - Must support viewing response details (status code, headers, body)
5. **Assertion Information Details**:
   - Status code assertions
   - Response body specific assertions (field-level validation)
   - Assertion type, expected value, actual value, result
6. **Individual Scenario Execution Time**: Execution duration for each scenario test case
7. **Total Test Execution Time**: Overall execution duration for all test cases
8. **Report Generation DateTime**: Timestamp when report was generated
9. **Project Name**: Project name (top-level directory name of project path)

All 9 items MUST be present in enhanced report (JSON/Markdown/Web formats).

### Automatic Fallback Strategy

Test report generation must never fail. If primary report generation method fails, automatic fallback strategies must be applied to ensure a report is always generated:

1. **Primary Method**: Template-based report (report.html + report.json)
   - **PREREQUISITE**: **MUST copy** template file (report.html) and assets directory to reports directory before attempting report generation
   - If successful: Use template-based report
   - If fails: Log error, inform user with detailed failure information, and fallback to secondary method

2. **Secondary Method**: Framework-specific HTML reporters (pytest-html, Jest HTML Reporter, etc.)
   - If available and successful: Use HTML reporters
   - If available but fails: Log error, inform user with detailed failure information, and fallback to tertiary method
   - If unavailable: Log error, inform user with detailed failure information, and fallback to tertiary method

3. **Tertiary Method**: Terminal & Console output with detailed summary
   - Always available: Must succeed
   - Provides comprehensive test execution summary
   - Includes all required information (test results, coverage, statistics)

### Fallback Implementation Requirements

- Each fallback attempt must be logged with detailed error information
- **CRITICAL: User Notification Requirement**: When report parsing or generation fails at any stage, MUST explicitly inform user with:
  - Detailed failure reason and error messages
  - Which report generation method failed
  - What fallback method is being used
  - **Prompt for automatic fix**: Inform user that they can request automatic fix for the failure
- Fallback must be automatic without user intervention for continuing report generation
- Final terminal & console output must always be generated regardless of report tool failures
- User can request automatic fix after reviewing the failure information

## Phase 6: Terminal & Console Summary Output (MANDATORY)

After test task completion, the following information MUST be output to terminal & console:

**Terminal & Console Summary Output Requirements:**
This is a mandatory final step to provide users with immediate visibility of test results and report location.

**Required Output Elements:**

1. **Test Report File Paths**
   - Output paths for all generated report formats
   - **CRITICAL: MUST include test framework's original report file paths** (e.g., pytest-html report, Allure report, Jest HTML report, etc.)
   - **Template-based report path**: report.html
   - **JSON data file path**: report.json
   - **Test Framework Default Report Locations** (relative to backend project root directory):
     - **Python (pytest)**:
       - HTML report: Default uses `--html` option to specify path, recommended `reports/http_testing_report.html`
       - Allure results: Default uses `--alluredir` option to specify path, recommended `allure-results/`
       - Allure report: Generated from Allure results, recommended `allure-report/`
       - Template report: Recommended `reports/report.html`
       - JSON data: Recommended `reports/report.json`
     - **Java (TestNG)**:
       - Default: `target/surefire-reports/`
       - Template report: Recommended `target/reports/report.html`
       - JSON data: Recommended `target/reports/report.json`
     - **Node.js (Jest)**:
       - Default: `coverage/` or custom output directory
       - Template report: Recommended `reports/report.html` or `__tests__/reports/report.html`
       - JSON data: Recommended `reports/report.json` or `__tests__/reports/report.json`
     - **Go (testing)**:
       - Default: Same directory as test files or custom directory
       - Template report: Recommended `reports/report.html`
       - JSON data: Recommended `reports/report.json`
     - **Rust (cargo test)**:
       - Default: `target/`
       - Template report: Recommended `target/reports/report.html`
       - JSON data: Recommended `target/reports/report.json`
   - For HTML reports: Provide file path
   - For Allure reports: Provide report path and startup command
   - For external report applications: Include application startup verification reminder
   - **For template reports**: Provide file path and opening instructions
   - Example:
     ```
     ========================================
     Test Report Generated
     ========================================
     Report Type: Template-based HTML Report (D3.js Visualization)
     
     Note: All paths below are relative to backend project root directory
     
     Template Report Path: {PROJECT_ROOT}/reports/report.html
     JSON Data Path: {PROJECT_ROOT}/reports/report.json
     
     Original Framework Report Path: {PROJECT_ROOT}/reports/http_testing_report.html
     
     To view report: Open reports/report.html in browser
     ========================================
     ```

2. **Expected Report Elements**
   - List all key elements that should be included in the report
   - Example:
     ```
     Report Contains Following Elements:
     ✓ Test execution summary
     ✓ Call chain (table header column)
     ✓ Assertion information (table header column)
     ✓ File name (test case file name)
     ✓ Class method name
     ✓ Input/output parameters
     ✓ Business value tracking
     ✓ Coverage statistics
     ✓ Performance metrics
     ✓ D3.js interactive visualization
     ✓ Search and filter functionality
     ✓ Template-based rendering (language-agnostic)
     ```

3. **Scenario Statistics**
   - Total number of scenarios (equals number of executed scenarios)
   - Number of passed scenarios (all test cases in scenario passed)
   - Number of failed scenarios (any test case in scenario failed)
   - Number of skipped scenarios (scenario not executed)
   - Example:
     ```
     Scenario Statistics:
     ----------------------------------------
     Total Scenarios: 8
     Passed Scenarios: 4
     Failed Scenarios: 1
     Skipped Scenarios: 0
     ----------------------------------------
     ```

4. **Pass Rate**
   - Calculate and display pass rate percentage
   - Example:
     ```
     Pass Rate:
     ----------------------------------------
     80.0% (4/5)
     ----------------------------------------
     ```

5. **Coverage Statistics**
   - Endpoint coverage (= tested endpoints / total endpoints × 100%)
   - Scenario coverage (= tested scenarios / total analyzed scenarios × 100%)
   - Call chain coverage (= tested call chains / total call chains × 100%)
   - Note: One call chain often contains multiple scenarios, therefore scenario count is typically greater than call chain count
   - Example:
     ```
     Coverage Statistics:
     ----------------------------------------
     Endpoint Coverage: 35.7% (10/28)
     Scenario Coverage: 62.5% (5/8)
     Call Chain Coverage: 62.5% (5/8)
     ----------------------------------------
     ```

**Complete Terminal & Console Output Example:**

```
========================================
Test Task Completed - Terminal & Console Summary
========================================

Test Report Generated
----------------------------------------
Report Type: Template-based HTML Report (D3.js Visualization)

Note: All paths below are relative to backend project root directory

Report Path: {PROJECT_ROOT}/reports/report.html
Startup Command: allure open {PROJECT_ROOT}/reports/allure-report

HTML Report Path: {PROJECT_ROOT}/reports/html_report.html
JSON Report Path: {PROJECT_ROOT}/reports/report.json
----------------------------------------

Note: For Allure reports, ensure Allure application is running. If not, start it using: allure serve <report-path>

Report Contains Following Elements:
✓ Test execution summary
✓ Call chain (table header column)
✓ Assertion information (table header column)
✓ File name (test case file name)
✓ Class method name
✓ Input/output parameters
✓ Business value tracking
✓ Coverage statistics
✓ Performance metrics
----------------------------------------

Scenario Statistics:
----------------------------------------
Total Scenarios: 8
Passed Scenarios: 4
Failed Scenarios: 1
Skipped Scenarios: 0
----------------------------------------

Scenario Pass Rate:
----------------------------------------
80.0% (4/5)
----------------------------------------

Coverage Statistics:
----------------------------------------
Endpoint Coverage: 35.7% (10/28)
Scenario Coverage: 87.5% (7/8)
Call Chain Coverage: 87.5% (7/8)
----------------------------------------

========================================
To view complete report, use the command above to open the report file
========================================
```

**Implementation Requirements:**
- Terminal & Console output MUST be generated after all report generation and validation steps complete
- All available report format paths MUST be output (HTML, Allure, JSON, etc.)
- For external report applications (Allure), include application startup verification reminder
- If report generation used fallback strategy, indicate which method was used and why
- **CRITICAL: Report Failure Notification**: When report parsing or generation fails at any stage, MUST output:
  - Clear failure notification with detailed error information
  - Which report generation method failed (template-based, HTML reporter, etc.)
  - Specific error messages and failure reasons
  - What fallback method is being used
  - **Prompt for automatic fix**: Explicitly inform user that they can request automatic fix for the failure
- Output format MUST be consistent across all language stacks (HTML, Allure, JSON, Terminal & Console)

## Summary

HTTP API Tester is a comprehensive testing framework that focuses on scenario-based testing of complete business workflows through API call chains. It provides automatic language detection, environment self-check, call chain analysis, enhanced report generation, and supports multiple programming languages.

### Key Updates and Improvements

- **Longest Dependency Chain**: Clarified that the maximum dependency chain refers to the **longest chain with actual dependencies**, not just the longest sequence of API calls
- **Test File Organization**: Added `testcases/atomic/` subdirectory for atomic layer tests, and implemented the **core business module principle** for naming test files
- **Core Business Module Principle**: Test files organized by core business module (determined by business purpose, final output, and business domain), especially when involving multiple modules
- **Document Structure Optimization**: Implemented progressive disclosure with:
  - **SKILL.md**: Core content and quick reference
  - **reference/ directory**: Detailed technical documentation
  - **SKILL-whole.md**: Complete backup file
- **Template and Assets Management**: Added detailed requirements for template files and assets directory, including mandatory copying to reports directory

### Core Testing Principles

- **Test Identity and Purpose**: Define who performs the test and what business behavior is validated
- **Response Body Assertions**: MUST validate response body field values, not just HTTP status codes
- **Scenario-Based Testing**: One call chain contains multiple scenarios, one scenario = one test case
- **Maximum Dependency Chain Coverage**: Test coverage must reach 100% for the longest dependency chain

### Enhanced Report Generation

- **Template-Based Approach**: Separate data from presentation using pure frontend templates
- **Multi-Format Support**: Generate JSON, Markdown, and Web format reports simultaneously
- **Interactive Visualization**: Use D3.js for web-based visualization with search/filter capabilities
- **Session-Based Reports**: Generate unified reports after complete test session, following one complete data file per session principle
- **Mandatory Report Elements**: Call chain and assertion information as table header columns, file name (test case file name), class method name, input/output parameters, and test results

### Test File Organization

- **Directory Structure**: `testcases/` for business modules/scenarios, `testcases/atomic/` for single API endpoint tests
- **File Naming**: Use `test_{core_module}.py` format for business layer tests, direct module name for atomic layer tests
- **Maximum Dependency Chain**: Create dedicated test file `test_max_dependency_chain.py` for the longest dependency chain

### Language Support

Supports Python, Java, Node.js, Go, and Rust with automatic framework selection based on detected language stack.

## Scenario vs. Endpoint Comparison

| Aspect       | Endpoint                     | Call Chain                                      | Scenario                                            |
| ------------ | ---------------------------- | ----------------------------------------------- | --------------------------------------------------- |
| Scope        | Single API operation         | Complete business workflow (multiple endpoints) | Specific business logic branch within call chain    |
| Example      | POST /auth/register          | User registration flow (4 endpoints)            | Successful registration, invalid code, expired code |
| Testing      | Unit-level integration       | End-to-end integration                          | Specific request-response path                      |
| Dependencies | None                         | Parameter dependencies between calls            | Defined inputs and expected outputs                 |
| Relationship | Building block of call chain | Contains multiple scenarios                     | One scenario = One test case                        |

## Quick Reference Table

| Aspect             | Description                                                            |
| ------------------ | ---------------------------------------------------------------------- |
| **技能名称**       | http-api-tester                                                        |
| **核心功能**       | 基于场景的HTTP API测试框架，支持调用链分析、参数依赖追踪、增强报告生成 |
| **测试原则**       | 场景化测试，核心业务模块命名，/atomic子目录结构                        |
| **支持语言**       | Python, Java, Node.js, Go, Rust                                        |
| **报告格式**       | JSON, Markdown, Web (D3.js可视化)                                      |
| **模板要求**       | 必须复制template和assets目录到reports目录                              |
| **测试数据前缀**   | AIT_/ait_ (非真实世界数据)                                             |
| **最大依赖链命名** | test_max_dependency_chain.py                                           |
| **执行顺序**       | 正常主流程 → 其他业务分支 → 异常流程                                   |
| **报告验证**       | 必须验证报告完整性和正确性                                             |
