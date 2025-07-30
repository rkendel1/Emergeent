#!/usr/bin/env python3
"""
Simple validation script for the migration
Tests basic functionality without external dependencies
"""
import subprocess
import sys
import json

def run_command(cmd, description):
    """Run a command and return success status"""
    try:
        print(f"🔍 {description}...")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - SUCCESS")
            return True, result.stdout
        else:
            print(f"❌ {description} - FAILED")
            print(f"Error: {result.stderr}")
            return False, result.stderr
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False, str(e)

def test_postgresql():
    """Test PostgreSQL connection and basic operations"""
    print("\n=== PostgreSQL Tests ===")
    
    # Test connection
    success, output = run_command(
        'PGPASSWORD=password psql -h localhost -p 5432 -U username -d test_database -c "SELECT version();"',
        "PostgreSQL connection"
    )
    if not success:
        return False
    
    # Test table creation (should already exist)
    success, output = run_command(
        'PGPASSWORD=password psql -h localhost -p 5432 -U username -d test_database -c "\\dt"',
        "Table verification"
    )
    if not success:
        return False
    
    # Test data insertion
    success, output = run_command(
        '''PGPASSWORD=password psql -h localhost -p 5432 -U username -d test_database -c "
        INSERT INTO user_profiles (id, name, background, experience, interests, skills) 
        VALUES ('test-migration-123', 'Migration Test User', 'Testing migration', 
                '[\\\"Migration testing\\\"]', '[\\\"PostgreSQL\\\"]', '[\\\"Python\\\", \\\"Docker\\\"]')
        ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name;"''',
        "Data insertion test"
    )
    if not success:
        return False
    
    # Test data retrieval
    success, output = run_command(
        'PGPASSWORD=password psql -h localhost -p 5432 -U username -d test_database -c "SELECT name FROM user_profiles WHERE id = \'test-migration-123\';"',
        "Data retrieval test"
    )
    if not success:
        return False
    
    print("✅ PostgreSQL migration validation complete!")
    return True

def test_docker():
    """Test Docker setup"""
    print("\n=== Docker Tests ===")
    
    # Test Docker is available
    success, output = run_command("docker --version", "Docker availability")
    if not success:
        return False
    
    # Test Docker Compose is available
    success, output = run_command("docker compose version", "Docker Compose availability")
    if not success:
        return False
    
    # Test PostgreSQL container is running
    success, output = run_command("docker compose ps postgres", "PostgreSQL container status")
    if not success:
        return False
    
    if "Up" not in output:
        print("❌ PostgreSQL container is not running")
        return False
    
    print("✅ Docker setup validation complete!")
    return True

def test_file_structure():
    """Test that all required files exist"""
    print("\n=== File Structure Tests ===")
    
    required_files = [
        "backend/database.py",
        "backend/groq_client.py", 
        "backend/server.py",
        "backend/Dockerfile",
        "backend/.env",
        "frontend/Dockerfile",
        "frontend/.env",
        "docker-compose.yml",
        "MIGRATION_GUIDE.md"
    ]
    
    all_exist = True
    for file_path in required_files:
        success, _ = run_command(f"test -f {file_path}", f"File exists: {file_path}")
        if not success:
            all_exist = False
    
    if all_exist:
        print("✅ All required files present!")
    
    return all_exist

def main():
    """Run all validation tests"""
    print("🚀 Starting Migration Validation")
    print("=" * 50)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Docker Setup", test_docker),
        ("PostgreSQL Database", test_postgresql),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with error: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name}: {status}")
        if success:
            passed += 1
    
    print("-" * 50)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All validation tests passed! Migration is successful.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)