import { useEffect } from "react";

interface Props {
  ref: React.RefObject<HTMLElement>;
  callback: Function;
}

/** React.RefObject 밖의 영역을 클릭했을 때 callback을 실행하는 hook */
function useClickOutside({ ref, callback }: Props) {
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        callback();
      }
    };

    window.addEventListener("mousedown", handleClick);

    // cleanUp
    return () => window.removeEventListener("mousedown", handleClick);
  }, [ref, callback]);
}

export default useClickOutside;
