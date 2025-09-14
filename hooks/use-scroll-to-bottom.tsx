import { useEffect, useRef, type RefObject } from "react";

export function useScrollToBottom<T extends HTMLElement>(): [
  RefObject<T>,
  RefObject<T>,
] {
  const containerRef = useRef<T>(null);
  const endRef = useRef<T>(null);

  useEffect(() => {
    const container = containerRef.current;
    const end = endRef.current;

    if (container && end) {
      const observer = new MutationObserver(() => {
        end.scrollIntoView({ behavior: "auto", block: "end" });
      });

      // Only observe child list mutations so clicks/attribute changes in
      // non-message areas (e.g., image container) don't auto-scroll.
      observer.observe(container, {
        childList: true,
      });

      return () => observer.disconnect();
    }
  }, []);

  return [containerRef, endRef];
}
