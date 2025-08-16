#!/usr/bin/env python3
"""
GitHub Integration for Crossplane Automation
Real GitHub API integration for creating branches, commits, and pull requests
"""

import os
import base64
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
import requests
from pathlib import Path

class GitHubAPIError(Exception):
    """Custom exception for GitHub API errors"""
    pass

class GitHubIntegration:
    """Real GitHub API integration for automated PR creation"""
    
    def __init__(self, token: str, repo_owner: str, repo_name: str):
        """
        Initialize GitHub integration
        
        Args:
            token: GitHub personal access token
            repo_owner: GitHub repository owner/organization
            repo_name: Repository name
        """
        self.token = token
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.base_url = "https://api.github.com"
        
        # Set up headers
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }
        
        # Verify token and repository access
        self._verify_access()
    
    def _verify_access(self):
        """Verify GitHub token and repository access"""
        try:
            # Test repository access
            url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 404:
                raise GitHubAPIError(f"Repository {self.repo_owner}/{self.repo_name} not found or no access")
            elif response.status_code == 401:
                raise GitHubAPIError("Invalid GitHub token")
            elif response.status_code != 200:
                raise GitHubAPIError(f"GitHub API error: {response.status_code} - {response.text}")
            
            repo_data = response.json()
            print(f"✅ Connected to repository: {repo_data['full_name']}")
            
        except requests.RequestException as e:
            raise GitHubAPIError(f"Failed to connect to GitHub API: {e}")
    
    def get_default_branch(self) -> str:
        """Get the default branch of the repository"""
        url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code != 200:
            raise GitHubAPIError(f"Failed to get repository info: {response.status_code}")
        
        return response.json()["default_branch"]
    
    def create_branch(self, branch_name: str, base_branch: Optional[str] = None) -> str:
        """
        Create a new branch
        
        Args:
            branch_name: Name of the new branch
            base_branch: Base branch to create from (defaults to default branch)
            
        Returns:
            SHA of the new branch
        """
        if base_branch is None:
            base_branch = self.get_default_branch()
        
        # Get base branch SHA
        url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/git/refs/heads/{base_branch}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code != 200:
            raise GitHubAPIError(f"Failed to get base branch {base_branch}: {response.status_code}")
        
        base_sha = response.json()["object"]["sha"]
        
        # Create new branch
        url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/git/refs"
        data = {
            "ref": f"refs/heads/{branch_name}",
            "sha": base_sha
        }
        
        response = requests.post(url, headers=self.headers, json=data)
        
        if response.status_code == 422:
            # Branch might already exist
            print(f"⚠️  Branch {branch_name} might already exist, continuing...")
            return base_sha
        elif response.status_code != 201:
            raise GitHubAPIError(f"Failed to create branch {branch_name}: {response.status_code} - {response.text}")
        
        print(f"✅ Created branch: {branch_name}")
        return response.json()["object"]["sha"]
    
    def create_or_update_file(self, file_path: str, content: str, commit_message: str, 
                             branch: str) -> Dict[str, Any]:
        """
        Create or update a file in the repository
        
        Args:
            file_path: Path to the file in the repository
            content: File content
            commit_message: Commit message
            branch: Branch to commit to
            
        Returns:
            Commit information
        """
        # Encode content to base64
        encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        
        # Check if file exists
        url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/contents/{file_path}"
        response = requests.get(url, headers=self.headers, params={"ref": branch})
        
        data = {
            "message": commit_message,
            "content": encoded_content,
            "branch": branch
        }
        
        # If file exists, we need the SHA for updating
        if response.status_code == 200:
            file_info = response.json()
            data["sha"] = file_info["sha"]
            print(f"📝 Updating existing file: {file_path}")
        else:
            print(f"📝 Creating new file: {file_path}")
        
        # Create or update file
        response = requests.put(url, headers=self.headers, json=data)
        
        if response.status_code not in [200, 201]:
            raise GitHubAPIError(f"Failed to create/update file {file_path}: {response.status_code} - {response.text}")
        
        return response.json()
    
    def commit_files(self, files: List[Dict[str, str]], commit_message: str, 
                    branch: str) -> List[Dict[str, Any]]:
        """
        Commit multiple files to a branch
        
        Args:
            files: List of file dictionaries with 'path' and 'content' keys
            commit_message: Commit message
            branch: Branch to commit to
            
        Returns:
            List of commit information for each file
        """
        commits = []
        
        for file_info in files:
            file_path = file_info['path']
            content = file_info['content']
            
            # Create individual commit message for each file
            individual_message = f"{commit_message}\n\nAdd: {file_path}"
            
            try:
                commit_info = self.create_or_update_file(
                    file_path=file_path,
                    content=content,
                    commit_message=individual_message,
                    branch=branch
                )
                commits.append(commit_info)
                
                # Small delay to avoid rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                print(f"⚠️  Failed to commit {file_path}: {e}")
                continue
        
        return commits
    
    def create_pull_request(self, title: str, description: str, head_branch: str, 
                          base_branch: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a pull request
        
        Args:
            title: PR title
            description: PR description
            head_branch: Source branch
            base_branch: Target branch (defaults to default branch)
            
        Returns:
            Pull request information
        """
        if base_branch is None:
            base_branch = self.get_default_branch()
        
        url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/pulls"
        data = {
            "title": title,
            "body": description,
            "head": head_branch,
            "base": base_branch,
            "maintainer_can_modify": True
        }
        
        response = requests.post(url, headers=self.headers, json=data)
        
        if response.status_code != 201:
            raise GitHubAPIError(f"Failed to create pull request: {response.status_code} - {response.text}")
        
        pr_info = response.json()
        print(f"🚀 Created Pull Request #{pr_info['number']}: {title}")
        print(f"🔗 URL: {pr_info['html_url']}")
        
        return pr_info
    
    def create_automated_pr(self, files: List[Dict[str, str]], pr_title: str, 
                          pr_description: str, branch_prefix: str = "automation") -> Dict[str, Any]:
        """
        Complete automated PR creation workflow
        
        Args:
            files: List of file dictionaries with 'path' and 'content' keys
            pr_title: Pull request title
            pr_description: Pull request description
            branch_prefix: Prefix for the branch name
            
        Returns:
            Pull request information
        """
        # Generate unique branch name
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        branch_name = f"{branch_prefix}-{timestamp}"
        
        try:
            # Step 1: Create branch
            print(f"🌿 Creating branch: {branch_name}")
            self.create_branch(branch_name)
            
            # Step 2: Commit files
            print(f"📁 Committing {len(files)} files...")
            commit_message = f"Automated: {pr_title}"
            commits = self.commit_files(files, commit_message, branch_name)
            
            if not commits:
                raise GitHubAPIError("No files were successfully committed")
            
            print(f"✅ Successfully committed {len(commits)} files")
            
            # Step 3: Create pull request
            print(f"🔄 Creating pull request...")
            pr_info = self.create_pull_request(pr_title, pr_description, branch_name)
            
            return {
                "branch": branch_name,
                "commits": commits,
                "pull_request": pr_info
            }
            
        except Exception as e:
            print(f"❌ Failed to create automated PR: {e}")
            # Attempt to clean up branch if PR creation failed
            try:
                self.delete_branch(branch_name)
            except:
                pass  # Ignore cleanup errors
            raise
    
    def delete_branch(self, branch_name: str):
        """
        Delete a branch
        
        Args:
            branch_name: Name of the branch to delete
        """
        url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/git/refs/heads/{branch_name}"
        response = requests.delete(url, headers=self.headers)
        
        if response.status_code == 204:
            print(f"🗑️  Deleted branch: {branch_name}")
        elif response.status_code != 404:  # 404 means branch doesn't exist
            print(f"⚠️  Failed to delete branch {branch_name}: {response.status_code}")
    
    def list_pull_requests(self, state: str = "open") -> List[Dict[str, Any]]:
        """
        List pull requests
        
        Args:
            state: PR state (open, closed, all)
            
        Returns:
            List of pull request information
        """
        url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/pulls"
        params = {"state": state, "per_page": 100}
        
        response = requests.get(url, headers=self.headers, params=params)
        
        if response.status_code != 200:
            raise GitHubAPIError(f"Failed to list pull requests: {response.status_code}")
        
        return response.json()

def test_github_integration():
    """Test function for GitHub integration (requires real token)"""
    
    print("🧪 Testing GitHub Integration")
    print("=" * 50)
    print("Note: This test requires a real GitHub token and repository")
    print("Set environment variables:")
    print("  - GITHUB_TOKEN")
    print("  - GITHUB_REPO_OWNER")
    print("  - GITHUB_REPO_NAME")
    
    token = os.getenv("GITHUB_TOKEN")
    repo_owner = os.getenv("GITHUB_REPO_OWNER")
    repo_name = os.getenv("GITHUB_REPO_NAME")
    
    if not all([token, repo_owner, repo_name]):
        print("❌ Missing required environment variables")
        return
    
    try:
        github = GitHubIntegration(token, repo_owner, repo_name)
        
        # Test file creation
        test_files = [
            {
                "path": "test/automated-test.yaml",
                "content": """apiVersion: v1
kind: ConfigMap
metadata:
  name: test-config
data:
  message: "This is a test file created by automation"
"""
            }
        ]
        
        result = github.create_automated_pr(
            files=test_files,
            pr_title="Test: Automated PR Creation",
            pr_description="This is a test PR created by the automation system.",
            branch_prefix="test"
        )
        
        print(f"✅ Test successful!")
        print(f"   Branch: {result['branch']}")
        print(f"   PR URL: {result['pull_request']['html_url']}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_github_integration()
