"use client";

import { PreviewMessage, ThinkingMessage } from "@/components/message";
import { MultimodalInput } from "@/components/multimodal-input";
import { Overview } from "@/components/overview";
import { useScrollToBottom } from "@/hooks/use-scroll-to-bottom";
import { AnalyzePanel, type DetectResult } from "@/components/analyze-panel";
import { ToolInvocation } from "ai";
import { useChat } from "ai/react";
import { toast } from "sonner";
import type { Message } from "ai";

export function Chat() {
  const chatId = "001";

  const {
    messages,
    setMessages,
    handleSubmit,
    input,
    setInput,
    append,
    isLoading,
    stop,
  } = useChat({
    maxSteps: 4,
    onError: (error: Error) => {
      if (error.message.includes("Too many requests")) {
        toast.error(
          "You are sending too many messages. Please try again later.",
        );
      }
    },
  });

  const [messagesContainerRef, messagesEndRef] =
    useScrollToBottom<HTMLDivElement>();

  const handleAnalyzed = (result: DetectResult) => {
    const detectionContext: Message = {
      id: `sys-detect-${Date.now()}`,
      role: "system",
      content:
        `Detection context (not visible to user):\n` +
        `Summary: ${result.summary}\n` +
        `Total: ${result.total}\n` +
        `Counts: ${JSON.stringify(result.counts)}\n` +
        `Annotated: ${result.imageUrl}\n` +
        `Original: ${result.originalImageUrl}`,
    } as Message;

    setMessages((prev: Array<Message>) => [...prev, detectionContext]);
  };

  const handleAsk = async (prompt: string, result: DetectResult) => {
    await append({ role: "user", content: prompt });
  };

  return (
    <div className="flex flex-col min-w-0 h-[calc(100dvh-52px)] bg-background">
      <div
        ref={messagesContainerRef}
        className="flex flex-col min-w-0 gap-6 flex-1 overflow-y-scroll pt-4"
      >
        <div className="px-4">
          <AnalyzePanel onAnalyzed={handleAnalyzed} onAsk={handleAsk} />
        </div>
        {messages.length === 0 && <Overview />}

        {messages
          .filter((m: Message) => m.role !== "system")
          .map((message: Message, index: number, arr: Message[]) => (
          <PreviewMessage
            key={message.id}
            chatId={chatId}
            message={message}
            isLoading={isLoading && arr.length - 1 === index}
          />
        ))}

        {isLoading &&
          messages.filter((m: Message) => m.role !== "system").length > 0 &&
          messages.filter((m: Message) => m.role !== "system")[
            messages.filter((m: Message) => m.role !== "system").length - 1
          ].role === "user" && <ThinkingMessage />}

        <div
          ref={messagesEndRef}
          className="shrink-0 min-w-[24px] min-h-[24px]"
        />
      </div>

      <form className="flex mx-auto px-4 bg-background pb-4 md:pb-6 gap-2 w-full md:max-w-3xl">
        <MultimodalInput
          chatId={chatId}
          input={input}
          setInput={setInput}
          handleSubmit={handleSubmit}
          isLoading={isLoading}
          stop={stop}
          messages={messages}
          setMessages={setMessages}
          append={append}
        />
      </form>
    </div>
  );
}
