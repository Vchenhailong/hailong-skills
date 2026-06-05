# Test Design Reference

## Test Scenario Definition

### What is a Test Scenario?
A test scenario is a specific business logic branch of request and response, not a single HTTP endpoint. Each scenario represents a specific path through the call chain with defined inputs and expected outputs.

### Example Scenario
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

### Key Distinctions
- ❌ Scenario ≠ Single HTTP endpoint
- ❌ Scenario ≠ Complete call chain
- ✅ Scenario = Specific business logic branch
- ✅ One call chain often contains multiple scenarios
- ✅ One scenario = One test case

## API Endpoint Relationship Analysis

### Analysis Principles
- **Static + Dynamic Analysis**: In addition to static code analysis, consider data states, business states, and multi-role data exchanges
- **Generalized Implementation**: Use generalized approaches rather than hardcoding for parameter dependency analysis
- **State-Aware Analysis**: Consider how state changes (e.g., service status transitions) affect endpoint dependencies
- **Cross-Role Dependencies**: Analyze dependencies between different roles (e.g., user-initiated processes requiring admin approval)
- **Non-Hardcoded Data**: Avoid hardcoding non-static data in test analysis and implementation

### Non-Hardcoded Data Requirement
- ❌ **Prohibited**: Hardcoding non-static data in test code or reports
- ✅ **Recommended**: Use configuration files, environment variables, or data generation functions for dynamic data
- ✅ **Recommended**: Store test data in separate files
- ✅ **Recommended**: Use custom parameterization patterns for test cases with multiple data sets
- ❌ **Not Recommended**: Use test framework-provided parameterization patterns (e.g., pytest's @pytest.mark.parametrize)
- ✅ **Recommended**: Generate dynamic data at runtime for uniqueness (e.g., timestamps, UUIDs)
- ✅ **Recommended**: Read dynamic identifiers from API responses or database instead of hardcoding

### Steps for Analysis
1. **Endpoint Discovery and Documentation**
   - Discover and document all available endpoints
   - Organize endpoints by resource
   - Record endpoint descriptions, request bodies, and response bodies

2. **Dependency Analysis**
   - Analyze dependencies between endpoints
   - Identify parameter mappings
   - Record upstream to downstream dependencies
   - Consider data state and business state dependencies
   - Analyze multi-role data exchange dependencies

3. **Call Chain Generation**
   - Generate call chains for different business scenarios
   - Record detailed information for each step
   - Include parameter extraction and dependencies
   - Consider state transitions in call chain generation

4. **Mermaid Diagram Generation**
   - Generate visual representations of call chains
   - Use Mermaid syntax
   - Include parameter passing paths
   - Mark state transitions and role boundaries

5. **Multi-Role Analysis**
   - **Role Identification**: Identify all business roles in the system (e.g., user, admin, customer service)
   - **Role-Endpoint Mapping**: Create mapping tables for each role, clearly marking endpoint ownership
   - **Cross-Role Process Analysis**: Analyze complete cross-role business processes, covering from initiator to approver to notification receiver
   - **Role-Specific Call Chains**: Create dedicated call chain analyses for each cross-role business process
   - **Cross-Role Dependencies**: Identify state transitions and dependencies between cross-role operations
   - **Role-Specific Endpoint Configuration**: Configure role-specific endpoint identification rules in static analysis probe (e.g., `/admin/` prefix)
   - **Role Marking in Diagrams**: Clearly mark different role operations in call chain diagrams
   - **Role Coverage Validation**: Verify all roles have complete endpoint coverage, especially CRITICAL level admin endpoints

## Gap Detection Logic

### Coverage Gap Dimensions
1. **Longest Dependency Chain Coverage** (CRITICAL):
   - Complete coverage of the maximum dependency chain
   - Functional coverage of each node in the maximum dependency chain
   - Validation of dependencies between nodes in the maximum dependency chain
   - Data consistency validation in the maximum dependency chain
   - Static analysis probe validation of chain integrity

2. **Business Process Coverage**:
   - Call chain coverage: Ensure all call chains have corresponding tests
   - Scenario coverage: Verify all business scenarios are covered
   - Data consistency coverage: Complete process data consistency validation
   - Parameter validation coverage for each chain node
   - Error handling coverage for each chain node
   - Business return code coverage for each chain node

3. **General Coverage**:
   - Dependency coverage: Verify all parameter mappings are tested
   - Error scenario coverage: Verify error cases for all endpoints
   - Edge case coverage: Verify boundary value and edge case tests
   - Security scenario coverage: Verify authentication and authorization tests

### Gap Severity Levels
- **CRITICAL**:
  - Untested maximum dependency chain (longest chain with actual dependencies)
  - Critical nodes in the maximum dependency chain (POST/DELETE)
  - Untested call chains, critical endpoints (POST/DELETE)
- **HIGH**: Untested endpoints with high business impact, error scenarios, security scenarios
- **MEDIUM**: Untested dependencies, edge cases, boundary values
- **LOW**: Untested optional features or minor scenarios

## Test Case Design Principles

### Layered Design Pattern
- ✅ Adopt "atomic layer + business layer" layered design pattern
- ✅ Atomic layer cannot be used as test cases, instead it is organized and called by business layer
- ✅ Atomic layer code files are only called, not directly tested
- ✅ Must use the maximum dependency chain (longest chain with actual dependencies) as core test design basis
- ✅ Design complete business process tests based on call chain analysis
- ✅ Test case call paths follow call chains identified in API endpoint relationship analysis
- ✅ Each call chain from analysis must have corresponding test cases
- ✅ Maximum dependency chain test coverage must reach 100%
- ✅ Test cases must validate parameter dependencies identified in analysis
- ✅ Test execution order: Normal main flow first, then other business branch flows, finally exception flows
- ✅ Test execution order respects call sequence defined in analysis

### Test Case Metadata Requirements
- Test titles: Must be descriptive and clearly indicate what is being tested
- Test descriptions: Must explain test purpose, test data, and expected behavior
- Test titles and descriptions MUST be displayed in HTML report headers for all tests
- File name: Test case file name (NOT file name of object under test) must be captured and included in reports
- Class method name: Test method identifier must be captured and included in reports
- Input parameters: Request parameters sent to API endpoints must be recorded
- Output parameters: Response parameters received from API endpoints must be recorded
- Assertion information: Each assertion step in test case must be recorded in "assertion info" table column
- Metadata MUST be captured and included in generated reports