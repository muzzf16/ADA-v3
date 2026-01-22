from typing import Dict, Any, Callable, Awaitable
import asyncio
from google.genai import types

class MiscHandler:
    def __init__(self,
                 web_agent,
                 project_manager,
                 kasa_agent,
                 on_web_data_callback=None,
                 on_project_update_callback=None,
                 on_device_update_callback=None,
                 on_error_callback=None,
                 session=None):
        self.web_agent = web_agent
        self.project_manager = project_manager
        self.kasa_agent = kasa_agent

        self.on_web_data = on_web_data_callback
        self.on_project_update = on_project_update_callback
        self.on_device_update = on_device_update_callback
        self.on_error = on_error_callback
        self.session = session # Reference to Gemini session for sending updates

    async def handle_run_web_agent(self, prompt, fc_id=None):
        """Handle web agent request."""
        print(f"[ADA DEBUG] [WEB] Web Agent Task: '{prompt}'")

        async def update_frontend(image_b64, log_text):
            if self.on_web_data:
                 self.on_web_data({"image": image_b64, "log": log_text})

        # Run the web agent and wait for it to return
        result = await self.web_agent.run_task(prompt, update_callback=update_frontend)
        print(f"[ADA DEBUG] [WEB] Web Agent Task Returned: {result}")

        # Send the final result back to the main model via session message
        if self.session:
            try:
                 await self.session.send(input=f"System Notification: Web Agent has finished.\nResult: {result}", end_of_turn=True)
            except Exception as e:
                 print(f"[ADA DEBUG] [ERR] Failed to send web agent result to model: {e}")

        # Return the immediate tool response
        return "Web Navigation started. Do not reply to this message."

    async def handle_create_project(self, name):
        """Handle create project."""
        print(f"[ADA DEBUG] [TOOL] Tool Call: 'create_project' name='{name}'")
        success, msg = self.project_manager.create_project(name)
        if success:
            # Auto-switch to the newly created project
            self.project_manager.switch_project(name)
            msg += f" Switched to '{name}'."
            if self.on_project_update:
                self.on_project_update(name)
        return {"result": msg}

    async def handle_switch_project(self, name):
        """Handle switch project."""
        print(f"[ADA DEBUG] [TOOL] Tool Call: 'switch_project' name='{name}'")
        success, msg = self.project_manager.switch_project(name)
        if success:
            if self.on_project_update:
                self.on_project_update(name)
            # Gather project context and send to AI (silently, no response expected)
            context = self.project_manager.get_project_context()
            print(f"[ADA DEBUG] [PROJECT] Sending project context to AI ({len(context)} chars)")
            if self.session:
                try:
                    await self.session.send(input=f"System Notification: {msg}\n\n{context}", end_of_turn=False)
                except Exception as e:
                    print(f"[ADA DEBUG] [ERR] Failed to send project context: {e}")
        return {"result": msg}

    async def handle_list_projects(self):
        """Handle list projects."""
        print(f"[ADA DEBUG] [TOOL] Tool Call: 'list_projects'")
        projects = self.project_manager.list_projects()
        return {"result": f"Available projects: {', '.join(projects)}"}

    async def handle_list_smart_devices(self):
        """Handle list smart devices."""
        print(f"[ADA DEBUG] [TOOL] Tool Call: 'list_smart_devices'")

        dev_summaries = []
        frontend_list = []

        for ip, d in self.kasa_agent.devices.items():
            dev_type = "unknown"
            if d.is_bulb: dev_type = "bulb"
            elif d.is_plug: dev_type = "plug"
            elif d.is_strip: dev_type = "strip"
            elif d.is_dimmer: dev_type = "dimmer"

            # Format for Model
            info = f"{d.alias} (IP: {ip}, Type: {dev_type})"
            if d.is_on:
                info += " [ON]"
            else:
                info += " [OFF]"
            dev_summaries.append(info)

            # Format for Frontend
            frontend_list.append({
                "ip": ip,
                "alias": d.alias,
                "model": d.model,
                "type": dev_type,
                "is_on": d.is_on,
                "brightness": d.brightness if d.is_bulb or d.is_dimmer else None,
                "hsv": d.hsv if d.is_bulb and d.is_color else None,
                "has_color": d.is_color if d.is_bulb else False,
                "has_brightness": d.is_dimmable if d.is_bulb or d.is_dimmer else False
            })

        result_str = "No devices found in cache."
        if dev_summaries:
            result_str = "Found Devices (Cached):\n" + "\n".join(dev_summaries)

        # Trigger frontend update
        if self.on_device_update:
            self.on_device_update(frontend_list)

        return {"result": result_str}

    async def handle_control_light(self, target, action, brightness=None, color=None):
        """Handle control light."""
        print(f"[ADA DEBUG] [TOOL] Tool Call: 'control_light' Target='{target}' Action='{action}'")

        result_msg = f"Action '{action}' on '{target}' failed."
        success = False

        if action == "turn_on":
            success = await self.kasa_agent.turn_on(target)
            if success:
                result_msg = f"Turned ON '{target}'."
        elif action == "turn_off":
            success = await self.kasa_agent.turn_off(target)
            if success:
                result_msg = f"Turned OFF '{target}'."
        elif action == "set":
            success = True
            result_msg = f"Updated '{target}':"

        # Apply extra attributes
        if success or action == "set":
            if brightness is not None:
                sb = await self.kasa_agent.set_brightness(target, brightness)
                if sb:
                    result_msg += f" Set brightness to {brightness}."
            if color is not None:
                sc = await self.kasa_agent.set_color(target, color)
                if sc:
                    result_msg += f" Set color to {color}."

        # Notify Frontend of State Change
        if success:
            updated_list = []
            for ip, dev in self.kasa_agent.devices.items():
                dev_type = "unknown"
                if dev.is_bulb: dev_type = "bulb"
                elif dev.is_plug: dev_type = "plug"
                elif dev.is_strip: dev_type = "strip"
                elif dev.is_dimmer: dev_type = "dimmer"

                d_info = {
                    "ip": ip,
                    "alias": dev.alias,
                    "model": dev.model,
                    "type": dev_type,
                    "is_on": dev.is_on,
                    "brightness": dev.brightness if dev.is_bulb or dev.is_dimmer else None,
                    "hsv": dev.hsv if dev.is_bulb and dev.is_color else None,
                    "has_color": dev.is_color if dev.is_bulb else False,
                    "has_brightness": dev.is_dimmable if dev.is_bulb or dev.is_dimmer else False
                }
                updated_list.append(d_info)

            if self.on_device_update:
                self.on_device_update(updated_list)
        else:
            # Report Error
            if self.on_error:
                self.on_error(result_msg)

        return {"result": result_msg}
