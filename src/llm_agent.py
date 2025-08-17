#!/usr/bin/env python3
"""
LLM Agent for Crossplane Resource Generation
Parses natural language requests and generates appropriate infrastructure configurations
"""

import json
import re
import openai
import requests
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

class LLMParsingError(Exception):
    """Exception raised when LLM parsing fails"""
    pass

class ResourceType(Enum):
    EKS_CLUSTER = "eks_cluster"
    S3_BUCKET = "s3_bucket"
    RDS_DATABASE = "rds_database"
    VPC = "vpc"

@dataclass
class ResourceRequest:
    """Structured representation of a resource request"""
    resource_type: ResourceType
    name: str
    region: str = "us-east-1"
    environment: str = "development"
    
    # EKS specific
    node_count: Optional[int] = None
    kubernetes_version: Optional[str] = None
    instance_types: Optional[List[str]] = None
    
    # S3 specific
    versioning: Optional[bool] = None
    encryption: Optional[bool] = None
    
    # RDS specific
    engine: Optional[str] = None
    instance_class: Optional[str] = None
    allocated_storage: Optional[int] = None
    
    # General
    tags: Optional[Dict[str, str]] = None
    description: Optional[str] = None

class LLMAgent:
    """LLM-powered agent for parsing infrastructure requests"""
    
    def __init__(self, api_key: str, model: str = "gpt-5"):
        """
        Initialize the LLM agent
        
        Args:
            api_key: OpenAI API key
            model: Model to use (gpt-4, gpt-3.5-turbo, etc.)
        """
        openai.api_key = api_key
        self.model = model
        
    def parse_request(self, user_input: str) -> ResourceRequest:
        """
        Parse natural language input into a structured ResourceRequest
        
        Args:
            user_input: Natural language description of infrastructure needs
            
        Returns:
            ResourceRequest object with parsed parameters
        """
        
        system_prompt = """
You are an expert infrastructure engineer specializing in AWS and Kubernetes. Your job is to parse natural language requests for cloud infrastructure and extract structured information.

Given a user's request, extract the following information and return it as JSON:

{
    "resource_type": "eks_cluster|s3_bucket|rds_database|vpc",
    "name": "resource-name",
    "region": "aws-region",
    "environment": "development|staging|production",
    "node_count": number (for EKS clusters),
    "kubernetes_version": "version" (for EKS clusters),
    "instance_types": ["type1", "type2"] (for EKS clusters),
    "versioning": true/false (for S3 buckets),
    "encryption": true/false (for S3 buckets),
    "engine": "mysql|postgres|etc" (for RDS),
    "instance_class": "db.t3.micro|etc" (for RDS),
    "allocated_storage": number (for RDS),
    "tags": {"key": "value"},
    "description": "brief description of the request"
}

Rules:
1. Always infer reasonable defaults for missing information
2. Use kebab-case for resource names
3. Default to us-east-1 region if not specified
4. Default to development environment if not specified
5. For EKS clusters, default to 3 nodes with kubernetes version 1.28
6. Include relevant tags based on the request context
7. Only include fields that are relevant to the resource type

Examples:

User: "Create an EKS cluster called analytics-cluster for production in us-west-2 with 5 nodes"
Response: {
    "resource_type": "eks_cluster",
    "name": "analytics-cluster",
    "region": "us-west-2",
    "environment": "production",
    "node_count": 5,
    "kubernetes_version": "1.28",
    "tags": {"purpose": "analytics", "team": "data"},
    "description": "Production EKS cluster for analytics workloads"
}

User: "I need a secure S3 bucket for storing customer data"
Response: {
    "resource_type": "s3_bucket",
    "name": "customer-data-bucket",
    "region": "us-east-1",
    "environment": "development",
    "versioning": true,
    "encryption": true,
    "tags": {"data-classification": "sensitive", "purpose": "customer-data"},
    "description": "Secure S3 bucket for customer data storage"
}
"""

        try:
            # Use HTTP path for GPT-5 family to support new params (max_completion_tokens)
            if str(self.model).startswith("gpt-5"):
                # Ultra-compact system prompt to minimize input tokens
                compact_system_prompt = "Return JSON only."

                def build_payload(max_tokens: int, use_schema: bool = True):
                    payload = {
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": compact_system_prompt},
                            {"role": "user", "content": user_input}
                        ],
                        "max_completion_tokens": max_tokens
                    }
                    
                    if use_schema:
                        payload["response_format"] = {
                            "type": "json_schema",
                            "json_schema": {
                                "name": "resource_request",
                                "schema": {
                                    "type": "object",
                                    "additionalProperties": False,
                                    "required": ["resource_type", "name"],
                                    "properties": {
                                        "resource_type": {
                                            "type": "string",
                                            "enum": ["eks_cluster", "s3_bucket", "rds_database", "vpc"]
                                        },
                                        "name": {"type": "string"},
                                        "region": {"type": "string"},
                                        "environment": {
                                            "type": "string",
                                            "enum": ["development", "staging", "production"]
                                        },
                                        "node_count": {"type": "integer"},
                                        "kubernetes_version": {"type": "string"},
                                        "instance_types": {"type": "array", "items": {"type": "string"}},
                                        "versioning": {"type": "boolean"},
                                        "encryption": {"type": "boolean"},
                                        "engine": {"type": "string"},
                                        "instance_class": {"type": "string"},
                                        "allocated_storage": {"type": "integer"},
                                        "tags": {"type": "object", "additionalProperties": {"type": "string"}},
                                        "description": {"type": "string"}
                                    }
                                }
                            }
                        }
                    else:
                        payload["response_format"] = {"type": "json_object"}
                    
                    return payload

                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                }

                # Progressive retry strategy: more tokens, then simpler format, then fallback model
                attempts = [
                    (512, True),   # 512 tokens with schema
                    (1024, True),  # 1024 tokens with schema
                    (1024, False), # 1024 tokens with simple json_object
                ]
                
                content = ""
                last_data = None
                last_finish = None
                
                for max_tok, use_schema in attempts:
                    try:
                        payload = build_payload(max_tok, use_schema)
                        resp = requests.post(
                            "https://api.openai.com/v1/chat/completions",
                            headers=headers,
                            data=json.dumps(payload),
                            timeout=60
                        )
                        resp.raise_for_status()
                        data = resp.json()
                        last_data = data
                        
                        # Print raw response for debugging
                        schema_type = "schema" if use_schema else "json_object"
                        print(f"🔄 LLM raw response (HTTP, {max_tok} tokens, {schema_type}):")
                        try:
                            print(json.dumps(data, indent=2, ensure_ascii=False))
                        except Exception:
                            print(f"Non-JSON response: {data}")
                        
                        content = data["choices"][0]["message"].get("content", "") or ""
                        content = content.strip()
                        last_finish = data["choices"][0].get("finish_reason")
                        
                        if content:
                            break
                            
                    except Exception as e:
                        print(f"⚠️ Attempt failed (tokens={max_tok}, schema={use_schema}): {e}")
                        continue

                # If still no content, try fallback to gpt-3.5-turbo
                if not content:
                    print("🔄 GPT-5 failed, falling back to gpt-3.5-turbo...")
                    fallback_agent = LLMAgent(self.api_key, "gpt-3.5-turbo")
                    return fallback_agent.parse_request(user_input)

                if not content:
                    raise LLMParsingError(
                        f"LLM returned empty content after all attempts (finish_reason={last_finish})."
                    )
            else:
                # Legacy SDK path for older models (e.g., gpt-3.5-turbo, gpt-4)
                response = openai.ChatCompletion.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_input}
                    ],
                    temperature=0.1,
                    max_tokens=500
                )
                
                # Extract JSON from response
                content = response.choices[0].message.content.strip()
            
            # Try to extract JSON if it's wrapped in markdown
            json_match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1)
            elif content.startswith('```') and content.endswith('```'):
                content = content[3:-3].strip()
            
            if not content:
                raise LLMParsingError("LLM returned empty content.")
            
            try:
                parsed_data = json.loads(content)
            except json.JSONDecodeError as e:
                raise LLMParsingError(f"LLM output is not valid JSON: {e}") from e
            
            # Convert to ResourceRequest
            resource_type = ResourceType(parsed_data["resource_type"])
            
            request = ResourceRequest(
                resource_type=resource_type,
                name=parsed_data["name"],
                region=parsed_data.get("region", "us-east-1"),
                environment=parsed_data.get("environment", "development"),
                node_count=parsed_data.get("node_count"),
                kubernetes_version=parsed_data.get("kubernetes_version"),
                instance_types=parsed_data.get("instance_types"),
                versioning=parsed_data.get("versioning"),
                encryption=parsed_data.get("encryption"),
                engine=parsed_data.get("engine"),
                instance_class=parsed_data.get("instance_class"),
                allocated_storage=parsed_data.get("allocated_storage"),
                tags=parsed_data.get("tags", {}),
                description=parsed_data.get("description")
            )
            
            return request
            
        except LLMParsingError as e:
            # Don't fall back to regex for LLM parsing errors - raise them directly
            raise e
        except Exception as e:
            # Fallback: try to extract basic information using regex for other errors
            print(f"⚠️  LLM parsing failed ({e}), falling back to regex parsing...")
            return self._fallback_parse(user_input)
    
    def _fallback_parse(self, user_input: str) -> ResourceRequest:
        """Fallback parsing using regex patterns"""
        
        # Determine resource type
        resource_type = ResourceType.EKS_CLUSTER  # default
        if any(word in user_input.lower() for word in ["bucket", "s3", "storage"]):
            resource_type = ResourceType.S3_BUCKET
        elif any(word in user_input.lower() for word in ["database", "db", "rds", "mysql", "postgres"]):
            resource_type = ResourceType.RDS_DATABASE
        elif any(word in user_input.lower() for word in ["vpc", "network", "subnet"]):
            resource_type = ResourceType.VPC
        
        # Extract name
        name_match = re.search(r'(?:called|named)\s+([a-zA-Z0-9-]+)', user_input)
        if not name_match:
            name_match = re.search(r'([a-zA-Z0-9-]+)(?:\s+cluster|\s+bucket|\s+database)', user_input)
        
        name = name_match.group(1) if name_match else "default-resource"
        name = re.sub(r'[^a-zA-Z0-9-]', '-', name).lower()
        
        # Extract region
        region_match = re.search(r'(us-[a-z]+-\d+|eu-[a-z]+-\d+|ap-[a-z]+-\d+)', user_input)
        region = region_match.group(1) if region_match else "us-east-1"
        
        # Extract environment
        environment = "development"  # default
        if any(word in user_input.lower() for word in ["prod", "production"]):
            environment = "production"
        elif any(word in user_input.lower() for word in ["staging", "stage"]):
            environment = "staging"
        
        # Extract node count for clusters
        node_count = None
        if resource_type == ResourceType.EKS_CLUSTER:
            node_match = re.search(r'(\d+)\s+nodes?', user_input)
            node_count = int(node_match.group(1)) if node_match else 3
        
        return ResourceRequest(
            resource_type=resource_type,
            name=name,
            region=region,
            environment=environment,
            node_count=node_count,
            kubernetes_version="1.28" if resource_type == ResourceType.EKS_CLUSTER else None,
            description=f"Parsed from: {user_input[:100]}..."
        )
    
    def generate_enhancement_suggestions(self, request: ResourceRequest) -> List[str]:
        """
        Generate suggestions for improving the resource configuration
        
        Args:
            request: The parsed resource request
            
        Returns:
            List of enhancement suggestions
        """
        
        suggestions = []
        
        if request.resource_type == ResourceType.EKS_CLUSTER:
            if request.node_count and request.node_count < 3:
                suggestions.append("Consider using at least 3 nodes for high availability")
            
            if request.environment == "production" and not request.instance_types:
                suggestions.append("For production, consider specifying instance types like ['m6i.large', 'm6i.xlarge']")
            
            if not request.tags or "cost-center" not in request.tags:
                suggestions.append("Consider adding cost-center tags for billing tracking")
        
        elif request.resource_type == ResourceType.S3_BUCKET:
            if request.encryption is None:
                suggestions.append("Consider enabling encryption for security")
            
            if request.versioning is None:
                suggestions.append("Consider enabling versioning for data protection")
        
        # General suggestions
        if request.environment == "production":
            suggestions.append("Ensure backup and disaster recovery plans are in place")
            suggestions.append("Consider implementing monitoring and alerting")
        
        return suggestions

def test_llm_agent():
    """Test function for the LLM agent"""
    
    # Mock test without actual API calls
    test_requests = [
        "Create an EKS cluster called analytics-cluster for production in us-west-2 with 5 nodes",
        "I need a secure S3 bucket for storing customer data",
        "Set up a MySQL database for our application"
    ]
    
    print("🧪 Testing LLM Agent (Mock Mode)")
    print("=" * 50)
    
    for i, request in enumerate(test_requests, 1):
        print(f"\n{i}. Request: {request}")
        
        # Mock parsing result
        if "cluster" in request:
            mock_result = ResourceRequest(
                resource_type=ResourceType.EKS_CLUSTER,
                name="analytics-cluster",
                region="us-west-2",
                environment="production",
                node_count=5,
                kubernetes_version="1.28",
                tags={"purpose": "analytics"},
                description="Production EKS cluster for analytics workloads"
            )
        elif "bucket" in request:
            mock_result = ResourceRequest(
                resource_type=ResourceType.S3_BUCKET,
                name="customer-data-bucket",
                region="us-east-1",
                environment="development",
                versioning=True,
                encryption=True,
                tags={"data-classification": "sensitive"},
                description="Secure S3 bucket for customer data storage"
            )
        else:
            mock_result = ResourceRequest(
                resource_type=ResourceType.RDS_DATABASE,
                name="app-database",
                region="us-east-1",
                environment="development",
                engine="mysql",
                instance_class="db.t3.micro",
                tags={"purpose": "application"},
                description="MySQL database for application"
            )
        
        print(f"   Parsed: {mock_result.resource_type.value}")
        print(f"   Name: {mock_result.name}")
        print(f"   Region: {mock_result.region}")
        print(f"   Environment: {mock_result.environment}")
        if mock_result.node_count:
            print(f"   Node Count: {mock_result.node_count}")

if __name__ == "__main__":
    test_llm_agent()
