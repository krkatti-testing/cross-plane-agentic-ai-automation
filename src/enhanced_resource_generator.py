#!/usr/bin/env python3
"""
Enhanced Crossplane Resource Generator
Integrates with LLM agent for intelligent resource generation
"""

import yaml
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from llm_agent import ResourceRequest, ResourceType

class EnhancedCrossplaneResourceGenerator:
    """Enhanced generator that works with LLM-parsed requests"""
    
    def __init__(self, output_dir: str = "generated"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def generate_from_request(self, request: ResourceRequest) -> Dict[str, Any]:
        """
        Generate Crossplane configurations from a ResourceRequest
        
        Args:
            request: Parsed resource request from LLM agent
            
        Returns:
            Dictionary of configuration objects
        """
        if request.resource_type == ResourceType.EKS_CLUSTER:
            return self._generate_eks_cluster(request)
        elif request.resource_type == ResourceType.S3_BUCKET:
            return self._generate_s3_bucket(request)
        elif request.resource_type == ResourceType.RDS_DATABASE:
            return self._generate_rds_database(request)
        elif request.resource_type == ResourceType.VPC:
            return self._generate_vpc(request)
        else:
            raise ValueError(f"Unsupported resource type: {request.resource_type}")
    
    def _generate_eks_cluster(self, request: ResourceRequest) -> Dict[str, Any]:
        """Generate EKS cluster configuration from request"""
        
        # Provider configuration
        provider_config = {
            "apiVersion": "aws.crossplane.io/v1beta1",
            "kind": "ProviderConfig",
            "metadata": {
                "name": f"{request.name}-provider-config",
                "labels": {
                    "environment": request.environment,
                    "managed-by": "crossplane-automation"
                }
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
        
        # Prepare tags
        tags = {
            "Environment": request.environment,
            "CreatedBy": "crossplane-automation",
            "CreatedAt": datetime.now().isoformat(),
            "Owner": "platform-team"
        }
        
        if request.tags:
            tags.update({k.replace("_", "-").title(): v for k, v in request.tags.items()})
        
        # EKS Cluster
        cluster = {
            "apiVersion": "eks.aws.crossplane.io/v1alpha1",
            "kind": "Cluster",
            "metadata": {
                "name": request.name,
                "labels": {
                    "environment": request.environment,
                    "region": request.region,
                    "managed-by": "crossplane-automation"
                },
                "annotations": {
                    "crossplane.io/external-name": request.name
                }
            },
            "spec": {
                "forProvider": {
                    "region": request.region,
                    "roleArn": f"arn:aws:iam::{{{{ .Values.awsAccountId }}}}:role/eks-cluster-role-{request.environment}",
                    "version": request.kubernetes_version or "1.28",
                    "resourcesVpcConfig": {
                        "securityGroupIds": [f"{{{{ .Values.{request.environment}.securityGroupId }}}}"],
                        "subnetIds": [
                            f"{{{{ .Values.{request.environment}.privateSubnet1Id }}}}",
                            f"{{{{ .Values.{request.environment}.privateSubnet2Id }}}}"
                        ],
                        "endpointConfigPrivateAccess": True,
                        "endpointConfigPublicAccess": request.environment != "production"
                    },
                    "encryptionConfig": {
                        "resources": ["secrets"],
                        "provider": {
                            "keyArn": f"{{{{ .Values.{request.environment}.kmsKeyArn }}}}"
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
                    "tags": tags
                },
                "providerConfigRef": {
                    "name": f"{request.name}-provider-config"
                }
            }
        }
        
        # Node Group configuration
        instance_types = request.instance_types or self._get_default_instance_types(request.environment)
        node_count = request.node_count or 3
        
        node_group = {
            "apiVersion": "eks.aws.crossplane.io/v1alpha1",
            "kind": "NodeGroup",
            "metadata": {
                "name": f"{request.name}-node-group",
                "labels": {
                    "environment": request.environment,
                    "cluster": request.name
                }
            },
            "spec": {
                "forProvider": {
                    "clusterName": request.name,
                    "nodeRole": f"arn:aws:iam::{{{{ .Values.awsAccountId }}}}:role/eks-node-group-role-{request.environment}",
                    "subnets": [
                        f"{{{{ .Values.{request.environment}.privateSubnet1Id }}}}",
                        f"{{{{ .Values.{request.environment}.privateSubnet2Id }}}}"
                    ],
                    "instanceTypes": instance_types,
                    "scalingConfig": {
                        "minSize": max(1, node_count - 1),
                        "maxSize": node_count * 2,
                        "desiredSize": node_count
                    },
                    "updateConfig": {
                        "maxUnavailable": 1 if node_count > 2 else 0,
                        "maxUnavailablePercentage": 25
                    },
                    "labels": {
                        "node.kubernetes.io/role": "application",
                        "environment": request.environment
                    },
                    "taints": [] if request.environment != "production" else [
                        {
                            "key": "node.kubernetes.io/production",
                            "value": "true",
                            "effect": "NoSchedule"
                        }
                    ],
                    "tags": {
                        "Environment": request.environment,
                        "Cluster": request.name,
                        "NodeGroup": f"{request.name}-node-group"
                    }
                },
                "providerConfigRef": {
                    "name": f"{request.name}-provider-config"
                }
            }
        }
        
        # Add addon configurations for production
        configurations = {
            "provider_config": provider_config,
            "cluster": cluster,
            "node_group": node_group
        }
        
        if request.environment == "production":
            configurations.update(self._generate_eks_addons(request))
        
        return configurations
    
    def _generate_s3_bucket(self, request: ResourceRequest) -> Dict[str, Any]:
        """Generate S3 bucket configuration from request"""
        
        # Prepare tags
        tags = {
            "Environment": request.environment,
            "CreatedBy": "crossplane-automation",
            "CreatedAt": datetime.now().isoformat()
        }
        
        if request.tags:
            tags.update({k.replace("_", "-").title(): v for k, v in request.tags.items()})
        
        bucket = {
            "apiVersion": "s3.aws.crossplane.io/v1beta1",
            "kind": "Bucket",
            "metadata": {
                "name": request.name,
                "labels": {
                    "environment": request.environment,
                    "region": request.region,
                    "managed-by": "crossplane-automation"
                }
            },
            "spec": {
                "forProvider": {
                    "region": request.region,
                    "acl": "private",
                    "versioningConfiguration": {
                        "status": "Enabled" if request.versioning != False else "Suspended"
                    },
                    "serverSideEncryptionConfiguration": {
                        "rules": [
                            {
                                "applyServerSideEncryptionByDefault": {
                                    "sseAlgorithm": "AES256" if not request.encryption else "aws:kms",
                                    "kmsMasterKeyID": f"{{{{ .Values.{request.environment}.kmsKeyArn }}}}" if request.encryption else None
                                },
                                "bucketKeyEnabled": True if request.encryption else False
                            }
                        ]
                    } if request.encryption != False else {},
                    "publicAccessBlockConfiguration": {
                        "blockPublicAcls": True,
                        "blockPublicPolicy": True,
                        "ignorePublicAcls": True,
                        "restrictPublicBuckets": True
                    },
                    "lifecycleConfiguration": {
                        "rules": [
                            {
                                "id": "DeleteIncompleteMultipartUploads",
                                "status": "Enabled",
                                "abortIncompleteMultipartUpload": {
                                    "daysAfterInitiation": 7
                                }
                            },
                            {
                                "id": "TransitionToIA",
                                "status": "Enabled",
                                "transitions": [
                                    {
                                        "days": 30,
                                        "storageClass": "STANDARD_IA"
                                    },
                                    {
                                        "days": 90,
                                        "storageClass": "GLACIER"
                                    }
                                ]
                            }
                        ]
                    },
                    "tags": tags
                },
                "providerConfigRef": {
                    "name": f"{request.name}-provider-config"
                }
            }
        }
        
        return {"bucket": bucket}
    
    def _generate_rds_database(self, request: ResourceRequest) -> Dict[str, Any]:
        """Generate RDS database configuration from request"""
        
        engine = request.engine or "mysql"
        instance_class = request.instance_class or self._get_default_db_instance_class(request.environment)
        allocated_storage = request.allocated_storage or 20
        
        # Prepare tags
        tags = {
            "Environment": request.environment,
            "CreatedBy": "crossplane-automation",
            "CreatedAt": datetime.now().isoformat(),
            "Engine": engine
        }
        
        if request.tags:
            tags.update({k.replace("_", "-").title(): v for k, v in request.tags.items()})
        
        database = {
            "apiVersion": "rds.aws.crossplane.io/v1alpha1",
            "kind": "RDSInstance",
            "metadata": {
                "name": request.name,
                "labels": {
                    "environment": request.environment,
                    "engine": engine,
                    "managed-by": "crossplane-automation"
                }
            },
            "spec": {
                "forProvider": {
                    "region": request.region,
                    "dbInstanceClass": instance_class,
                    "engine": engine,
                    "engineVersion": self._get_engine_version(engine),
                    "allocatedStorage": allocated_storage,
                    "storageType": "gp2",
                    "storageEncrypted": True,
                    "multiAZ": request.environment == "production",
                    "publiclyAccessible": False,
                    "vpcSecurityGroupIds": [
                        f"{{{{ .Values.{request.environment}.databaseSecurityGroupId }}}}"
                    ],
                    "dbSubnetGroupName": f"{{{{ .Values.{request.environment}.dbSubnetGroupName }}}}",
                    "backupRetentionPeriod": 7 if request.environment == "production" else 1,
                    "backupWindow": "03:00-04:00",
                    "maintenanceWindow": "sun:04:00-sun:05:00",
                    "autoMinorVersionUpgrade": request.environment != "production",
                    "deletionProtection": request.environment == "production",
                    "tags": tags
                },
                "providerConfigRef": {
                    "name": f"{request.name}-provider-config"
                },
                "writeConnectionSecretsToRef": {
                    "name": f"{request.name}-db-connection",
                    "namespace": "crossplane-system"
                }
            }
        }
        
        return {"database": database}
    
    def _generate_vpc(self, request: ResourceRequest) -> Dict[str, Any]:
        """Generate VPC configuration from request"""
        
        # This is a basic VPC setup - in practice, you'd want more sophisticated networking
        vpc = {
            "apiVersion": "ec2.aws.crossplane.io/v1beta1",
            "kind": "VPC",
            "metadata": {
                "name": request.name,
                "labels": {
                    "environment": request.environment,
                    "managed-by": "crossplane-automation"
                }
            },
            "spec": {
                "forProvider": {
                    "region": request.region,
                    "cidrBlock": "10.0.0.0/16",
                    "enableDnsHostnames": True,
                    "enableDnsSupport": True,
                    "tags": {
                        "Name": request.name,
                        "Environment": request.environment,
                        "CreatedBy": "crossplane-automation"
                    }
                },
                "providerConfigRef": {
                    "name": f"{request.name}-provider-config"
                }
            }
        }
        
        return {"vpc": vpc}
    
    def _generate_eks_addons(self, request: ResourceRequest) -> Dict[str, Any]:
        """Generate EKS addons for production clusters"""
        
        addons = {}
        
        # AWS Load Balancer Controller
        addons["aws_load_balancer_controller"] = {
            "apiVersion": "eks.aws.crossplane.io/v1alpha1",
            "kind": "Addon",
            "metadata": {
                "name": f"{request.name}-aws-load-balancer-controller"
            },
            "spec": {
                "forProvider": {
                    "clusterName": request.name,
                    "addonName": "aws-load-balancer-controller",
                    "addonVersion": "v1.6.2-eksbuild.1"
                }
            }
        }
        
        # EBS CSI Driver
        addons["ebs_csi_driver"] = {
            "apiVersion": "eks.aws.crossplane.io/v1alpha1",
            "kind": "Addon",
            "metadata": {
                "name": f"{request.name}-ebs-csi-driver"
            },
            "spec": {
                "forProvider": {
                    "clusterName": request.name,
                    "addonName": "aws-ebs-csi-driver",
                    "addonVersion": "v1.24.0-eksbuild.1"
                }
            }
        }
        
        return addons
    
    def _get_default_instance_types(self, environment: str) -> List[str]:
        """Get default instance types based on environment"""
        if environment == "production":
            return ["m6i.large", "m6i.xlarge", "m5.large", "m5.xlarge"]
        elif environment == "staging":
            return ["m6i.large", "m5.large", "t3.large"]
        else:
            return ["t3.medium", "t3.large"]
    
    def _get_default_db_instance_class(self, environment: str) -> str:
        """Get default database instance class based on environment"""
        if environment == "production":
            return "db.t3.medium"
        elif environment == "staging":
            return "db.t3.small"
        else:
            return "db.t3.micro"
    
    def _get_engine_version(self, engine: str) -> str:
        """Get default engine version"""
        versions = {
            "mysql": "8.0.35",
            "postgres": "15.4",
            "mariadb": "10.11.5"
        }
        return versions.get(engine, "8.0.35")
    
    def save_configurations_as_files(self, request: ResourceRequest, 
                                   configs: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Save configurations to YAML files and return file information for GitHub
        
        Args:
            request: The resource request
            configs: Configuration objects
            
        Returns:
            List of file dictionaries with 'path' and 'content' keys
        """
        files = []
        
        for config_name, config in configs.items():
            # Create filename
            filename = f"{request.name}-{config_name}.yaml"
            filepath = self.output_dir / filename
            
            # Convert to YAML
            yaml_content = yaml.dump(config, default_flow_style=False, sort_keys=False)
            
            # Add header comment
            header = f"""# Generated by Crossplane Automation
# Resource: {request.resource_type.value}
# Name: {request.name}
# Environment: {request.environment}
# Generated at: {datetime.now().isoformat()}
# Description: {request.description or 'No description provided'}

"""
            
            full_content = header + yaml_content
            
            # Save locally
            with open(filepath, 'w') as f:
                f.write(full_content)
            
            # Prepare for GitHub
            github_path = f"crossplane/{request.environment}/{filename}"
            files.append({
                "path": github_path,
                "content": full_content
            })
        
        return files
    
    def validate_request(self, request: ResourceRequest) -> List[str]:
        """
        Validate a resource request and return any issues
        
        Args:
            request: Resource request to validate
            
        Returns:
            List of validation issues (empty if valid)
        """
        issues = []
        
        # Name validation
        if not request.name or len(request.name) < 3:
            issues.append("Resource name must be at least 3 characters long")
        
        if not request.name.replace('-', '').replace('_', '').isalnum():
            issues.append("Resource name can only contain letters, numbers, hyphens, and underscores")
        
        # EKS specific validation
        if request.resource_type == ResourceType.EKS_CLUSTER:
            if request.node_count and request.node_count < 1:
                issues.append("Node count must be at least 1")
            
            if request.node_count and request.node_count > 20:
                issues.append("Node count should not exceed 20 without special consideration")
            
            if request.kubernetes_version:
                # Basic version format validation
                if not re.match(r'^\d+\.\d+(\.\d+)?$', request.kubernetes_version):
                    issues.append("Kubernetes version must be in format X.Y or X.Y.Z")
        
        # S3 specific validation
        elif request.resource_type == ResourceType.S3_BUCKET:
            # S3 bucket names have specific requirements
            if len(request.name) > 63:
                issues.append("S3 bucket name cannot exceed 63 characters")
            
            if not re.match(r'^[a-z0-9.-]+$', request.name):
                issues.append("S3 bucket name can only contain lowercase letters, numbers, dots, and hyphens")
        
        # RDS specific validation
        elif request.resource_type == ResourceType.RDS_DATABASE:
            if request.allocated_storage and request.allocated_storage < 20:
                issues.append("RDS allocated storage must be at least 20 GB")
            
            if request.engine and request.engine not in ['mysql', 'postgres', 'mariadb']:
                issues.append("Supported database engines: mysql, postgres, mariadb")
        
        return issues

# For backwards compatibility, create an alias
CrossplaneResourceGenerator = EnhancedCrossplaneResourceGenerator
