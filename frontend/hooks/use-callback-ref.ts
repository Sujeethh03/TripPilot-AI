"use client";

import { useCallback, useEffect, useRef } from "react";

/**
 * Returns a stable callback whose identity never changes but which always calls
 * the latest passed function. Lets effects depend on a handler without
 * re-running when the handler's closure changes (e.g. the WS socket effect).
 */
export function useCallbackRef<Args extends unknown[], Return>(
  callback: (...args: Args) => Return
): (...args: Args) => Return {
  const ref = useRef(callback);

  useEffect(() => {
    ref.current = callback;
  });

  return useCallback((...args: Args) => ref.current(...args), []);
}
