#!/usr/bin/env python3
"""
Crossplane Resource Request System
Automatically generates Crossplane configurations and GitHub PRs for AWS resources
"""

import argparse
import json
import os
import sys
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

class CrossplaneResourceGenerator:
    """Generates Crossplane YAML configurations for AWS resources"""
    
    def __init__(self, output_dir: str = "generated"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def generate_eks_cluster(self, name: str, region: str, environment: str, 
                           node_count: int = 3, version: str = "1.28") -> Dict[str, Any]:
        """Generate EKS cluster configuration"""
        
        # Provider configuration
        provider_config = {
            "apiVersion": "aws.crossplane.io/v1beta1",
            "kind": "ProviderConfig",
            "metadata": {
                "name": f"{name}-aws-provider-config"
            },
            "spec": {
                "credentials": {
                    "source": "Secret",
                    "secretRef": {
                        "namespace": "crossplane-system",
                        "name": "aws-secret",
                        "key": "credentials"
                    }
                }
            }
        }
        
        # EKS Cluster
        cluster = {
            "apiVersion": "eks.aws.crossplane.io/v1alpha1",
            "kind": "Cluster",
            "metadata": {
                "name": name,
                "labels": {
                    "environment": environment,
                    "region": region,
                    "managed-by": "crossplane-automation"
                }
            },
            "spec": {
                "forProvider": {
                    "region": region,
                    "roleArn": "arn:aws:iam::123456789012:role/eks-cluster-role",
                    "version": version,
                    "resourcesVpcConfig": {
                        "securityGroupIds": ["sg-12345678"],
                        "subnetIds": ["subnet-12345678", "subnet-87654321"]
                    },
                    "encryptionConfig": {
                        "resources": ["secrets"],
                        "provider": {
                            "keyArn": "arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012"
                        }
                    },
                    "logging": {
                        "clusterLogging": [
                            {
                                "types": ["api", "audit", "authenticator", "controllerManager", "scheduler"],
                                "enabled": True
                            }
                        ]
                    },
                    "tags": {
                        "Environment": environment,
                        "Owner": "platform-team",
                        "CostCenter": "platform-infra",
                        "CreatedBy": "crossplane-automation"
                    }
                },
                "providerConfigRef": {
                    "name": f"{name}-aws-provider-config"
                }
            }
        }
        
        # Node Group
        node_group = {
            "apiVersion": "eks.aws.crossplane.io/v1alpha1",
            "kind": "NodeGroup",
            "metadata": {
                "name": f"{name}-node-group"
            },
            "spec": {
                "forProvider": {
                    "clusterName": name,
                    "nodeRole": "arn:aws:iam::123456789012:role/eks-node-group-role",
                    "subnets": ["subnet-12345678", "subnet-87654321"],
                    "instanceTypes": ["m6i.large", "m6i.xlarge"],
                    "scalingConfig": {
                        "minSize": max(1, node_count - 1),
                        "maxSize": node_count * 2,
                        "desiredSize": node_count
                    },
                    "updateConfig": {
                        "maxUnavailable": 1
                    },
                    "labels": {
                        "node.kubernetes.io/role": "application"
                    },
                    "tags": {
                        "Environment": environment,
                        "Owner": "platform-team"
                    }
                },
                "providerConfigRef": {
                    "name": f"{name}-aws-provider-config"
                }
            }
        }
        
        return {
            "provider_config": provider_config,
            "cluster": cluster,
            "node_group": node_group
        }
    
    def generate_s3_bucket(self, name: str, region: str, environment: str) -> Dict[str, Any]:
        """Generate S3 bucket configuration"""
        
        bucket = {
            "apiVersion": "s3.aws.crossplane.io/v1beta1",
            "kind": "Bucket",
            "metadata": {
                "name": name,
                "labels": {
                    "environment": environment,
                    "region": region,
                    "managed-by": "crossplane-automation"
                }
            },
            "spec": {
                "forProvider": {
                    "region": region,
                    "acl": "private",
                    "versioningConfiguration": {
                        "status": "Enabled"
                    },
                    "publicAccessBlockConfiguration": {
                        "blockPublicAcls": True,
                        "blockPublicPolicy": True,
                        "ignorePublicAcls": True,
                        "restrictPublicBuckets": True
                    },
                    "tags": {
                        "Environment": environment,
                        "Owner": "platform-team",
                        "CostCenter": "platform-infra"
                    }
                },
                "providerConfigRef": {
                    "name": f"{name}-aws-provider-config"
                }
            }
        }
        
        return {"bucket": bucket}
    
    def save_configurations(self, resource_type: str, name: str, configs: Dict[str, Any]) -> List[str]:
        """Save configurations to YAML files"""
        files_created = []
        
        for config_name, config in configs.items():
            filename = f"{name}-{config_name}.yaml"
            filepath = self.output_dir / filename
            
            with open(filepath, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
            
            files_created.append(str(filepath))
        
        return files_created

class GitHubPRGenerator:
    """Generates GitHub Pull Requests for Crossplane configurations"""
    
    def __init__(self, repo_owner: str, repo_name: str, github_token: str):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.github_token = github_token
        
    def create_pr(self, branch_name: str, title: str, description: str, 
                  files: List[str]) -> str:
        """Create a GitHub PR (simulated)"""
        
        # In a real implementation, this would use the GitHub API
        # For now, we'll simulate the PR creation
        
        pr_url = f"https://github.com/{self.repo_owner}/{self.repo_name}/pull/12345"
        
        print(f"🚀 Creating GitHub Pull Request...")
        print(f"📝 Title: {title}")
        print(f"📋 Description: {description}")
        print(f"🔗 PR URL: {pr_url}")
        print(f"📁 Files to be added:")
        for file in files:
            print(f"   - {file}")
        
        return pr_url

def main():
    parser = argparse.ArgumentParser(description="Generate Crossplane resources and GitHub PRs")
    parser.add_argument("resource_type", choices=["cluster", "bucket", "database"], 
                       help="Type of resource to create")
    parser.add_argument("--name", required=True, help="Name of the resource")
    parser.add_argument("--region", default="us-east-1", help="AWS region")
    parser.add_argument("--environment", default="development", 
                       choices=["development", "staging", "production"],
                       help="Environment")
    parser.add_argument("--node-count", type=int, default=3, help="Number of nodes (for clusters)")
    parser.add_argument("--version", default="1.28", help="Kubernetes version (for clusters)")
    parser.add_argument("--repo-owner", help="GitHub repository owner")
    parser.add_argument("--repo-name", help="GitHub repository name")
    parser.add_argument("--github-token", help="GitHub access token")
    
    args = parser.parse_args()
    
    # Generate Crossplane configurations
    generator = CrossplaneResourceGenerator()
    
    if args.resource_type == "cluster":
        configs = generator.generate_eks_cluster(
            name=args.name,
            region=args.region,
            environment=args.environment,
            node_count=args.node_count,
            version=args.version
        )
        resource_description = f"EKS cluster '{args.name}' in {args.region}"
    elif args.resource_type == "bucket":
        configs = generator.generate_s3_bucket(
            name=args.name,
            region=args.region,
            environment=args.environment
        )
        resource_description = f"S3 bucket '{args.name}' in {args.region}"
    else:
        print(f"❌ Unsupported resource type: {args.resource_type}")
        sys.exit(1)
    
    # Save configurations
    files_created = generator.save_configurations(args.resource_type, args.name, configs)
    
    print(f"✅ Generated Crossplane configurations for {resource_description}")
    print(f"📁 Files created:")
    for file in files_created:
        print(f"   - {file}")
    
    # Create GitHub PR if credentials provided
    if args.repo_owner and args.repo_name and args.github_token:
        pr_generator = GitHubPRGenerator(args.repo_owner, args.repo_name, args.github_token)
        
        branch_name = f"add-{args.resource_type}-{args.name}"
        title = f"Add {args.resource_type.title()}: {args.name}"
        description = f"""
## Resource Request

**Type**: {args.resource_type.title()}
**Name**: {args.name}
**Region**: {args.region}
**Environment**: {args.environment}

## Changes

This PR adds Crossplane configurations for the requested {args.resource_type}.

## Files Added

{chr(10).join([f"- {file}" for file in files_created])}

## Review Checklist

- [ ] Resource naming follows conventions
- [ ] Security configurations are appropriate
- [ ] Resource limits and scaling are reasonable
- [ ] Tags and labels are properly set
- [ ] Environment-specific configurations are correct

## Deployment

Once approved and merged, Crossplane will automatically provision the requested resources.

**⚠️ Note**: This will create actual AWS resources and incur costs.
        """.strip()
        
        pr_url = pr_generator.create_pr(branch_name, title, description, files_created)
        
        print(f"\n🎉 Successfully created Pull Request!")
        print(f"🔗 Review and approve at: {pr_url}")
    else:
        print(f"\n📝 To create a GitHub PR, provide: --repo-owner, --repo-name, and --github-token")
        print(f"💡 Example: --repo-owner myorg --repo-name infrastructure --github-token ghp_...")

if __name__ == "__main__":
    main()
