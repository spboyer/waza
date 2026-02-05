"""JSON-RPC 2.0 server implementation."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from pydantic import ValidationError

from waza.jsonrpc.methods import MethodHandler
from waza.jsonrpc.protocol import (
    JSONRPCError,
    JSONRPCNotification,
    JSONRPCRequest,
    JSONRPCResponse,
)
from waza.jsonrpc.transports import Transport

logger = logging.getLogger(__name__)


class JSONRPCServer:
    """JSON-RPC 2.0 server."""

    def __init__(self, transport: Transport):
        """Initialize JSON-RPC server.
        
        Args:
            transport: Transport to use for communication.
        """
        self._transport = transport
        self._method_handler = MethodHandler(notification_callback=self._send_notification)
        self._running = False

    async def _send_notification(self, method: str, params: dict[str, Any]) -> None:
        """Send a notification to the client.
        
        Args:
            method: Notification method name.
            params: Notification parameters.
        """
        notification = JSONRPCNotification(method=method, params=params)
        await self._transport.write_message(notification.model_dump(exclude_none=True))

    async def _handle_request(self, request_data: dict[str, Any]) -> JSONRPCResponse | None:
        """Handle a JSON-RPC request.
        
        Args:
            request_data: Raw request data.
            
        Returns:
            Response, or None for notifications.
        """
        # Parse request
        try:
            request = JSONRPCRequest(**request_data)
        except ValidationError as e:
            return JSONRPCResponse.error_response(
                None,
                JSONRPCError.invalid_request(str(e))
            )
        except Exception as e:
            return JSONRPCResponse.error_response(
                None,
                JSONRPCError.parse_error(str(e))
            )

        # Check if this is a notification (no response needed)
        if request.is_notification:
            logger.info(f"Received notification: {request.method}")
            return None

        # Route to method handler
        try:
            result = await self._dispatch_method(request.method, request.params or {})
            return JSONRPCResponse.success(request.id, result)
        except JSONRPCError as e:
            return JSONRPCResponse.error_response(request.id, e)
        except Exception as e:
            logger.exception(f"Internal error handling {request.method}: {e}")
            return JSONRPCResponse.error_response(
                request.id,
                JSONRPCError.internal_error(str(e))
            )

    async def _dispatch_method(self, method: str, params: dict[str, Any]) -> Any:
        """Dispatch method to handler.
        
        Args:
            method: Method name.
            params: Method parameters.
            
        Returns:
            Method result.
        """
        # Map methods to handlers
        handlers = {
            "eval.run": self._method_handler.handle_eval_run,
            "eval.list": self._method_handler.handle_eval_list,
            "eval.get": self._method_handler.handle_eval_get,
            "eval.validate": self._method_handler.handle_eval_validate,
            "task.list": self._method_handler.handle_task_list,
            "task.get": self._method_handler.handle_task_get,
            "run.status": self._method_handler.handle_run_status,
            "run.cancel": self._method_handler.handle_run_cancel,
        }

        handler = handlers.get(method)
        if not handler:
            raise JSONRPCError.method_not_found(method)

        return await handler(params)

    async def serve(self) -> None:
        """Start serving JSON-RPC requests."""
        self._running = True
        logger.info("JSON-RPC server started")

        try:
            while self._running:
                # Read message from transport
                try:
                    message = await self._transport.read_message()
                except json.JSONDecodeError as e:
                    # Send parse error
                    response = JSONRPCResponse.error_response(
                        None,
                        JSONRPCError.parse_error(str(e))
                    )
                    await self._transport.write_message(response.model_dump(exclude_none=True))
                    continue
                except Exception as e:
                    logger.error(f"Error reading message: {e}")
                    break

                # Check if connection closed
                if message is None:
                    logger.info("Connection closed")
                    break

                # Handle request
                response = await self._handle_request(message)

                # Send response (if not a notification)
                if response:
                    await self._transport.write_message(response.model_dump(exclude_none=True))
        finally:
            await self._transport.close()
            logger.info("JSON-RPC server stopped")

    async def stop(self) -> None:
        """Stop the server."""
        self._running = False
        await self._transport.close()
