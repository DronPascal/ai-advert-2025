"""MCP-enabled LLM provider for tool integration."""

import os
import json
import asyncio
import subprocess
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .base import LLMProvider, LLMResponse


@dataclass
class MCPTool:
    """MCP tool definition."""
    name: str
    description: str
    inputSchema: Dict[str, Any]


class MCPProvider(LLMProvider):
    """LLM Provider with MCP tool integration."""
    
    def __init__(
        self,
        base_provider: LLMProvider,
        mcp_server_command: str,
        mcp_server_args: List[str] = None
    ):
        self.base_provider = base_provider
        self.mcp_server_command = mcp_server_command
        self.mcp_server_args = mcp_server_args or []
        self.available_tools: List[MCPTool] = []
        self.mcp_process: Optional[subprocess.Popen] = None
        self._debug_mode = False
    
    def set_debug_mode(self, enabled: bool):
        """Enable or disable debug mode for verbose logging."""
        self._debug_mode = enabled
    
    async def initialize_mcp(self) -> bool:
        """Initialize MCP server connection."""
        try:
            # Prepare environment for MCP server
            env = os.environ.copy()
            
            # Debug: Check if GitHub token is available
            if 'GITHUB_PERSONAL_ACCESS_TOKEN' in env:
                if hasattr(self, '_debug_mode') and self._debug_mode:
                    print(f"🔑 GITHUB_PERSONAL_ACCESS_TOKEN available for MCP server")
                else:
                    print(f"🔑 GitHub token available for MCP server")
            else:
                print("⚠️ No GITHUB_PERSONAL_ACCESS_TOKEN found in environment")
                
            # Start MCP server process with current environment
            self.mcp_process = subprocess.Popen(
                [self.mcp_server_command] + self.mcp_server_args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env  # Pass prepared environment to subprocess
            )
            
            # Initialize MCP protocol
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "clientInfo": {
                        "name": "regoose",
                        "version": "0.2.0"
                    }
                }
            }
            
            # Send initialization
            self.mcp_process.stdin.write(json.dumps(init_request) + "\n")
            self.mcp_process.stdin.flush()
            
            # Read response
            response_line = self.mcp_process.stdout.readline()
            if response_line:
                response = json.loads(response_line.strip())
                if response.get("result"):
                    await self._fetch_available_tools()
                    return True
            
            return False
            
        except Exception as e:
            print(f"MCP initialization error: {e}")
            return False
    
    async def _fetch_available_tools(self) -> None:
        """Fetch available tools from MCP server."""
        try:
            tools_request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }
            
            self.mcp_process.stdin.write(json.dumps(tools_request) + "\n")
            self.mcp_process.stdin.flush()
            
            response_line = self.mcp_process.stdout.readline()
            if response_line:
                response = json.loads(response_line.strip())
                tools_data = response.get("result", {}).get("tools", [])
                
                self.available_tools = [
                    MCPTool(
                        name=tool["name"],
                        description=tool["description"],
                        inputSchema=tool["inputSchema"]
                    )
                    for tool in tools_data
                ]
                
        except Exception as e:
            print(f"Error fetching MCP tools: {e}")
    
    async def call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call an MCP tool and return the result."""
        try:
            # Log the tool call for debugging
            print(f"🔧 MCP Tool Call: {tool_name}")
            if hasattr(self, '_debug_mode') and self._debug_mode:
                print(f"📋 Arguments: {json.dumps(arguments, indent=2)}")
            
            tool_request = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            self.mcp_process.stdin.write(json.dumps(tool_request) + "\n")
            self.mcp_process.stdin.flush()
            
            response_line = self.mcp_process.stdout.readline()
            if response_line:
                response = json.loads(response_line.strip())
                result = response.get("result", {})
                error = response.get("error")
                
                if error:
                    print(f"❌ MCP Tool Error: {error.get('message', 'Unknown error')}")
                    if hasattr(self, '_debug_mode') and self._debug_mode:
                        print(f"🔍 Full error: {json.dumps(error, indent=2)}")
                    return {"error": error}
                else:
                    print(f"✅ MCP Tool Success")
                    if hasattr(self, '_debug_mode') and self._debug_mode:
                        print(f"🔍 Full result: {json.dumps(result, indent=2)[:500]}...")
                    return result
            
            print("❌ No response from MCP server")
            return {"error": "No response from MCP server"}
            
        except Exception as e:
            print(f"❌ MCP tool call error: {e}")
            return {"error": f"MCP tool call error: {e}"}
    
    def get_tools_for_llm(self) -> List[Dict[str, Any]]:
        """Get tools formatted for LLM function calling."""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                }
            }
            for tool in self.available_tools
        ]
    
    async def generate(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """Generate response with MCP tool support."""
        # Add tools to the generation call if available
        if self.available_tools:
            kwargs['tools'] = self.get_tools_for_llm()
            kwargs['tool_choice'] = 'auto'
        
        # Generate response using base provider
        response = await self.base_provider.generate(messages, **kwargs)
        
        # Check if LLM wants to use tools
        if hasattr(response, 'tool_calls') and response.tool_calls:
            # Execute tool calls
            tool_results = []
            for tool_call in response.tool_calls:
                result = await self.call_mcp_tool(
                    tool_call.function.name,
                    json.loads(tool_call.function.arguments)
                )
                tool_results.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": tool_call.function.name,
                    "content": json.dumps(result)
                })
            
            # Add tool results to messages and generate final response
            final_messages = messages + [
                {"role": "assistant", "content": response.content, "tool_calls": response.tool_calls},
                *tool_results
            ]
            
            return await self.base_provider.generate(final_messages, **kwargs)
        
        return response
    
    def get_model_name(self) -> str:
        """Get model name with MCP suffix."""
        return f"{self.base_provider.get_model_name()}-mcp"
    
    def get_max_tokens(self) -> int:
        """Get maximum tokens from base provider."""
        return self.base_provider.get_max_tokens()
    
    def cleanup(self):
        """Cleanup MCP server process."""
        if self.mcp_process:
            self.mcp_process.terminate()
            self.mcp_process.wait()
            self.mcp_process = None
