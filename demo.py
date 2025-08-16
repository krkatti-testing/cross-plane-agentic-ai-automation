#!/usr/bin/env python3
"""
Demo script for Crossplane Agentic Automation System
Shows how the system works without requiring actual API keys
"""

import os
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import only what we need for the demo (avoid OpenAI dependency)
try:
    from llm_agent import ResourceRequest, ResourceType
    from enhanced_resource_generator import EnhancedCrossplaneResourceGenerator
    IMPORTS_OK = True
except ImportError as e:
    print(f"⚠️  Some imports failed: {e}")
    print("This is expected in demo mode without all dependencies installed.")
    IMPORTS_OK = False
    
    # Mock the classes we need
    from enum import Enum
    from dataclasses import dataclass
    from typing import Optional, Dict, List
    
    class ResourceType(Enum):
        EKS_CLUSTER = "eks_cluster"
        S3_BUCKET = "s3_bucket"
        RDS_DATABASE = "rds_database"
        VPC = "vpc"
    
    @dataclass
    class ResourceRequest:
        resource_type: ResourceType
        name: str
        region: str = "us-east-1"
        environment: str = "development"
        node_count: Optional[int] = None
        kubernetes_version: Optional[str] = None
        instance_types: Optional[List[str]] = None
        versioning: Optional[bool] = None
        encryption: Optional[bool] = None
        engine: Optional[str] = None
        instance_class: Optional[str] = None
        allocated_storage: Optional[int] = None
        tags: Optional[Dict[str, str]] = None
        description: Optional[str] = None

def demo_llm_parsing():
    """Demo the LLM parsing functionality (mock mode)"""
    print("🧠 LLM Parsing Demo")
    print("=" * 50)
    
    test_requests = [
        "Create an EKS cluster called analytics-cluster for production in us-west-2 with 5 nodes",
        "I need a secure S3 bucket for storing customer data",
        "Set up a MySQL database for our application",
        "Create a development environment with a small cluster and database"
    ]
    
    for i, request in enumerate(test_requests, 1):
        print(f"\n{i}. Request: '{request}'")
        
        # Mock parsing (since we don't have real API keys)
        if "cluster" in request.lower():
            mock_request = ResourceRequest(
                resource_type=ResourceType.EKS_CLUSTER,
                name="analytics-cluster",
                region="us-west-2",
                environment="production",
                node_count=5,
                kubernetes_version="1.28",
                tags={"purpose": "analytics", "team": "data"},
                description="Production EKS cluster for analytics workloads"
            )
        elif "bucket" in request.lower():
            mock_request = ResourceRequest(
                resource_type=ResourceType.S3_BUCKET,
                name="customer-data-bucket",
                region="us-east-1",
                environment="development",
                versioning=True,
                encryption=True,
                tags={"data-classification": "sensitive"},
                description="Secure S3 bucket for customer data storage"
            )
        elif "database" in request.lower():
            mock_request = ResourceRequest(
                resource_type=ResourceType.RDS_DATABASE,
                name="app-database",
                region="us-east-1",
                environment="development",
                engine="mysql",
                instance_class="db.t3.micro",
                tags={"purpose": "application"},
                description="MySQL database for application"
            )
        else:
            mock_request = ResourceRequest(
                resource_type=ResourceType.EKS_CLUSTER,
                name="dev-cluster",
                region="us-east-1",
                environment="development",
                node_count=2,
                kubernetes_version="1.28",
                description="Development cluster"
            )
        
        print(f"   ✅ Parsed as: {mock_request.resource_type.value}")
        print(f"   📛 Name: {mock_request.name}")
        print(f"   🌍 Region: {mock_request.region}")
        print(f"   🏷️  Environment: {mock_request.environment}")
        
        if mock_request.node_count:
            print(f"   🔢 Node Count: {mock_request.node_count}")
        if mock_request.engine:
            print(f"   ⚙️  Engine: {mock_request.engine}")
        if mock_request.encryption:
            print(f"   🔒 Encryption: Enabled")

def demo_resource_generation():
    """Demo the resource generation functionality"""
    print("\n\n⚙️  Resource Generation Demo")
    print("=" * 50)
    
    if not IMPORTS_OK:
        print("   ⚠️  Skipping actual resource generation (dependencies not installed)")
        print("   📋 In real mode, this would:")
        print("      - Validate the resource request")
        print("      - Generate Crossplane YAML configurations")
        print("      - Save files with proper structure and naming")
        print("      - Include environment-specific optimizations")
        return
    
    generator = EnhancedCrossplaneResourceGenerator("demo_output")
    
    # Demo EKS cluster generation
    print("\n🔧 Generating EKS Cluster Configuration...")
    
    cluster_request = ResourceRequest(
        resource_type=ResourceType.EKS_CLUSTER,
        name="demo-cluster",
        region="us-west-2",
        environment="production",
        node_count=3,
        kubernetes_version="1.28",
        tags={"purpose": "demo", "team": "platform"},
        description="Demo production EKS cluster"
    )
    
    # Validate request
    issues = generator.validate_request(cluster_request)
    if issues:
        print(f"   ❌ Validation issues: {issues}")
    else:
        print("   ✅ Request validation passed")
    
    # Generate configurations
    configs = generator.generate_from_request(cluster_request)
    print(f"   ✅ Generated {len(configs)} configuration objects:")
    
    for config_name, config in configs.items():
        print(f"      - {config_name}: {config['kind']}")
    
    # Save as files
    files = generator.save_configurations_as_files(cluster_request, configs)
    print(f"   ✅ Saved {len(files)} files:")
    
    for file_info in files:
        print(f"      - {file_info['path']}")
        
    # Show a sample configuration
    print("\n📄 Sample Configuration (provider_config):")
    print("-" * 30)
    sample_config = configs['provider_config']
    print(f"apiVersion: {sample_config['apiVersion']}")
    print(f"kind: {sample_config['kind']}")
    print(f"metadata:")
    print(f"  name: {sample_config['metadata']['name']}")
    print(f"  labels:")
    for k, v in sample_config['metadata']['labels'].items():
        print(f"    {k}: {v}")

def demo_github_integration():
    """Demo the GitHub integration (mock mode)"""
    print("\n\n🚀 GitHub Integration Demo")
    print("=" * 50)
    
    print("📝 This would create a GitHub Pull Request with:")
    print("   - New feature branch: eks-cluster-production-20240101-120000")
    print("   - Committed files:")
    print("     * crossplane/production/demo-cluster-provider-config.yaml")
    print("     * crossplane/production/demo-cluster-cluster.yaml")
    print("     * crossplane/production/demo-cluster-node-group.yaml")
    print("     * crossplane/production/demo-cluster-aws-load-balancer-controller.yaml")
    print("     * crossplane/production/demo-cluster-ebs-csi-driver.yaml")
    print("   - PR Title: 'Add EKS Cluster: demo-cluster'")
    print("   - Detailed description with review checklist")
    print("   - URL: https://github.com/your-org/infrastructure/pull/123")
    
    print("\n📋 PR Description would include:")
    print("   - Resource type and configuration summary")
    print("   - Environment-specific settings")
    print("   - Security considerations")
    print("   - Review checklist")
    print("   - Deployment instructions")

def demo_complete_workflow():
    """Demo the complete workflow"""
    print("\n\n🤖 Complete Workflow Demo")
    print("=" * 50)
    
    user_request = "Create a production EKS cluster called platform-cluster in eu-west-1 with 4 nodes"
    
    print(f"📝 User Request: '{user_request}'")
    print("\n🔄 Workflow Steps:")
    
    print("   1. 🧠 LLM parses natural language request")
    print("      ✅ Identified: EKS cluster, production, eu-west-1, 4 nodes")
    
    print("   2. 🔍 System validates the request")
    print("      ✅ All parameters valid, no issues found")
    
    print("   3. 💡 AI generates enhancement suggestions")
    print("      💡 Consider adding cost-center tags for billing")
    print("      💡 Ensure backup and disaster recovery plans")
    
    print("   4. ⚙️  Generate Crossplane configurations")
    print("      ✅ Created 5 YAML files with production settings")
    
    print("   5. 📁 Prepare files for GitHub")
    print("      ✅ Files organized in crossplane/production/ directory")
    
    print("   6. 🚀 Create GitHub Pull Request")
    print("      ✅ Branch: eks-cluster-production-20240101-120000")
    print("      ✅ PR #123: Add EKS Cluster: platform-cluster")
    print("      ✅ URL: https://github.com/your-org/infrastructure/pull/123")
    
    print("\n🎉 Workflow Complete!")
    print("   👀 Review the PR at the provided URL")
    print("   ✅ Approve and merge when ready")
    print("   📊 Monitor Crossplane for deployment status")

def main():
    """Run the complete demo"""
    print("🤖 Crossplane Agentic Automation System - DEMO")
    print("=" * 60)
    print("This demo shows how the system works without requiring API keys")
    print("=" * 60)
    
    demo_llm_parsing()
    demo_resource_generation()
    demo_github_integration()
    demo_complete_workflow()
    
    print("\n\n" + "=" * 60)
    print("🎓 Demo Complete!")
    print("=" * 60)
    print("To use the real system:")
    print("1. Set up your API keys (OpenAI, GitHub)")
    print("2. Run: python src/agentic_workflow.py --interactive")
    print("3. Start making natural language requests!")
    print("\nFor more information, see README.md")

if __name__ == "__main__":
    main()
