"use client";

import { ChatWindow } from "../components/ChatWindow";
import { ToastContainer } from "react-toastify";
import { v4 as uuidv4 } from "uuid";
import { ChakraProvider } from "@chakra-ui/react";

export default function ChatPage() {
  const conversationId = uuidv4();
  return (
    <ChakraProvider>
      <ToastContainer />
      <div className="h-screen w-screen">
        <ChatWindow titleText="Chatbot" conversationId={conversationId} />
      </div>
    </ChakraProvider>
  );
}
