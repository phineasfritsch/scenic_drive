type P = { size?: number };

const base = (size: number) => ({
  width: size,
  height: size,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 2,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
  "aria-hidden": true,
});

export const Logo = ({ size = 28 }: P) => (
  <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden>
    <rect width="32" height="32" rx="9" fill="var(--primary)" />
    <path d="M6 22c4-1 5-6 9-7s5 4 11-3" fill="none" stroke="var(--on-primary)" strokeWidth="3" strokeLinecap="round" />
  </svg>
);

export const Plus = ({ size = 18 }: P) => (
  <svg {...base(size)}>
    <path d="M12 5v14M5 12h14" />
  </svg>
);

export const Minus = ({ size = 18 }: P) => (
  <svg {...base(size)}>
    <path d="M5 12h14" />
  </svg>
);

export const Fit = ({ size = 18 }: P) => (
  <svg {...base(size)}>
    <path d="M4 9V5a1 1 0 0 1 1-1h4M15 4h4a1 1 0 0 1 1 1v4M20 15v4a1 1 0 0 1-1 1h-4M9 20H5a1 1 0 0 1-1-1v-4" />
  </svg>
);

export const Shield = ({ size = 16 }: P) => (
  <svg {...base(size)}>
    <path d="M12 3l7 3v5c0 5-3.5 8.5-7 10-3.5-1.5-7-5-7-10V6l7-3z" />
  </svg>
);

export const ArrowOut = ({ size = 18 }: P) => (
  <svg {...base(size)}>
    <path d="M7 17L17 7M9 7h8v8" />
  </svg>
);

export const Sparkle = ({ size = 14 }: P) => (
  <svg {...base(size)} fill="currentColor" stroke="none">
    <path d="M12 2l2.2 6.3L20.5 10l-6.3 2.2L12 18.5l-2.2-6.3L3.5 10l6.3-1.7L12 2z" />
  </svg>
);

export const Clock = ({ size = 14 }: P) => (
  <svg {...base(size)}>
    <circle cx="12" cy="12" r="9" />
    <path d="M12 7v5l3 2" />
  </svg>
);
