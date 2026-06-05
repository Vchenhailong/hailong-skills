# Language Stack Support Reference

## Automatic Language Detection

### Priority Language Detection
The skill automatically detects the project's programming language stack when invoked, prioritizing backend languages for API testing.

### Detection Methods
- ✅ **Feature File Analysis**: Checks for language-specific configuration files
  - `pyproject.toml` or `requirements.txt` → Python
  - `pom.xml` or `build.gradle` → Java
  - `package.json` → Node.js
  - `go.mod` → Go
  - `Cargo.toml` → Rust
- ✅ **Project Structure Analysis**: Analyzes directory structure and file extensions
- ✅ **Backend Language Priority**: Prioritizes backend languages for API testing
- ✅ **Mixed Language Handling**: Automatically selects backend language in mixed projects

## Supported Language Stacks

### Python Stack (pytest)
- **Required Dependencies**:
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

- **Execution Commands**:
  - Run all tests: `pytest tests/ -v`
  - Run specific scenario: `pytest tests/ -m scenario_user_registration`
  - Generate HTML report: `pytest tests/ --html=reports/http_testing_report.html`
  - Generate Allure report: `pytest tests/ --alluredir=reports/allure-results`

### Java Stack (TestNG)
- **Required Dependencies**:
  - Java 8+ (Java 11+ recommended)
  - TestNG >= 7.0.0
  - REST Assured >= 5.0.0
  - Allure TestNG >= 2.13.0
  - JUnit >= 5.0.0
  - Maven/Gradle (build tool)
  - Allure (command-line tool) - Optional but recommended

- **Execution Commands**:
  - Run all tests: `mvn test` or `gradle test`
  - Generate Allure report: `mvn allure:report` or `gradle allureReport`

### Node.js Stack (Jest)
- **Required Dependencies**:
  - Node.js 14+ (Node.js 16+ recommended)
  - Jest >= 27.0.0
  - @types/jest >= 27.0.0
  - supertest >= 6.0.0
  - axios >= 1.0.0
  - jest-html-reporters >= 3.0.0
  - allure-jest >= 2.0.0
  - Allure (command-line tool) - Optional but recommended

- **Execution Commands**:
  - Run all tests: `jest`
  - Run specific test: `jest tests/test_order.js`
  - Generate HTML report: `jest --reporters=jest-html-reporters`
  - Generate Allure report: `jest --reporters=jest-allure`

### Go Stack (testing)
- **Required Dependencies**:
  - Go 1.18+ (Go 1.20+ recommended)
  - gotestsum >= 1.8.0
  - go-junit-report >= 2.0.0
  - Allure Go >= 2.0.0
  - Allure (command-line tool) - Optional but recommended

- **Execution Commands**:
  - Run all tests: `go test ./...`
  - Run specific tag: `go test -tags=auth ./...`
  - Generate JUnit report: `go test ./... | go-junit-report > reports/junit-report.xml`

### Rust Stack (cargo test)
- **Required Dependencies**:
  - Rust 1.65+ (Rust 1.70+ recommended)
  - cargo2junit >= 0.4.0
  - Allure Rust >= 0.1.0
  - Allure (command-line tool) - Optional but recommended

- **Execution Commands**:
  - Run all tests: `cargo test`
  - Run specific test: `cargo test auth`
  - Generate JUnit report: `cargo test -- --nocapture | cargo2junit > reports/junit-report.xml`

## Framework Configuration Examples

### Python pytest Configuration
```ini
# pytest.ini
[pytest]
markers =
    scenario_user_registration: User registration flow tests
    scenario_order_creation: Order creation flow tests
```

### Java TestNG Configuration
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

### Node.js Jest Configuration
```javascript
// jest.config.js
module.exports = {
    testMatch: [
        '**/tests/**/*.test.js',
        '**/tests/**/*.spec.js'
    ]
};
```

### Go Testing Configuration
```go
//go:build auth
// +build auth

package auth_test

func TestLogin(t *testing.T) {
    // Test implementation
}
```

### Rust Test Configuration
```rust
#[cfg(test)]
mod auth_tests {
    use super::*;

    #[test]
    fn test_login() {
        // Test implementation
    }
}
```

## Environment Self-Check

### Automatic Environment Validation
The skill includes a comprehensive environment self-check and installation system that automatically verifies all required dependencies before running tests.

### Color-Coded Status Indicators
- ✅ **Green**: Dependency is installed and available
- 🟡 **Orange**: Dependency is missing but can be auto-installed
- 🔴 **Red**: Dependency is required but cannot be auto-installed (manual intervention needed)

### Priority Installation
Uses language-specific package managers:
- Python: uv/pip
- Java: Maven/Gradle
- Node.js: npm/yarn
- Go: go mod
- Rust: cargo