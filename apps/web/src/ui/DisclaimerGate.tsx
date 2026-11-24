import { useEffect, useRef } from "react";
import { Shield } from "./Icons";

export const DISCLAIMER_KEY = "scenic.disclaimer.v1";

/** The safety disclaimer gates the first plan (CLAUDE.md product invariant). Native <dialog>: focus trap + Escape. */
export function DisclaimerGate({ onAccept }: { onAccept: () => void }) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const dialog = ref.current;
    if (dialog && !dialog.open) dialog.showModal();
  }, []);
  return (
    <dialog ref={ref} className="gate" aria-labelledby="gate-title" onCancel={(e) => e.preventDefault()}>
      <span className="gate-icon">
        <Shield size={22} />
      </span>
      <h2 id="gate-title">Before you drive</h2>
      <p>
        Scenic routes use mountain and canyon roads. They can be narrow, winding, closed, or without phone signal, and
        this app does not know about road conditions today.
      </p>
      <ul>
        <li>Check closures and weather before you go.</li>
        <li>Follow road signs and your own judgement over any route.</li>
        <li>Set the route before you drive. Don't use your phone while driving.</li>
      </ul>
      <button
        type="button"
        className="button-primary"
        autoFocus
        onClick={() => {
          localStorage.setItem(DISCLAIMER_KEY, new Date().toISOString());
          ref.current?.close();
          onAccept();
        }}
      >
        I understand
      </button>
    </dialog>
  );
}
