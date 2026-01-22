from typing import Dict, Any, Callable, Awaitable, List
from google.genai import types
import inspect

class ToolRegistry:
    def __init__(self):
        self.handlers: Dict[str, Callable[..., Awaitable[Any]]] = {}
        self.definitions: List[Dict[str, Any]] = []

    def register_tool(self, name: str, handler: Callable[..., Awaitable[Any]], definition: Dict[str, Any]):
        """
        Register a tool with its handler and definition.

        Args:
            name: The tool name (must match definition['name'])
            handler: Async function to execute the tool
            definition: The JSON schema for the tool
        """
        if name != definition['name']:
            raise ValueError(f"Tool name mismatch: {name} != {definition['name']}")

        self.handlers[name] = handler
        self.definitions.append(definition)
        print(f"[REGISTRY] Registered tool: {name}")

    def register_handler(self, handler_instance, tool_map: Dict[str, str], definitions_list: List[Dict[str, Any]]):
        """
        Bulk register tools from a handler instance.

        Args:
            handler_instance: The handler object (e.g., GoogleWorkspaceHandler)
            tool_map: Dict mapping tool_name -> method_name on the handler
            definitions_list: List of tool definition dicts
        """
        for tool_name, method_name in tool_map.items():
            if not hasattr(handler_instance, method_name):
                print(f"[REGISTRY] WARNING: Handler {handler_instance} missing method {method_name} for tool {tool_name}")
                continue

            method = getattr(handler_instance, method_name)

            # Find matching definition
            defn = next((d for d in definitions_list if d['name'] == tool_name), None)
            if not defn:
                print(f"[REGISTRY] WARNING: No definition found for tool {tool_name}")
                continue

            self.register_tool(tool_name, method, defn)

    def get_tool_definitions(self):
        """Get the list of all registered tool definitions."""
        return self.definitions

    async def execute_tool(self, tool_call, permissions: Dict[str, bool] = None, on_confirmation=None):
        """
        Execute a tool call from Gemini.

        Args:
            tool_call: The tool call object (fc) from Gemini
            permissions: Dict of tool permissions
            on_confirmation: Callback for user confirmation

        Returns:
            The FunctionResponse object
        """
        name = tool_call.name
        args = tool_call.args

        if name not in self.handlers:
            print(f"[REGISTRY] Error: Unknown tool '{name}'")
            return types.FunctionResponse(
                id=tool_call.id,
                name=name,
                response={"error": f"Unknown tool: {name}"}
            )

        # Permission Check
        if permissions:
            allowed = permissions.get(name, True) # Default allow if not specified? Or False? ada.py used True
            if not allowed:
                # If explicitly False, check if we need confirmation?
                # Ada.py logic: "If not confirmation_required: pass"
                # Actually ada.py logic was: `confirmation_required = self.permissions.get(fc.name, True)`
                # This implies permissions dict stores "Requires Confirmation" bool, NOT "Is Allowed".
                pass

        # Confirmation Logic (Replicating ada.py logic)
        # permissions map: tool_name -> requires_confirmation (bool)
        # Default in ada.py was True (requires confirmation) if not found.
        requires_confirmation = True
        if permissions and name in permissions:
             requires_confirmation = permissions[name]

        # Some tools might be always safe? Ada.py didn't seem to have a whitelist.

        if requires_confirmation and on_confirmation:
            import asyncio
            import uuid
            request_id = str(uuid.uuid4())
            print(f"[ADA DEBUG] [STOP] Requesting confirmation for '{name}' (ID: {request_id})")

            confirmed = await on_confirmation(request_id, name, args)

            if not confirmed:
                print(f"[ADA DEBUG] [DENY] Tool call '{name}' denied by user.")
                return types.FunctionResponse(
                    id=tool_call.id,
                    name=name,
                    response={"result": "User denied the request to use this tool."}
                )

        # Execute
        try:
            handler = self.handlers[name]

            # Inspect signature to see if we need to pass specific args (like fc.id for async/callback tools)
            # For now, we assume handler takes **args or specific named args matching the schema.
            # Ada.py manually unpacked args for some, passed kwargs for others.
            # Most handlers I wrote take named args.

            # Special case for run_web_agent which might need the tool call ID if we wanted to respond later?
            # But my refactored handler returns a string immediately.

            print(f"[REGISTRY] Executing {name} with args: {args}")

            # Inspect if handler accepts **kwargs to safely pass everything
            sig = inspect.signature(handler)
            if any(p.kind == p.VAR_KEYWORD for p in sig.parameters.values()):
                 result = await handler(**args)
            else:
                 # Filter args to only what the function accepts
                 valid_args = {k: v for k, v in args.items() if k in sig.parameters}
                 result = await handler(**valid_args)

            # If result is already a dict with "result" key, use it. Otherwise wrap it.
            # My handlers return {"result": ...} or similar dicts.
            if isinstance(result, dict):
                response_data = result
            else:
                response_data = {"result": str(result)}

            return types.FunctionResponse(
                id=tool_call.id,
                name=name,
                response=response_data
            )

        except Exception as e:
            print(f"[REGISTRY] Execution failed for {name}: {e}")
            import traceback
            traceback.print_exc()
            return types.FunctionResponse(
                id=tool_call.id,
                name=name,
                response={"error": str(e)}
            )
