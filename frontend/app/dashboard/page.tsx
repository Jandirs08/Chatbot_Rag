"use client";

import {
  Box,
  Heading,
  Text,
  SimpleGrid,
  Card,
  CardBody,
  ChakraProvider,
} from "@chakra-ui/react";
import { FloatingChatWidget } from "../components/FloatingChatWidget";
import { ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";

export default function Dashboard() {
  return (
    <ChakraProvider>
      <ToastContainer />
      <Box p={8} maxW="1200px" mx="auto">
        <Heading
          as="h1"
          mb={6}
          fontSize="3xl"
          bgGradient="linear(to-r, #da5b3e, #fc382a)"
          bgClip="text"
        >
          Bienvenido al panel del chatbot
        </Heading>

        <Text mb={8} color="gray.300">
          Desde aquí podrás gestionar y monitorizar tu asistente virtual.
        </Text>

        <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={6}>
          <Card bg="gray.800" borderColor="gray.700" borderWidth="1px">
            <CardBody>
              <Text color="#ffd26b" fontWeight="bold" mb={2}>
                Espacio para futuras tarjetas
              </Text>
              <Text color="gray.400">
                Aquí se mostrarán estadísticas y resúmenes.
              </Text>
            </CardBody>
          </Card>
        </SimpleGrid>
      </Box>
      <FloatingChatWidget />
    </ChakraProvider>
  );
}
