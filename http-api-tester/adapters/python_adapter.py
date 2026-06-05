"""
Python Report Adapter for HTTP API Tester
Provides convenience functions for generating standardized JSON report data from pytest results
"""

import json
from datetime import datetime
from typing import Dict, List, Any, Optional


class PythonReportAdapter:
    """Python pytest report adapter for generating standardized JSON"""

    def __init__(self, author: str = "hailong.chen", ai_model: str = "GLM-4.7"):
        self.author = author
        self.ai_model = ai_model

    def generate_report_data(
        self,
        test_results: List[Dict[str, Any]],
        call_chains: Optional[List[Dict[str, Any]]] = None,
        coverage_stats: Optional[Dict[str, Any]] = None,
        scenarios: Optional[Dict[str, Any]] = None,
        project_name: Optional[str] = None,
        total_analyzed_scenarios: int = 0,
        total_http_endpoint: int = 0,
    ) -> Dict[str, Any]:
        """
        Generate standardized JSON report data from pytest results

        Args:
            test_results: List of test result dictionaries
            call_chains: Optional list of call chain data
            coverage_stats: Optional coverage statistics
            scenarios: Optional scenario-based test groupings
            project_name: Optional project name (defaults to root directory name)
            total_analyzed_scenarios: Total number of scenarios analyzed
            total_http_endpoint: Total number of HTTP endpoints

        Returns:
            Dictionary containing standardized report data
        """
        if not test_results:
            test_results = []

        if not call_chains:
            call_chains = []

        if not coverage_stats:
            coverage_stats = {
                "endpoint_coverage": 0.0,
                "scenario_coverage": 0.0,
                "call_chain_coverage": 0.0,
                "endpoints_covered": 0,
                "endpoints_total": total_http_endpoint,
                "scenarios_covered": 0,
                "total_analyzed_scenarios": total_analyzed_scenarios,
                "call_chains_covered": len(call_chains),
                "call_chains_total": len(call_chains),
            }

        if not scenarios:
            scenarios = {}

        if not project_name:
            import os
            project_name = os.path.basename(os.getcwd())

        # Calculate basic test statistics
        total = len(test_results)
        passed = len([t for t in test_results if t.get("status") == "passed"])
        failed = len([t for t in test_results if t.get("status") == "failed"])
        skipped = len([t for t in test_results if t.get("status") == "skipped"])
        pass_rate = (passed / total * 100) if total > 0 else 0.0
        total_execution_time = sum(t.get("execution_time", 0) for t in test_results)
        total_exc_tests = passed + failed
        total_exc_endpoint = coverage_stats.get("endpoints_covered", 0)

        # Calculate scenario statistics
        passed_scenarios = 0
        failed_scenarios = 0
        skipped_scenarios = 0
        for scenario_name, scenario_data in scenarios.items():
            if isinstance(scenario_data, dict):
                if scenario_data.get("failed_count", 0) > 0:
                    failed_scenarios += 1
                elif scenario_data.get("passed_count", 0) > 0:
                    passed_scenarios += 1
                else:
                    skipped_scenarios += 1

        scenario_pass_rate = 0.0
        if (passed_scenarios + failed_scenarios + skipped_scenarios) > 0:
            scenario_pass_rate = (passed_scenarios / (passed_scenarios + failed_scenarios + skipped_scenarios)) * 100

        report_data = {
            "report_metadata": {
                "author": self.author,
                "ai_model": self.ai_model,
                "language_stack": "Python 3.11+",
                "test_framework": "pytest",
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_analyzed_scenarios": total_analyzed_scenarios,
                "total_test_cases": total,
                "total_http_endpoint": total_http_endpoint,
                "passed_scenarios": passed_scenarios,
                "failed_scenarios": failed_scenarios,
                "skipped_scenarios": skipped_scenarios,
                "scenario_pass_rate": round(scenario_pass_rate, 2),
                "passed": passed,
                "failed": failed,
                "skipped": skipped,
                "pass_rate": round(pass_rate, 2),
                "total_exc_tests": total_exc_tests,
                "total_exc_endpoint": total_exc_endpoint,
                "total_execution_time": round(total_execution_time, 3),
                "project_name": project_name,
            },
            "test_results": test_results,
            "call_chains": call_chains,
            "coverage_stats": coverage_stats,
            "scenarios": scenarios,
        }

        return report_data

    def save_report(self, report_data: Dict[str, Any], output_path: str) -> str:
        """
        Save report data to JSON file

        Args:
            report_data: Dictionary containing report data
            output_path: Path to save JSON file

        Returns:
            Path to saved JSON file
        """
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)

        return output_path

    def from_pytest_results(
        self,
        pytest_results: List[Dict[str, Any]],
        call_chains: Optional[List[Dict[str, Any]]] = None,
        coverage_stats: Optional[Dict[str, Any]] = None,
        scenarios: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Convert pytest results to standardized format

        Args:
            pytest_results: List of pytest test result dictionaries
            call_chains: Optional list of call chain data
            coverage_stats: Optional coverage statistics
            scenarios: Optional scenario-based test groupings

        Returns:
            Dictionary containing standardized report data
        """
        test_results = []
        total_analyzed_scenarios = 0
        total_http_endpoint = 0

        # Extract call chain information and endpoints
        endpoints = set()
        if call_chains:
            for chain in call_chains:
                for call in chain.get("calls", []):
                    endpoints.add(call.get("endpoint", ""))
            total_http_endpoint = len(endpoints)
        
        # Calculate total analyzed scenarios from scenarios data
        if scenarios:
            total_analyzed_scenarios = len(scenarios)

        for result in pytest_results:
            test_result = {
                "test_name": result.get(
                    "test_name", result.get("name", "Unknown Test")
                ),
                "test_description": result.get("test_description", ""),
                "file_name": result.get(
                    "file_name", result.get("filename", "unknown.py")
                ),
                "class_method_name": result.get(
                    "class_method_name", result.get("nodeid", "unknown")
                ),
                "status": result.get("status", "unknown").lower(),
                "execution_time": result.get(
                    "execution_time", result.get("duration", 0.0)
                ),
                "timestamp": result.get("timestamp", datetime.now().isoformat()),
                "call_chain": result.get("call_chain", ""),
                "assertion_info": result.get("assertion_info", []),
                "input_params": result.get("input_params", {}),
                "output_params": result.get("output_params", {}),
                "error_message": result.get("error_message", result.get("error", None)),
            }
            test_results.append(test_result)

        # Process scenarios to match new format
        processed_scenarios = {}
        if scenarios:
            for scenario_name, scenario_tests in scenarios.items():
                if isinstance(scenario_tests, list):
                    passed_count = len([t for t in scenario_tests if t.get("status") == "passed"])
                    failed_count = len([t for t in scenario_tests if t.get("status") == "failed"])
                    processed_scenarios[scenario_name] = {
                        "tests": scenario_tests,
                        "test_count": len(scenario_tests),
                        "passed_count": passed_count,
                        "failed_count": failed_count
                    }
                elif isinstance(scenario_tests, dict):
                    processed_scenarios[scenario_name] = scenario_tests

        return self.generate_report_data(
            test_results=test_results,
            call_chains=call_chains,
            coverage_stats=coverage_stats,
            scenarios=processed_scenarios,
            total_analyzed_scenarios=total_analyzed_scenarios,
            total_http_endpoint=total_http_endpoint,
        )


def create_sample_report() -> Dict[str, Any]:
    """
    Create a sample report for testing purposes

    Returns:
        Dictionary containing sample report data
    """
    current_time = datetime.now()
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
    iso_time = current_time.isoformat()
    
    # Calculate scenario-based statistics
    total_analyzed_scenarios = 2
    total_http_endpoint = 3
    
    sample_data = {
        "report_metadata": {
            "author": "hailong.chen",
            "ai_model": "GLM-4.7",
            "language_stack": "Python 3.11+",
            "test_framework": "pytest",
            "generated_at": formatted_time,
            "total_analyzed_scenarios": total_analyzed_scenarios,
            "total_test_cases": 3,
            "total_http_endpoint": total_http_endpoint,
            "passed_scenarios": 1,
            "failed_scenarios": 1,
            "skipped_scenarios": 0,
            "scenario_pass_rate": 50.0,
            "total_exc_tests": 3,
            "passed": 2,
            "failed": 1,
            "skipped": 0,
            "pass_rate": 66.67,
            "total_exc_endpoint": 3,
            "total_execution_time": 1.234,
            "project_name": "freedom",
        },
        "test_results": [
            {
                "test_name": "test_user_login",
                "test_description": "Test user login with valid credentials",
                "file_name": "test_auth.py",
                "class_method_name": "TestAuth.test_user_login",
                "status": "passed",
                "execution_time": 0.456,
                "timestamp": iso_time,
                "call_chain": "POST /api/auth/login → GET /api/user/profile",
                "assertion_info": [
                    {
                        "type": "status_code",
                        "expected": 200,
                        "actual": 200,
                        "result": "passed",
                    },
                    {
                        "type": "field_value",
                        "expected": "success",
                        "actual": "success",
                        "result": "passed",
                    },
                    {
                        "type": "field_value",
                        "expected": "AIT_test_user_001",
                        "actual": "AIT_test_user_001",
                        "result": "passed",
                    }
                ],
                "input_params": {
                    "username": "AIT_test_user_001",
                    "password": "password123",
                },
                "output_params": {"user_id": "12345", "username": "AIT_test_user_001"},
                "error_message": None,
            },
            {
                "test_name": "test_user_logout",
                "test_description": "Test user logout functionality",
                "file_name": "test_auth.py",
                "class_method_name": "TestAuth.test_user_logout",
                "status": "passed",
                "execution_time": 0.321,
                "timestamp": iso_time,
                "call_chain": "POST /api/auth/logout",
                "assertion_info": [
                    {
                        "type": "status_code",
                        "expected": 200,
                        "actual": 200,
                        "result": "passed",
                    },
                    {
                        "type": "field_value",
                        "expected": "success",
                        "actual": "success",
                        "result": "passed",
                    }
                ],
                "input_params": {
                    "user_id": "12345"
                },
                "output_params": {"message": "Logout successful"},
                "error_message": None,
            },
            {
                "test_name": "test_invalid_login",
                "test_description": "Test user login with invalid credentials",
                "file_name": "test_auth.py",
                "class_method_name": "TestAuth.test_invalid_login",
                "status": "failed",
                "execution_time": 0.457,
                "timestamp": iso_time,
                "call_chain": "POST /api/auth/login",
                "assertion_info": [
                    {
                        "type": "status_code",
                        "expected": 401,
                        "actual": 200,
                        "result": "failed",
                    },
                    {
                        "type": "field_value",
                        "expected": "error",
                        "actual": "success",
                        "result": "failed",
                    }
                ],
                "input_params": {
                    "username": "AIT_invalid_user_001",
                    "password": "wrongpassword",
                },
                "output_params": {"user_id": "99999", "username": "AIT_invalid_user_001"},
                "error_message": "Expected status code 401 but got 200, and expected result 'error' but got 'success'",
            },
        ],
        "call_chains": [
            {
                "chain_id": "user_authentication",
                "chain_name": "用户认证流程",
                "endpoints": [
                    "POST /api/auth/login",
                    "GET /api/user/profile",
                    "POST /api/auth/logout"
                ],
                "description": "用户登录、获取个人信息并登出的完整流程",
                "calls": [
                    {
                        "method": "POST",
                        "endpoint": "/api/auth/login",
                        "status_code": 200,
                        "execution_time": 0.456,
                        "request_headers": {"Content-Type": "application/json"},
                        "request_body": {
                            "username": "AIT_test_user_001",
                            "password": "password123",
                        },
                        "response_headers": {"Content-Type": "application/json"},
                        "response_body": {
                            "user_id": "12345",
                            "username": "AIT_test_user_001",
                            "status": "success"
                        },
                    },
                    {
                        "method": "GET",
                        "endpoint": "/api/user/profile",
                        "status_code": 200,
                        "execution_time": 0.234,
                        "request_headers": {"Authorization": "Bearer token123"},
                        "request_body": None,
                        "response_headers": {"Content-Type": "application/json"},
                        "response_body": {
                            "user_id": "12345",
                            "username": "AIT_test_user_001",
                            "email": "test@example.com",
                            "status": "success"
                        },
                    },
                    {
                        "method": "POST",
                        "endpoint": "/api/auth/logout",
                        "status_code": 200,
                        "execution_time": 0.321,
                        "request_headers": {"Authorization": "Bearer token123"},
                        "request_body": {"user_id": "12345"},
                        "response_headers": {"Content-Type": "application/json"},
                        "response_body": {
                            "message": "Logout successful",
                            "status": "success"
                        },
                    },
                ],
            },
            {
                "chain_id": "invalid_login",
                "chain_name": "无效登录流程",
                "endpoints": [
                    "POST /api/auth/login"
                ],
                "description": "使用无效凭据登录的失败流程",
                "calls": [
                    {
                        "method": "POST",
                        "endpoint": "/api/auth/login",
                        "status_code": 200,
                        "execution_time": 0.457,
                        "request_headers": {"Content-Type": "application/json"},
                        "request_body": {
                            "username": "AIT_invalid_user_001",
                            "password": "wrongpassword",
                        },
                        "response_headers": {"Content-Type": "application/json"},
                        "response_body": {
                            "user_id": "99999",
                            "username": "AIT_invalid_user_001",
                            "status": "success"
                        },
                    },
                ],
            }
        ],
        "coverage_stats": {
            "endpoint_coverage": 100.0,
            "endpoints_covered": 3,
            "endpoints_total": 3,
            "scenario_coverage": 100.0,
            "scenarios_covered": 2,
            "total_analyzed_scenarios": 2,
            "call_chain_coverage": 100.0,
            "call_chains_covered": 2,
            "call_chains_total": 2,
            "scenarios_passed": 1,
            "scenarios_failed": 1,
            "scenarios_skipped": 0,
            "scenario_pass_rate": 50.0,
        },
        "scenarios": {
            "User Authentication - Successful": {
                "chain_name": "用户认证流程 - 成功",
                "description": "用户使用有效凭据登录、获取个人信息并成功登出",
                "endpoints": [
                    "POST /api/auth/login",
                    "GET /api/user/profile",
                    "POST /api/auth/logout"
                ],
                "test_count": 2,
                "passed_count": 2,
                "failed_count": 0,
                "tests": [
                    {
                        "test_name": "test_user_login",
                        "test_description": "Test user login with valid credentials",
                        "file_name": "test_auth.py",
                        "class_method_name": "TestAuth.test_user_login",
                        "status": "passed",
                        "execution_time": 0.456,
                        "timestamp": iso_time,
                        "call_chain": "POST /api/auth/login → GET /api/user/profile",
                        "assertion_info": [
                            {
                                "type": "status_code",
                                "expected": 200,
                                "actual": 200,
                                "result": "passed",
                            },
                            {
                                "type": "field_value",
                                "expected": "success",
                                "actual": "success",
                                "result": "passed",
                            }
                        ],
                        "input_params": {"username": "AIT_test_user_001", "password": "password123"},
                        "output_params": {"user_id": "12345", "username": "AIT_test_user_001"},
                        "error_message": None,
                    },
                    {
                        "test_name": "test_user_logout",
                        "test_description": "Test user logout functionality",
                        "file_name": "test_auth.py",
                        "class_method_name": "TestAuth.test_user_logout",
                        "status": "passed",
                        "execution_time": 0.321,
                        "timestamp": iso_time,
                        "call_chain": "POST /api/auth/logout",
                        "assertion_info": [
                            {
                                "type": "status_code",
                                "expected": 200,
                                "actual": 200,
                                "result": "passed",
                            }
                        ],
                        "input_params": {"user_id": "12345"},
                        "output_params": {"message": "Logout successful"},
                        "error_message": None,
                    }
                ]
            },
            "User Authentication - Failed": {
                "chain_name": "用户认证流程 - 失败",
                "description": "用户使用无效凭据登录，预期应该失败",
                "endpoints": [
                    "POST /api/auth/login"
                ],
                "test_count": 1,
                "passed_count": 0,
                "failed_count": 1,
                "tests": [
                    {
                        "test_name": "test_invalid_login",
                        "test_description": "Test user login with invalid credentials",
                        "file_name": "test_auth.py",
                        "class_method_name": "TestAuth.test_invalid_login",
                        "status": "failed",
                        "execution_time": 0.457,
                        "timestamp": iso_time,
                        "call_chain": "POST /api/auth/login",
                        "assertion_info": [
                            {
                                "type": "status_code",
                                "expected": 401,
                                "actual": 200,
                                "result": "failed",
                            }
                        ],
                        "input_params": {"username": "AIT_invalid_user_001", "password": "wrongpassword"},
                        "output_params": {"user_id": "99999", "username": "AIT_invalid_user_001"},
                        "error_message": "Expected status code 401 but got 200",
                    }
                ]
            }
        },
    }

    return sample_data


if __name__ == "__main__":
    import sys

    adapter = PythonReportAdapter()

    if len(sys.argv) > 1:
        action = sys.argv[1]

        if action == "sample":
            sample_data = create_sample_report()
            print(json.dumps(sample_data, indent=2, ensure_ascii=False))
        elif action == "help":
            print("Usage: python python_adapter.py [sample|help]")
            print("  sample  - Generate sample report data")
            print("  help    - Show this help message")
        else:
            print(f"Unknown action: {action}")
            print("Use 'help' for usage information")
    else:
        print("Usage: python python_adapter.py [sample|help]")
        print("Use 'help' for usage information")
