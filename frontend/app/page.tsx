"use client";

import { ChatWindow } from "./components/ChatWindow";
import { ChakraProvider } from "@chakra-ui/react";
import { ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";

import { v4 as uuidv4 } from "uuid";

export default function Home() {
  const conversationId = uuidv4();
  return (
    <ChakraProvider>
      <ToastContainer />
      <ChatWindow
        titleText="Personality Chatbot"
        conversationId={conversationId}
      ></ChatWindow>
    </ChakraProvider>
  );
}
