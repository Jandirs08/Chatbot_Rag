import { MouseEvent, MouseEventHandler } from "react";
import {
  Heading,
  Link,
  Card,
  CardHeader,
  Flex,
  Spacer,
} from "@chakra-ui/react";
import { ExternalLinkIcon } from "@chakra-ui/icons";

export function EmptyState(props: { onChoice: (question: string) => any }) {
  const handleClick = (e: MouseEvent) => {
    props.onChoice((e.target as HTMLDivElement).innerText);
  };
  return (
    <div className="rounded flex flex-col items-center max-w-full md:p-1">
      <Heading fontSize="2xl" fontWeight={"medium"} mb={1} color={"white"}>
        Becas Grupo Romero
      </Heading>
    </div>
  );
}
