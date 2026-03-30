"use client";
import { io, Socket } from "socket.io-client";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

let _socket: Socket | null = null;

export function getSocket(token: string): Socket {
  if (!_socket) {
    _socket = io(API_URL, {
      auth: { token },
      transports: ["websocket"],
      reconnectionDelayMax: 10000,
    });
  }
  return _socket;
}

export function disconnectSocket(): void {
  _socket?.disconnect();
  _socket = null;
}
