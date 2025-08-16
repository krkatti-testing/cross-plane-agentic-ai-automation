# 🤖 Crossplane Agentic Automation System

An intelligent, LLM-powered system for automated infrastructure provisioning using Crossplane. This system takes natural language requests from users, generates appropriate Crossplane configurations, and creates GitHub pull requests for review and deployment.

## ✨ Features

- **🧠 Natural Language Processing**: Uses OpenAI GPT models to parse infrastructure requests in plain English
- **⚙️ Intelligent Resource Generation**: Automatically generates production-ready Crossplane YAML configurations
- **🔄 Automated PR Workflow**: Creates GitHub branches, commits files, and opens pull requests automatically
- **🎯 Environment-Aware**: Generates different configurations based on environment (dev, staging, production)
- **🔍 Validation & Suggestions**: Validates requests and provides enhancement suggestions
- **🌐 Multi-Resource Support**: Supports EKS clusters, S3 buckets, RDS databases, and VPCs

## 🏗️ Architecture

```
User Request (Natural Language)
           ↓
    LLM Agent (OpenAI)
           ↓
  Resource Request Parser
           ↓
Enhanced Resource Generator
           ↓
   Crossplane YAML Files
           ↓
   GitHub Integration
           ↓
   Automated Pull Request
```

## 🚀 Quick Start

### Prerequisites

1. **OpenAI API Key**: Get one from [OpenAI Platform](https://platform.openai.com/)
2. **GitHub Personal Access Token**: Create one with repo permissions
3. **Python 3.8+**: Make sure you have Python installed

### Installation

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd crossplane-automation
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   export OPENAI_API_KEY="sk-your-openai-api-key"
   export GITHUB_TOKEN="ghp_your-github-token"
   export GITHUB_REPO_OWNER="your-github-username"
   export GITHUB_REPO_NAME="your-infrastructure-repo"
   ```

### Usage Examples

#### Interactive Mode
```bash
python src/agentic_workflow.py --interactive
```

Then type requests like:
- `"Create an EKS cluster called analytics-cluster for production with 5 nodes"`
- `"I need a secure S3 bucket for storing customer data"`
- `"Set up a MySQL database for our application"`

#### Single Request Mode
```bash
python src/agentic_workflow.py --request "Create an EKS cluster for production in us-west-2"
```

#### Generate Without PR
```bash
python src/agentic_workflow.py --request "Create a development EKS cluster" --no-pr
```

## 📋 Supported Resources

### EKS Clusters
- **Features**: Multi-AZ deployment, security groups, node groups, addons
- **Environments**: Development (t3 instances), Staging (mixed), Production (m6i instances)
- **Security**: KMS encryption, private endpoints, proper IAM roles

### S3 Buckets
- **Features**: Versioning, encryption, lifecycle policies, public access blocking
- **Security**: KMS encryption, bucket policies, access logging
- **Compliance**: Follows AWS security best practices

### RDS Databases
- **Engines**: MySQL, PostgreSQL, MariaDB
- **Features**: Multi-AZ (production), automated backups, encryption
- **Security**: VPC deployment, security groups, connection secrets

### VPC Networks
- **Features**: Custom CIDR blocks, DNS settings, proper tagging
- **Integration**: Works with other resources for complete networking

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for LLM | Yes |
| `GITHUB_TOKEN` | GitHub personal access token | Yes |
| `GITHUB_REPO_OWNER` | GitHub repository owner/org | Yes |
| `GITHUB_REPO_NAME` | GitHub repository name | Yes |

### Command Line Options

```bash
python src/agentic_workflow.py --help
```

## 📁 Project Structure

```
crossplane-automation/
├── src/
│   ├── agentic_workflow.py          # Main orchestrator
│   ├── llm_agent.py                 # LLM integration
│   ├── enhanced_resource_generator.py # Resource generation
│   ├── github_integration.py        # GitHub API integration
│   └── resource_request.py          # Legacy CLI tool
├── configs/                         # Configuration templates
├── examples/                        # Example configurations
├── docs/                           # Documentation
├── requirements.txt                # Python dependencies
└── README.md                       # This file
```

## 🎯 How It Works

1. **Natural Language Parsing**: The LLM agent analyzes your request and extracts:
   - Resource type (EKS, S3, RDS, VPC)
   - Resource name and environment
   - Specific parameters (node count, instance types, etc.)
   - Security requirements

2. **Intelligent Generation**: The enhanced resource generator creates:
   - Production-ready Crossplane YAML files
   - Environment-appropriate configurations
   - Security best practices
   - Proper resource relationships

3. **Automated PR Creation**: The GitHub integration:
   - Creates a new feature branch
   - Commits all generated files
   - Opens a detailed pull request
   - Includes review checklists and documentation

## 🔍 Example Workflow

**User Input**: `"Create a production EKS cluster called data-platform in us-west-2 with 5 nodes"`

**System Actions**:
1. 🧠 **Parse**: Identifies EKS cluster, production environment, specific region and node count
2. ⚙️ **Generate**: Creates provider config, cluster definition, node group, and production addons
3. 📁 **Prepare**: Saves files with proper naming and structure
4. 🚀 **Deploy**: Creates PR with detailed description and review checklist

**Generated Files**:
```
crossplane/production/
├── data-platform-provider-config.yaml
├── data-platform-cluster.yaml
├── data-platform-node-group.yaml
├── data-platform-aws-load-balancer-controller.yaml
└── data-platform-ebs-csi-driver.yaml
```

## 🛡️ Security Features

- **KMS Encryption**: All resources use KMS encryption where applicable
- **Private Networking**: Production resources deploy in private subnets
- **IAM Best Practices**: Uses least-privilege IAM roles
- **Security Groups**: Restrictive security group configurations
- **Secrets Management**: Database credentials stored in Kubernetes secrets

## 🔄 Integration with Crossplane

This system generates standard Crossplane configurations that work with:
- **AWS Provider**: Requires AWS Provider to be installed in your cluster
- **Helm Provider**: For additional Kubernetes applications
- **Kubernetes Provider**: For in-cluster resource management

## 🧪 Testing

Run the test suite:
```bash
pytest tests/ -v
```

Test individual components:
```bash
python src/llm_agent.py          # Test LLM parsing
python src/github_integration.py # Test GitHub API (requires tokens)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Troubleshooting

### Common Issues

**"Invalid GitHub token"**
- Ensure your token has `repo` permissions
- Check that the token hasn't expired

**"LLM parsing failed"**
- Verify your OpenAI API key is correct
- Check your API quota and billing settings

**"Repository not found"**
- Ensure the repository exists and you have access
- Check the repository owner and name are correct

### Getting Help

1. Check the [Issues](../../issues) page for known problems
2. Create a new issue with detailed error information
3. Include your request and any error messages

## 🚀 Roadmap

- [ ] Support for more AWS services (Lambda, API Gateway, etc.)
- [ ] Azure and GCP provider support
- [ ] Terraform integration
- [ ] Web UI interface
- [ ] Slack/Teams bot integration
- [ ] Cost estimation before deployment
- [ ] Resource dependency visualization
