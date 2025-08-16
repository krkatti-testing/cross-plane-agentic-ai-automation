# Example Natural Language Requests

This document shows examples of natural language requests that the Crossplane Agentic Automation System can understand and process.

## EKS Cluster Examples

### Basic Development Cluster
```
"Create an EKS cluster called my-dev-cluster for development"
```
**Generated**: Basic development cluster with 3 t3.medium nodes

### Production Cluster with Specific Requirements
```
"Create a production EKS cluster called data-platform in us-west-2 with 5 nodes using m6i.large instances"
```
**Generated**: Production cluster with security features, monitoring, and addons

### Cluster with Version Specification
```
"I need a Kubernetes 1.27 cluster named analytics-cluster for staging with 4 nodes"
```
**Generated**: Staging cluster with specified Kubernetes version

## S3 Bucket Examples

### Basic Secure Bucket
```
"I need a secure S3 bucket for storing customer data"
```
**Generated**: Encrypted bucket with versioning and public access blocking

### Backup Bucket
```
"Create an S3 bucket called backup-storage for production with versioning enabled"
```
**Generated**: Production bucket with lifecycle policies and encryption

### Data Lake Bucket
```
"Set up an S3 bucket for our data lake in us-east-1 with encryption"
```
**Generated**: Optimized bucket configuration for data lake use case

## RDS Database Examples

### Application Database
```
"Set up a MySQL database for our application"
```
**Generated**: MySQL database with appropriate sizing for development

### Production Database
```
"Create a production PostgreSQL database called user-db with high availability"
```
**Generated**: Multi-AZ PostgreSQL with automated backups and monitoring

### Development Database
```
"I need a small MySQL database for testing called test-db"
```
**Generated**: Small development database with minimal resources

## Complex Multi-Resource Requests

### Complete Application Stack
```
"Set up a complete stack for my web application: an EKS cluster, MySQL database, and S3 bucket for assets"
```
**Generated**: Multiple coordinated resources with proper networking

### Analytics Platform
```
"Create an analytics platform with EKS cluster for processing and S3 for data storage in us-west-2"
```
**Generated**: Coordinated analytics infrastructure

## Environment-Specific Examples

### Development Environment
```
"Create development infrastructure: small EKS cluster and MySQL database"
```
**Features**:
- Cost-optimized instance types
- Single AZ deployment
- Basic security settings
- Minimal monitoring

### Staging Environment
```
"Set up staging environment with EKS cluster and PostgreSQL database for testing"
```
**Features**:
- Mid-tier instance types
- Single AZ with some redundancy
- Enhanced security
- Basic monitoring

### Production Environment
```
"Deploy production infrastructure: highly available EKS cluster with 5 nodes and encrypted database"
```
**Features**:
- High-performance instances
- Multi-AZ deployment
- Full security features
- Comprehensive monitoring
- Automated backups

## Advanced Configuration Examples

### Security-Focused Request
```
"Create a highly secure EKS cluster for financial data processing with encryption and private networking"
```
**Generated Features**:
- Private cluster endpoints
- KMS encryption everywhere
- Restrictive security groups
- Audit logging enabled
- Network policies

### High-Performance Request
```
"Set up a high-performance EKS cluster for machine learning workloads with GPU nodes"
```
**Generated Features**:
- GPU-enabled instance types
- High-bandwidth networking
- Optimized storage classes
- Resource quotas

### Cost-Optimized Request
```
"Create a cost-effective development environment with minimal resources"
```
**Generated Features**:
- Spot instances where appropriate
- Minimal node counts
- Basic storage tiers
- Limited retention periods

## Tips for Better Requests

### Be Specific About Requirements
❌ **Vague**: "Create a cluster"
✅ **Better**: "Create an EKS cluster called my-app-cluster for production with 3 nodes"

### Mention Environment
❌ **Missing Context**: "Set up a database"
✅ **Better**: "Set up a MySQL database for development testing"

### Include Security Requirements
❌ **Basic**: "Create an S3 bucket"
✅ **Better**: "Create a secure S3 bucket with encryption for customer data"

### Specify Regions When Needed
❌ **Default**: "Create a cluster"
✅ **Better**: "Create a cluster in eu-west-1 for European users"

## Request Parsing Features

The system understands:

- **Resource Types**: EKS, S3, RDS, VPC, cluster, bucket, database
- **Environments**: development, dev, staging, stage, production, prod
- **Regions**: All AWS regions (us-east-1, eu-west-1, ap-southeast-1, etc.)
- **Sizes**: small, medium, large, or specific instance types
- **Security**: secure, encrypted, private, public
- **Availability**: highly available, multi-az, redundant
- **Performance**: high-performance, fast, optimized

## What Gets Generated

For each request, the system generates:

1. **Provider Configuration**: AWS credentials and region setup
2. **Resource Definitions**: Main resource (cluster, bucket, database)
3. **Supporting Resources**: Security groups, IAM roles, networking
4. **Environment-Specific Settings**: Sizing, security, monitoring based on environment
5. **Best Practices**: Security, tagging, naming conventions
6. **Documentation**: Comments and descriptions in YAML files

## GitHub PR Content

Each generated PR includes:

- **Detailed Description**: What was requested and what was generated
- **Review Checklist**: Items to verify before approval
- **Security Considerations**: Security features and requirements
- **Cost Implications**: Estimated costs and resource usage
- **Deployment Notes**: How to deploy and monitor the resources

## Next Steps After PR Creation

1. **Review** the generated configurations
2. **Test** in a development environment first
3. **Customize** any specific requirements
4. **Approve** and merge when ready
5. **Monitor** the Crossplane deployment
