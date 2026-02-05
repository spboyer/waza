"""Transport implementations for JSON-RPC."""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class Transport(ABC):
    """Abstract base class for transports."""

    @abstractmethod
    async def read_message(self) -> dict[str, Any] | None:
        """Read a message from the transport.
        
        Returns:
            Parsed JSON message, or None if connection closed.
        """
        pass

    @abstractmethod
    async def write_message(self, message: dict[str, Any]) -> None:
        """Write a message to the transport.
        
        Args:
            message: Message to write (will be JSON-serialized).
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close the transport."""
        pass


class StdioTransport(Transport):
    """Stdio transport - reads from stdin, writes to stdout."""

    def __init__(self):
        """Initialize stdio transport."""
        self._stdin_reader: asyncio.StreamReader | None = None
        self._stdout_writer: asyncio.StreamWriter | None = None
        self._closed = False

    async def _ensure_streams(self) -> None:
        """Ensure stdin/stdout streams are initialized."""
        if self._stdin_reader is None:
            loop = asyncio.get_event_loop()
            self._stdin_reader = asyncio.StreamReader()
            protocol = asyncio.StreamReaderProtocol(self._stdin_reader)
            await loop.connect_read_pipe(lambda: protocol, sys.stdin)
            
            # Create writer for stdout
            transport, protocol = await loop.connect_write_pipe(
                asyncio.streams.FlowControlMixin,
                sys.stdout
            )
            self._stdout_writer = asyncio.StreamWriter(transport, protocol, None, loop)

    async def read_message(self) -> dict[str, Any] | None:
        """Read a JSON-RPC message from stdin.
        
        Returns:
            Parsed JSON message, or None if stdin closed.
        """
        if self._closed:
            return None

        await self._ensure_streams()
        
        try:
            # Read line from stdin
            line = await self._stdin_reader.readline()
            if not line:
                return None
            
            # Parse JSON
            text = line.decode('utf-8').strip()
            if not text:
                return None
                
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            raise
        except Exception as e:
            logger.error(f"Error reading from stdin: {e}")
            return None

    async def write_message(self, message: dict[str, Any]) -> None:
        """Write a JSON-RPC message to stdout.
        
        Args:
            message: Message to write.
        """
        if self._closed:
            return

        await self._ensure_streams()
        
        try:
            # Serialize to JSON
            text = json.dumps(message, separators=(',', ':'))
            
            # Write to stdout with newline
            self._stdout_writer.write((text + '\n').encode('utf-8'))
            await self._stdout_writer.drain()
        except Exception as e:
            logger.error(f"Error writing to stdout: {e}")
            raise

    async def close(self) -> None:
        """Close the transport."""
        self._closed = True
        if self._stdout_writer:
            self._stdout_writer.close()
            await self._stdout_writer.wait_closed()


class TCPTransport(Transport):
    """TCP transport - reads/writes over TCP socket."""

    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Initialize TCP transport.
        
        Args:
            reader: Async stream reader.
            writer: Async stream writer.
        """
        self._reader = reader
        self._writer = writer
        self._closed = False

    async def read_message(self) -> dict[str, Any] | None:
        """Read a JSON-RPC message from TCP socket.
        
        Returns:
            Parsed JSON message, or None if connection closed.
        """
        if self._closed:
            return None

        try:
            # Read line from socket
            line = await self._reader.readline()
            if not line:
                return None
            
            # Parse JSON
            text = line.decode('utf-8').strip()
            if not text:
                return None
                
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            raise
        except Exception as e:
            logger.error(f"Error reading from TCP: {e}")
            return None

    async def write_message(self, message: dict[str, Any]) -> None:
        """Write a JSON-RPC message to TCP socket.
        
        Args:
            message: Message to write.
        """
        if self._closed:
            return

        try:
            # Serialize to JSON
            text = json.dumps(message, separators=(',', ':'))
            
            # Write to socket with newline
            self._writer.write((text + '\n').encode('utf-8'))
            await self._writer.drain()
        except Exception as e:
            logger.error(f"Error writing to TCP: {e}")
            raise

    async def close(self) -> None:
        """Close the transport."""
        self._closed = True
        self._writer.close()
        await self._writer.wait_closed()
