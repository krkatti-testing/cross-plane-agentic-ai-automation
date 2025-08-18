#!/usr/bin/env python3
"""
Flask Web Application for Crossplane Agentic Automation
Provides a web interface for natural language infrastructure requests
"""

import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any
from flask import Flask, render_template, request, jsonify, redirect, url_for
import threading
import time

# Import our workflow components
from src.agentic_workflow import CrossplaneAgenticWorkflow
from src.llm_agent import ResourceType

app = Flask(__name__)

# Global workflow status storage
workflow_status = {}

def check_configuration():
    """Check if required environment variables are configured"""
    return {
        'openai_configured': bool(os.getenv('OPENAI_API_KEY')),
        'github_configured': bool(os.getenv('GITHUB_TOKEN')),
        'repo_owner': os.getenv('GITHUB_REPO_OWNER', ''),
        'repo_name': os.getenv('GITHUB_REPO_NAME', '')
    }

def run_workflow_async(workflow_id: str, user_input: str, config: Dict[str, str]):
    """Run the workflow asynchronously and update status"""
    try:
        # Update status to running
        workflow_status[workflow_id].update({
            'status': 'running',
            'stage': 'initializing',
            'message': 'Initializing workflow...',
            'started_at': datetime.now().isoformat()
        })
        
        # Initialize workflow
        workflow = CrossplaneAgenticWorkflow(
            openai_api_key=config['openai_api_key'],
            github_token=config['github_token'],
            repo_owner=config['repo_owner'],
            repo_name=config['repo_name'],
            llm_model="gpt-5"
        )
        
        # Run the workflow
        result = workflow.run_workflow(user_input, workflow_id)
        
        # Debug: Print the result structure
        print(f"🔍 DEBUG - Workflow result: {result}")
        
        # Process and format the result data
        formatted_result = {}
        if result and result.get('status') == 'success':
            # Extract PR URL from pr_info
            if 'pr_info' in result and result['pr_info'].get('pull_request'):
                formatted_result['pr_url'] = result['pr_info']['pull_request']['html_url']
                formatted_result['branch'] = result['pr_info'].get('branch', '')
            
            # Extract files list and convert to file paths
            if 'files' in result:
                formatted_result['files'] = [file['path'] for file in result['files']]
            
            # Extract parsed request
            if 'request' in result:
                formatted_result['request'] = result['request']
        
        # Update final status
        final_status = 'completed' if result and result.get('status') == 'success' else 'error'
        final_message = result.get('message', 'Workflow completed successfully') if final_status == 'completed' else result.get('error', 'Workflow failed')
        
        workflow_status[workflow_id].update({
            'status': final_status,
            'stage': 'completed',
            'message': final_message,
            'result': formatted_result if formatted_result else result,
            'completed_at': datetime.now().isoformat()
        })
        
        if final_status == 'error' and result:
            workflow_status[workflow_id]['error'] = result.get('error', str(result))
        
    except Exception as e:
        workflow_status[workflow_id].update({
            'status': 'error',
            'stage': 'error',
            'message': f'Workflow failed: {str(e)}',
            'error': str(e),
            'completed_at': datetime.now().isoformat()
        })

@app.route('/')
def index():
    """Main page with prompt interface"""
    config = check_configuration()
    return render_template('index.html', config=config)

@app.route('/submit', methods=['POST'])
def submit_request():
    """Handle form submission and start workflow"""
    user_input = request.form.get('prompt', '').strip()
    
    if not user_input:
        return jsonify({'error': 'Please enter a request'}), 400
    
    # Check configuration
    config = check_configuration()
    if not config['openai_configured'] or not config['github_configured']:
        return jsonify({'error': 'OpenAI API key or GitHub token not configured'}), 400
    
    # Generate workflow ID
    workflow_id = str(uuid.uuid4())
    
    # Initialize workflow status
    workflow_status[workflow_id] = {
        'id': workflow_id,
        'prompt': user_input,
        'status': 'queued',
        'stage': 'queued',
        'message': 'Workflow queued for processing',
        'created_at': datetime.now().isoformat(),
        'paused': False
    }
    
    # Start workflow in background thread
    workflow_config = {
        'openai_api_key': os.getenv('OPENAI_API_KEY'),
        'github_token': os.getenv('GITHUB_TOKEN'),
        'repo_owner': os.getenv('GITHUB_REPO_OWNER'),
        'repo_name': os.getenv('GITHUB_REPO_NAME')
    }
    
    thread = threading.Thread(
        target=run_workflow_async,
        args=(workflow_id, user_input, workflow_config)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'workflow_id': workflow_id,
        'status': 'queued',
        'message': 'Workflow started successfully'
    })

@app.route('/status/<workflow_id>')
def get_workflow_status(workflow_id):
    """Get workflow status"""
    if workflow_id not in workflow_status:
        return jsonify({'error': 'Workflow not found'}), 404
    
    status = workflow_status[workflow_id].copy()
    
    # Handle ResourceType serialization
    if 'result' in status and status['result']:
        result = status['result'].copy()
        if 'request' in result and hasattr(result['request'], 'resource_type'):
            if hasattr(result['request'].resource_type, 'value'):
                result['request'] = {
                    'resource_type': result['request'].resource_type.value,
                    'name': result['request'].name,
                    'region': result['request'].region,
                    'environment': result['request'].environment,
                    'node_count': result['request'].node_count,
                    'kubernetes_version': result['request'].kubernetes_version,
                    'instance_types': result['request'].instance_types,
                    'versioning': result['request'].versioning,
                    'encryption': result['request'].encryption,
                    'engine': result['request'].engine,
                    'instance_class': result['request'].instance_class,
                    'allocated_storage': result['request'].allocated_storage,
                    'tags': result['request'].tags,
                    'description': result['request'].description
                }
        status['result'] = result
    
    return jsonify(status)

@app.route('/workflows')
def workflows():
    """List all workflows"""
    return render_template('workflows.html', workflows=workflow_status)

@app.route('/workflow/<workflow_id>')
def workflow_detail(workflow_id):
    """Show detailed workflow information"""
    if workflow_id not in workflow_status:
        return "Workflow not found", 404
    
    workflow = workflow_status[workflow_id]
    return render_template('workflow_detail.html', workflow=workflow)

@app.route('/examples')
def examples():
    """Show example requests"""
    return render_template('examples.html')

@app.route('/api/config')
def api_config():
    """API endpoint to check configuration"""
    config = check_configuration()
    return jsonify(config)

if __name__ == '__main__':
    print("🌐 Starting Crossplane Agentic Automation Web Interface...")
    
    # Check configuration
    config = check_configuration()
    print(f"🔧 Workflow Available: True")
    print(f"🔑 OpenAI Configured: {config['openai_configured']}")
    print(f"🐙 GitHub Configured: {config['github_configured']}")
    print("=" * 60)
    print(f"🚀 Open your browser to: http://localhost:5001")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5001)
