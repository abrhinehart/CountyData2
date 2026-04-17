import { useEffect, useState, type ReactNode } from "react";

interface Props {
  id: string;
  title: ReactNode;
  defaultOpen?: boolean;
  children: ReactNode;
}

export default function CollapsibleSection({ id, title, defaultOpen = true, children }: Props) {
  const storageKey = `health:section:${id}`;
  const [open, setOpen] = useState<boolean>(() => {
    try {
      const v = localStorage.getItem(storageKey);
      if (v === "0") return false;
      if (v === "1") return true;
    } catch {
      /* ignore */
    }
    return defaultOpen;
  });

  useEffect(() => {
    try {
      localStorage.setItem(storageKey, open ? "1" : "0");
    } catch {
      /* ignore */
    }
  }, [open, storageKey]);

  return (
    <section className="space-y-3">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="text-left w-full select-none group"
      >
        <h2 className={
          "text-lg font-medium border-b pb-1 transition-colors " +
          (open
            ? "text-gray-800 border-gray-300 group-hover:text-gray-900"
            : "text-gray-500 border-transparent group-hover:text-gray-800")
        }>
          {title}
        </h2>
      </button>
      {open && <div>{children}</div>}
    </section>
  );
}
