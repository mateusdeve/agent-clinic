"use client";
import * as React from "react";
import { getSocket, disconnectSocket } from "@/lib/socket";
import type { Socket } from "socket.io-client";

interface UseSocketReturn {
  socket: Socket | null;
  isConnected: boolean;
}

export function useSocket(token: string | undefined): UseSocketReturn {
  const [socket, setSocket] = React.useState<Socket | null>(null);
  const [isConnected, setIsConnected] = React.useState(false);

  React.useEffect(() => {
    if (!token) return;

    const s = getSocket(token);
    setSocket(s);

    function onConnect() { setIsConnected(true); }
    function onDisconnect() { setIsConnected(false); }

    s.on("connect", onConnect);
    s.on("disconnect", onDisconnect);

    if (s.connected) setIsConnected(true);

    return () => {
      s.off("connect", onConnect);
      s.off("disconnect", onDisconnect);
      // Do NOT call disconnectSocket here — singleton survives remounts
    };
  }, [token]);

  return { socket, isConnected };
}
