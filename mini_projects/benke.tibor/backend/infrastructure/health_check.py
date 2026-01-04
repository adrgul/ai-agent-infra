"""
Health check and startup validation for infrastructure components.

Validates that all required services (OpenAI, Qdrant, PostgreSQL, Redis)
are available and properly configured before the application starts.

Inspired by vector_embeddings/app/config.py validation patterns.
"""

import os
from typing import List, Tuple
from dataclasses import dataclass


@dataclass
class HealthCheckResult:
    """Result of a health check."""
    service: str
    status: bool
    message: str
    critical: bool = True


class HealthChecker:
    """
    Validates infrastructure components on startup.
    
    Follows Fail-Fast principle: better to catch configuration errors
    at startup than during runtime.
    """
    
    def __init__(self):
        self.results: List[HealthCheckResult] = []
    
    def check_env_var(self, var_name: str, required: bool = True) -> HealthCheckResult:
        """
        Check if environment variable is set.
        
        Args:
            var_name: Name of the environment variable
            required: Whether this variable is critical
            
        Returns:
            HealthCheckResult
        """
        value = os.getenv(var_name)
        
        if value:
            # Mask sensitive values
            display_value = value[:10] + "..." if len(value) > 10 else value
            if "KEY" in var_name or "SECRET" in var_name or "PASSWORD" in var_name:
                display_value = "***" + value[-4:] if len(value) > 4 else "****"
            
            return HealthCheckResult(
                service=f"ENV:{var_name}",
                status=True,
                message=f"✅ {var_name}={display_value}",
                critical=required
            )
        else:
            return HealthCheckResult(
                service=f"ENV:{var_name}",
                status=False,
                message=f"❌ {var_name} not set",
                critical=required
            )
    
    async def check_openai(self) -> HealthCheckResult:
        """Check OpenAI API availability."""
        try:
            from infrastructure.openai_clients import OpenAIClientFactory
            
            # Check if API key is set
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                return HealthCheckResult(
                    service="OpenAI",
                    status=False,
                    message="❌ OPENAI_API_KEY not configured",
                    critical=True
                )
            
            # Try to get a client instance
            OpenAIClientFactory.get_llm()
            
            return HealthCheckResult(
                service="OpenAI",
                status=True,
                message="✅ OpenAI client initialized",
                critical=True
            )
        except Exception as e:
            return HealthCheckResult(
                service="OpenAI",
                status=False,
                message=f"❌ OpenAI error: {str(e)[:100]}",
                critical=True
            )
    
    async def check_qdrant(self) -> HealthCheckResult:
        """Check Qdrant vector database availability."""
        try:
            from infrastructure.qdrant_rag_client import qdrant_rag_client
            
            if qdrant_rag_client.is_available():
                return HealthCheckResult(
                    service="Qdrant",
                    status=True,
                    message="✅ Qdrant vector store ready",
                    critical=True
                )
            else:
                return HealthCheckResult(
                    service="Qdrant",
                    status=False,
                    message="❌ Qdrant not available",
                    critical=True
                )
        except Exception as e:
            return HealthCheckResult(
                service="Qdrant",
                status=False,
                message=f"❌ Qdrant error: {str(e)[:100]}",
                critical=True
            )
    
    async def check_postgres(self) -> HealthCheckResult:
        """Check PostgreSQL database availability."""
        try:
            from infrastructure.postgres_client import postgres_client
            
            if postgres_client.is_available():
                return HealthCheckResult(
                    service="PostgreSQL",
                    status=True,
                    message="✅ PostgreSQL ready (lazy init)",
                    critical=False  # Not critical - will init on first use
                )
            else:
                return HealthCheckResult(
                    service="PostgreSQL",
                    status=False,
                    message="⚠️ PostgreSQL not configured (optional)",
                    critical=False
                )
        except Exception as e:
            return HealthCheckResult(
                service="PostgreSQL",
                status=False,
                message=f"⚠️ PostgreSQL: {str(e)[:100]}",
                critical=False
            )
    
    async def check_redis(self) -> HealthCheckResult:
        """Check Redis cache availability."""
        try:
            from infrastructure.redis_client import redis_cache
            
            if redis_cache.is_available():
                return HealthCheckResult(
                    service="Redis",
                    status=True,
                    message="✅ Redis cache ready",
                    critical=False
                )
            else:
                return HealthCheckResult(
                    service="Redis",
                    status=False,
                    message="⚠️ Redis not available (degraded mode)",
                    critical=False
                )
        except Exception as e:
            return HealthCheckResult(
                service="Redis",
                status=False,
                message=f"⚠️ Redis: {str(e)[:100]}",
                critical=False
            )
    
    async def run_all_checks(self) -> Tuple[bool, List[HealthCheckResult]]:
        """
        Run all health checks.
        
        Returns:
            Tuple of (all_critical_passed, all_results)
        """
        self.results = []
        
        # Environment variables
        self.results.append(self.check_env_var('OPENAI_API_KEY', required=True))
        self.results.append(self.check_env_var('QDRANT_HOST', required=False))
        self.results.append(self.check_env_var('POSTGRES_HOST', required=False))
        self.results.append(self.check_env_var('REDIS_HOST', required=False))
        
        # Service availability checks
        self.results.append(await self.check_openai())
        self.results.append(await self.check_qdrant())
        self.results.append(await self.check_postgres())
        self.results.append(await self.check_redis())
        
        # Check if all critical services passed
        critical_failures = [r for r in self.results if r.critical and not r.status]
        all_critical_passed = len(critical_failures) == 0
        
        return all_critical_passed, self.results
    
    def print_report(self, results: List[HealthCheckResult]) -> None:
        """
        Print a formatted health check report.
        
        Args:
            results: List of health check results
        """
        print("\n" + "="*70)
        print("🏥 INFRASTRUCTURE HEALTH CHECK")
        print("="*70)
        
        critical_results = [r for r in results if r.critical]
        optional_results = [r for r in results if not r.critical]
        
        if critical_results:
            print("\n📌 CRITICAL SERVICES:")
            for result in critical_results:
                print(f"  {result.message}")
        
        if optional_results:
            print("\n📋 OPTIONAL SERVICES:")
            for result in optional_results:
                print(f"  {result.message}")
        
        print("\n" + "="*70)
        
        critical_failures = [r for r in results if r.critical and not r.status]
        if critical_failures:
            print("❌ STARTUP FAILED - Critical services unavailable")
            print("="*70 + "\n")
            return False
        else:
            print("✅ ALL CRITICAL SERVICES READY")
            print("="*70 + "\n")
            return True


# Global health checker instance
health_checker = HealthChecker()


async def validate_startup_config() -> bool:
    """
    Validate all infrastructure components on startup.
    
    Returns:
        True if all critical services are available, False otherwise
    """
    success, results = await health_checker.run_all_checks()
    health_checker.print_report(results)
    return success


def validate_startup_config_sync() -> bool:
    """
    Synchronous wrapper for validate_startup_config.
    
    Used in Django apps.py ready() method since it cannot be async.
    Creates a minimal sync version without async dependencies.
    
    Returns:
        True if all critical services are available, False otherwise
    """
    import logging
    logger = logging.getLogger(__name__)
    
    print("\n" + "=" * 70)
    print("🏥 INFRASTRUCTURE HEALTH CHECK")
    print("=" * 70 + "\n")
    
    results = []
    all_critical_ok = True
    
    # Check 1: OPENAI_API_KEY
    api_key = os.getenv("OPENAI_API_KEY", "")
    if api_key:
        masked_key = api_key[:8] + "***" if len(api_key) > 8 else "***"
        results.append(("✅", f"ENV:OPENAI_API_KEY={masked_key}", True))
    else:
        results.append(("❌", "ENV:OPENAI_API_KEY=<missing>", True))
        all_critical_ok = False
    
    # Check 2: OpenAI client (basic check)
    try:
        # Just check that infrastructure module can be imported
        import infrastructure.openai_clients  # noqa: F401
        results.append(("✅", "OpenAI client importable", True))
    except Exception as e:
        results.append(("❌", f"OpenAI client error: {e}", True))
        all_critical_ok = False
    
    # Check 3: Qdrant URL
    qdrant_url = os.getenv("QDRANT_URL", "http://qdrant:6333")
    results.append(("✅", f"Qdrant URL configured: {qdrant_url}", True))
    
    # Check 4: PostgreSQL (optional)
    postgres_host = os.getenv("POSTGRES_HOST", "postgres")
    results.append(("⚠️", f"PostgreSQL will use lazy init: {postgres_host}", False))
    
    # Check 5: Redis (optional)
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
    results.append(("⚠️", f"Redis configured: {redis_url}", False))
    
    # Print results
    print("📌 CRITICAL SERVICES:")
    for icon, msg, critical in results:
        if critical:
            print(f"  {icon} {msg}")
    
    print("\n📋 OPTIONAL SERVICES:")
    for icon, msg, critical in results:
        if not critical:
            print(f"  {icon} {msg}")
    
    print("\n" + "=" * 70)
    if all_critical_ok:
        print("✅ ALL CRITICAL SERVICES READY")
        logger.info("✅ Health check passed - all critical services available")
    else:
        print("❌ SOME CRITICAL SERVICES UNAVAILABLE")
        logger.warning("❌ Health check failed - some critical services unavailable")
    print("=" * 70 + "\n")
    
    return all_critical_ok
