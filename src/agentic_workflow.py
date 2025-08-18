#!/usr/bin/env python3
"""
Agentic Workflow for Crossplane Automation
Main conversational interface that integrates LLM, resource generation, and GitHub PR creation
"""

import os
import sys
import argparse
from typing import Optional, Dict, Any
from pathlib import Path

from .llm_agent import LLMAgent, ResourceRequest, ResourceType, LLMParsingError
from .enhanced_resource_generator import EnhancedCrossplaneResourceGenerator
from .github_integration import GitHubIntegration, GitHubAPIError

class CrossplaneAgenticWorkflow:
    """Main workflow orchestrator for automated infrastructure provisioning"""
    
    def __init__(self, openai_api_key: str, github_token: str, 
                 repo_owner: str, repo_name: str, llm_model: str = "gpt-5"):
        """
        Initialize the agentic workflow
        
        Args:
            openai_api_key: OpenAI API key for LLM
            github_token: GitHub personal access token
            repo_owner: GitHub repository owner
            repo_name: GitHub repository name
            llm_model: LLM model to use
        """
        self.llm_agent = LLMAgent(openai_api_key, llm_model)
        self.resource_generator = EnhancedCrossplaneResourceGenerator()
        self.github = GitHubIntegration(github_token, repo_owner, repo_name)
        
        print(f"🤖 Crossplane Agentic Workflow initialized")
        print(f"   LLM Model: {llm_model}")
        print(f"   Repository: {repo_owner}/{repo_name}")
        print("=" * 60)
    
    def run_workflow(self, user_input: str, workflow_id: str = None) -> Dict[str, Any]:
        """
        Run the complete workflow with status tracking
        
        Args:
            user_input: Natural language description of infrastructure needs
            workflow_id: Optional workflow ID for tracking
            
        Returns:
            Dictionary with processing results
        """
        return self.process_request(user_input, auto_create_pr=True)
    
    def _update_workflow_status(self, workflow_id: str, status: str, message: str, stage: str = None, paused: bool = False):
        """
        Update workflow status (placeholder for web integration)
        
        Args:
            workflow_id: Workflow identifier
            status: Current status
            message: Status message
            stage: Current stage
            paused: Whether workflow is paused
        """
        # This is a placeholder - in the web app, this would update the global workflow_status dict
        pass
    
    def process_request(self, user_input: str, auto_create_pr: bool = True) -> Dict[str, Any]:
        """
        Process a natural language infrastructure request
        
        Args:
            user_input: Natural language description of infrastructure needs
            auto_create_pr: Whether to automatically create a PR
            
        Returns:
            Dictionary with processing results
        """
        print(f"📝 Processing request: {user_input}")
        print("-" * 40)
        
        try:
            # Step 1: Parse the request using LLM
            print("🧠 Step 1: Parsing request with LLM...")
            try:
                request = self.llm_agent.parse_request(user_input)
            except LLMParsingError as e:
                print(f"   ❌ LLM parsing failed: {e}")
                return {"status": "error", "message": f"LLM parsing failed: {e}", "paused": True, "stage": "llm_parsing"}
            
            print(f"   ✅ Parsed as: {request.resource_type.value}")
            print(f"   📛 Name: {request.name}")
            print(f"   🌍 Region: {request.region}")
            print(f"   🏷️  Environment: {request.environment}")
            
            if request.node_count:
                print(f"   🔢 Node Count: {request.node_count}")
            if request.kubernetes_version:
                print(f"   ⚙️  Kubernetes Version: {request.kubernetes_version}")
            
            # Step 2: Validate the request
            print("\n🔍 Step 2: Validating request...")
            validation_issues = self.resource_generator.validate_request(request)
            
            if validation_issues:
                print("   ❌ Validation issues found:")
                for issue in validation_issues:
                    print(f"      - {issue}")
                return {"status": "error", "issues": validation_issues}
            
            print("   ✅ Request validation passed")
            
            # Step 3: Generate suggestions
            print("\n💡 Step 3: Generating enhancement suggestions...")
            suggestions = self.llm_agent.generate_enhancement_suggestions(request)
            
            if suggestions:
                print("   💡 Suggestions:")
                for suggestion in suggestions:
                    print(f"      - {suggestion}")
            else:
                print("   ✅ No additional suggestions")
            
            # Step 4: Generate Crossplane configurations
            print("\n⚙️  Step 4: Generating Crossplane configurations...")
            configs = self.resource_generator.generate_from_request(request)
            
            print(f"   ✅ Generated {len(configs)} configuration objects:")
            for config_name in configs.keys():
                print(f"      - {config_name}")
            
            # Step 5: Prepare files for GitHub
            print("\n📁 Step 5: Preparing files...")
            files = self.resource_generator.save_configurations_as_files(request, configs)
            
            print(f"   ✅ Prepared {len(files)} files:")
            for file_info in files:
                print(f"      - {file_info['path']}")
            
            result = {
                "status": "success",
                "request": request,
                "suggestions": suggestions,
                "configs": configs,
                "files": files
            }
            
            # Step 6: Create GitHub PR if requested
            if auto_create_pr:
                print("\n🚀 Step 6: Creating GitHub Pull Request...")
                pr_info = self._create_pr(request, files, suggestions)
                result["pr_info"] = pr_info
            else:
                print("\n📝 Skipping PR creation (auto_create_pr=False)")
            
            return result
            
        except Exception as e:
            print(f"❌ Error processing request: {e}")
            return {"status": "error", "error": str(e)}
    
    def _create_pr(self, request: ResourceRequest, files: list, 
                  suggestions: list) -> Dict[str, Any]:
        """Create a GitHub pull request"""
        
        # Generate PR title and description
        pr_title = f"Add {request.resource_type.value.replace('_', ' ').title()}: {request.name}"
        
        pr_description = f"""## 🤖 Automated Infrastructure Request

**Resource Type**: {request.resource_type.value.replace('_', ' ').title()}
**Name**: `{request.name}`
**Environment**: `{request.environment}`
**Region**: `{request.region}`

### 📋 Request Details

{request.description or 'Generated from natural language request'}

### 🔧 Generated Configurations

This PR adds the following Crossplane configurations:

{chr(10).join([f"- `{file['path']}`" for file in files])}

### ⚙️ Configuration Summary

"""
        
        # Add resource-specific details
        if request.resource_type == ResourceType.EKS_CLUSTER:
            pr_description += f"""
**EKS Cluster Configuration:**
- Kubernetes Version: `{request.kubernetes_version or '1.28'}`
- Node Count: `{request.node_count or 3}`
- Instance Types: `{request.instance_types or 'Auto-selected based on environment'}`
"""
        elif request.resource_type == ResourceType.S3_BUCKET:
            pr_description += f"""
**S3 Bucket Configuration:**
- Versioning: `{'Enabled' if request.versioning != False else 'Disabled'}`
- Encryption: `{'Enabled' if request.encryption != False else 'Disabled'}`
"""
        elif request.resource_type == ResourceType.RDS_DATABASE:
            pr_description += f"""
**RDS Database Configuration:**
- Engine: `{request.engine or 'mysql'}`
- Instance Class: `{request.instance_class or 'Auto-selected'}`
- Storage: `{request.allocated_storage or 20}GB`
"""
        
        # Add suggestions
        if suggestions:
            pr_description += f"""
### 💡 Enhancement Suggestions

The AI agent has identified the following suggestions for consideration:

{chr(10).join([f"- {suggestion}" for suggestion in suggestions])}
"""
        
        pr_description += f"""
### 🔍 Review Checklist

- [ ] Resource naming follows organizational conventions
- [ ] Security configurations are appropriate for `{request.environment}` environment
- [ ] Resource sizing and scaling parameters are reasonable
- [ ] All required tags and labels are properly set
- [ ] Environment-specific configurations are correct
- [ ] Cost implications have been considered

### 🚀 Next Steps

1. **Review** the generated configurations carefully
2. **Test** in a non-production environment if possible
3. **Approve** and merge when ready
4. **Monitor** the Crossplane operator for successful provisioning

### ⚠️ Important Notes

- This will create **real AWS resources** and may incur costs
- Ensure you have proper AWS permissions configured
- Monitor the deployment through your Crossplane operator logs

---
*🤖 This PR was automatically generated by the Crossplane Agentic Workflow*
        """.strip()
        
        try:
            pr_result = self.github.create_automated_pr(
                files=files,
                pr_title=pr_title,
                pr_description=pr_description,
                branch_prefix=f"{request.resource_type.value}-{request.environment}"
            )
            
            print("   ✅ Pull Request created successfully!")
            print(f"   🔗 URL: {pr_result['pull_request']['html_url']}")
            print(f"   🌿 Branch: {pr_result['branch']}")
            
            return pr_result
            
        except GitHubAPIError as e:
            print(f"   ❌ Failed to create PR: {e}")
            return {"status": "error", "error": str(e)}
    
    def interactive_mode(self):
        """Run in interactive mode for conversational requests"""
        
        print("🤖 Welcome to Crossplane Agentic Workflow!")
        print("Type your infrastructure requests in natural language.")
        print("Examples:")
        print("  - 'Create an EKS cluster called analytics-cluster for production'")
        print("  - 'I need a secure S3 bucket for customer data'")
        print("  - 'Set up a MySQL database for our application'")
        print("\nType 'quit' or 'exit' to end the session.\n")
        
        while True:
            try:
                user_input = input("🔤 What infrastructure do you need? ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("👋 Goodbye!")
                    break
                
                if not user_input:
                    continue
                
                print("\n" + "=" * 60)
                result = self.process_request(user_input)
                print("=" * 60 + "\n")
                
                if result["status"] == "success" and "pr_info" in result:
                    pr_url = result["pr_info"]["pull_request"]["html_url"]
                    print(f"🎉 Success! Review your PR at: {pr_url}\n")
                elif result["status"] == "error":
                    print(f"❌ Error: {result.get('error', 'Unknown error')}\n")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Unexpected error: {e}\n")

def main():
    """Main entry point"""
    
    parser = argparse.ArgumentParser(
        description="Crossplane Agentic Workflow - Natural Language Infrastructure Provisioning",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python agentic_workflow.py --interactive
  
  # Single request
  python agentic_workflow.py --request "Create an EKS cluster for production"
  
  # Environment variables (recommended):
  export OPENAI_API_KEY="sk-..."
  export GITHUB_TOKEN="ghp_..."
  export GITHUB_REPO_OWNER="myorg"
  export GITHUB_REPO_NAME="infrastructure"
        """
    )
    
    # Mode selection
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--interactive", "-i", action="store_true",
                           help="Run in interactive mode")
    mode_group.add_argument("--request", "-r", type=str,
                           help="Process a single request")
    
    # API credentials
    parser.add_argument("--openai-api-key", 
                       default=os.getenv("OPENAI_API_KEY"),
                       help="OpenAI API key (or set OPENAI_API_KEY env var)")
    parser.add_argument("--github-token",
                       default=os.getenv("GITHUB_TOKEN"),
                       help="GitHub personal access token (or set GITHUB_TOKEN env var)")
    parser.add_argument("--repo-owner",
                       default=os.getenv("GITHUB_REPO_OWNER"),
                       help="GitHub repository owner (or set GITHUB_REPO_OWNER env var)")
    parser.add_argument("--repo-name",
                       default=os.getenv("GITHUB_REPO_NAME"),
                       help="GitHub repository name (or set GITHUB_REPO_NAME env var)")
    
    # Optional parameters
    parser.add_argument("--llm-model", default="gpt-5",
                       choices=["gpt-5", "gpt-5-nano", "gpt-4", "gpt-3.5-turbo"],
                       help="LLM model to use")
    parser.add_argument("--no-pr", action="store_true",
                       help="Don't create GitHub PR automatically")
    
    args = parser.parse_args()
    
    # Validate required credentials
    missing_creds = []
    if not args.openai_api_key:
        missing_creds.append("OpenAI API key (--openai-api-key or OPENAI_API_KEY)")
    if not args.github_token:
        missing_creds.append("GitHub token (--github-token or GITHUB_TOKEN)")
    if not args.repo_owner:
        missing_creds.append("Repository owner (--repo-owner or GITHUB_REPO_OWNER)")
    if not args.repo_name:
        missing_creds.append("Repository name (--repo-name or GITHUB_REPO_NAME)")
    
    if missing_creds:
        print("❌ Missing required credentials:")
        for cred in missing_creds:
            print(f"   - {cred}")
        print("\nPlease provide credentials via command line arguments or environment variables.")
        sys.exit(1)
    
    try:
        # Initialize workflow
        workflow = CrossplaneAgenticWorkflow(
            openai_api_key=args.openai_api_key,
            github_token=args.github_token,
            repo_owner=args.repo_owner,
            repo_name=args.repo_name,
            llm_model=args.llm_model
        )
        
        if args.interactive:
            workflow.interactive_mode()
        else:
            result = workflow.process_request(args.request, auto_create_pr=not args.no_pr)
            
            if result["status"] == "success":
                if "pr_info" in result:
                    pr_url = result["pr_info"]["pull_request"]["html_url"]
                    print(f"\n🎉 Success! Review your PR at: {pr_url}")
                else:
                    print(f"\n✅ Configurations generated successfully!")
                    print("Use --no-pr flag was used, so no PR was created.")
            else:
                print(f"\n❌ Error: {result.get('error', 'Unknown error')}")
                sys.exit(1)
    
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
