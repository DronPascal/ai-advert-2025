#!/usr/bin/env python3
"""Script to install and configure MCP servers for Regoose."""

import os
import subprocess
import sys
from pathlib import Path


def run_command(command: str) -> bool:
    """Run a shell command and return success status."""
    print(f"Running: {command}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ Success: {command}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed: {command}")
        print(f"Error: {e.stderr}")
        return False


def install_mcp_servers():
    """Install MCP servers for filesystem and shell operations."""
    
    print("🚀 Installing MCP servers for Regoose...")
    
    # Check if npm is available
    if not run_command("which npm"):
        print("❌ npm is required but not found. Please install Node.js and npm first.")
        return False
    
    # Install MCP filesystem server
    print("\\n📁 Installing MCP filesystem server...")
    if not run_command("npm install -g @modelcontextprotocol/server-filesystem"):
        print("⚠️  Failed to install filesystem MCP server")
    
    # Install MCP shell server
    print("\\n🖥️  Installing MCP shell server...")
    if not run_command("npm install -g @modelcontextprotocol/server-shell"):
        print("⚠️  Failed to install shell MCP server")
    
    # Create MCP configuration directory
    config_dir = Path.home() / ".config" / "regoose"
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # Create MCP configuration file
    mcp_config = {
        "mcpServers": {
            "filesystem": {
                "command": "npx",
                "args": ["@modelcontextprotocol/server-filesystem", "/tmp/regoose"],
                "env": {}
            },
            "shell": {
                "command": "npx", 
                "args": ["@modelcontextprotocol/server-shell"],
                "env": {}
            }
        }
    }
    
    import json
    config_file = config_dir / "mcp_config.json"
    config_file.write_text(json.dumps(mcp_config, indent=2))
    
    print(f"\\n📝 MCP configuration saved to: {config_file}")
    
    # Test MCP servers
    print("\\n🧪 Testing MCP servers...")
    
    # Test filesystem server
    if run_command("npx @modelcontextprotocol/server-filesystem --help"):
        print("✅ Filesystem MCP server is working")
    else:
        print("❌ Filesystem MCP server test failed")
    
    # Test shell server  
    if run_command("npx @modelcontextprotocol/server-shell --help"):
        print("✅ Shell MCP server is working")
    else:
        print("❌ Shell MCP server test failed")
    
    print("\\n🎉 MCP server installation complete!")
    print("\\n📋 Next steps:")
    print("1. Set up your OpenAI API key: regoose setup")
    print("2. Test the installation: regoose generate --code 'def test(): return True'")
    
    return True


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        # Check if MCP servers are installed
        print("🔍 Checking MCP server installation...")
        
        filesystem_ok = run_command("npx @modelcontextprotocol/server-filesystem --help")
        shell_ok = run_command("npx @modelcontextprotocol/server-shell --help")
        
        if filesystem_ok and shell_ok:
            print("✅ All MCP servers are installed and working")
            sys.exit(0)
        else:
            print("❌ Some MCP servers are missing or not working")
            sys.exit(1)
    else:
        success = install_mcp_servers()
        sys.exit(0 if success else 1)
