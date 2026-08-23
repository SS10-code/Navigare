import { SVGProps } from "react";

export type IconName =
  | "logo"
  | "chart"
  | "box"
  | "cart"
  | "users"
  | "trending"
  | "search"
  | "upload"
  | "cash"
  | "mail"
  | "rocket"
  | "download"
  | "file"
  | "check"
  | "alert"
  | "warning"
  | "clock"
  | "radar"
  | "siren"
  | "route"
  | "lock"
  | "refresh"
  | "arrowUp"
  | "arrowDown"
  | "settings"
  | "sun"
  | "bolt"
  | "loading";

const PATHS: Record<IconName, React.ReactNode> = {
  logo: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 3 L18 12 L12 21 L6 12 Z" />
      <circle cx="12" cy="12" r="1.5" fill="currentColor" stroke="none" />
    </>
  ),
  chart: (
    <>
      <path d="M4 20 L20 20" />
      <path d="M6 20 L6 12" />
      <path d="M12 20 L12 5" />
      <path d="M18 20 L18 9" />
    </>
  ),
  box: (
    <>
      <path d="M3 7 L12 3 L21 7 L21 17 L12 21 L3 17 Z" />
      <path d="M3 7 L12 11 L21 7" />
      <path d="M12 11 L12 21" />
    </>
  ),
  cart: (
    <>
      <path d="M3 4 L5 4 L7 15 L19 15 L21 7 L6.5 7" />
      <circle cx="9.5" cy="19" r="1.4" />
      <circle cx="16.5" cy="19" r="1.4" />
    </>
  ),
  users: (
    <>
      <circle cx="9" cy="8" r="3.5" />
      <path d="M2.5 20 C2.5 15 5.5 12.5 9 12.5 C12.5 12.5 15.5 15 15.5 20" />
      <circle cx="17" cy="9" r="2.5" />
      <path d="M16 13.5 C19 13.8 21.5 16 21.5 20" />
    </>
  ),
  trending: (
    <>
      <path d="M3 17 L9 11 L13 15 L21 6" />
      <path d="M15 6 L21 6 L21 12" />
    </>
  ),
  search: (
    <>
      <circle cx="11" cy="11" r="6.5" />
      <path d="M16 16 L21 21" />
    </>
  ),
  upload: (
    <>
      <path d="M12 16 L12 4" />
      <path d="M7 9 L12 4 L17 9" />
      <path d="M4 16 L4 20 L20 20 L20 16" />
    </>
  ),
  cash: (
    <>
      <rect x="2.5" y="6" width="19" height="13" />
      <circle cx="12" cy="12.5" r="3.5" />
      <path d="M5.5 9.5 L5.5 9.5" />
      <path d="M18.5 15.5 L18.5 15.5" />
    </>
  ),
  mail: (
    <>
      <rect x="3" y="5" width="18" height="14" />
      <path d="M3 7 L12 13 L21 7" />
    </>
  ),
  rocket: (
    <>
      <path d="M12 3 C15 6 16 10 16 13 L8 13 C8 10 9 6 12 3" />
      <circle cx="12" cy="11" r="1.6" />
      <path d="M8 13 L5 17 L8 16.5 L9 19 L11 16" />
      <path d="M16 13 L19 17 L16 16.5 L15 19 L13 16" />
      <path d="M12 13 L12 16" />
    </>
  ),
  download: (
    <>
      <path d="M12 4 L12 16" />
      <path d="M7 11 L12 16 L17 11" />
      <path d="M4 16 L4 20 L20 20 L20 16" />
    </>
  ),
  file: (
    <>
      <path d="M6 3 L14 3 L18 7 L18 21 L6 21 Z" />
      <path d="M14 3 L14 7 L18 7" />
      <path d="M9 12 L15 12" />
      <path d="M9 16 L15 16" />
    </>
  ),
  check: <path d="M4 12.5 L9.5 18 L20 6" />,
  alert: (
    <>
      <path d="M12 3 L22 20 L2 20 Z" />
      <path d="M12 9 L12 14" />
      <circle cx="12" cy="17" r="0.8" fill="currentColor" stroke="none" />
    </>
  ),
  warning: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7 L12 13" />
      <circle cx="12" cy="16.5" r="0.9" fill="currentColor" stroke="none" />
    </>
  ),
  clock: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 6.5 L12 12 L16 14.5" />
    </>
  ),
  radar: (
    <>
      <circle cx="12" cy="12" r="9" />
      <circle cx="12" cy="12" r="5" />
      <circle cx="12" cy="12" r="1.2" fill="currentColor" stroke="none" />
      <path d="M12 12 L20 12" />
      <path d="M12 12 L17 6" />
    </>
  ),
  siren: (
    <>
      <path d="M12 3 L20 16 L4 16 Z" />
      <rect x="7" y="16" width="10" height="4" />
      <circle cx="12" cy="18.5" r="0.9" fill="currentColor" stroke="none" />
      <path d="M12 7 L12 11" />
      <path d="M8.5 8.5 L9.5 10" />
      <path d="M15.5 8.5 L14.5 10" />
    </>
  ),
  route: (
    <>
      <circle cx="6" cy="6" r="2.5" />
      <circle cx="18" cy="18" r="2.5" />
      <path d="M6 8.5 L6 15 C6 17 7 18.5 8.5 18.5 L15.5 18.5 C17 18.5 18 17.5 18 15.5 L18 15.5" />
    </>
  ),
  lock: (
    <>
      <rect x="5" y="10.5" width="14" height="9.5" />
      <path d="M8 10.5 L8 7.5 C8 5 9.5 3.5 12 3.5 C14.5 3.5 16 5 16 7.5 L16 10.5" />
    </>
  ),
  refresh: (
    <>
      <path d="M20 12 C20 16.5 16.5 20 12 20 C8 20 4.5 16.5 4.5 12" />
      <path d="M4.5 4.5 L4.5 9 L9 9" />
      <path d="M4 12 C4 7.5 7.5 4 12 4 C16 4 19.5 7.5 19.5 12" />
      <path d="M19.5 19.5 L19.5 15 L15 15" />
    </>
  ),
  arrowUp: (
    <>
      <path d="M12 20 L12 4" />
      <path d="M5 11 L12 4 L19 11" />
    </>
  ),
  arrowDown: (
    <>
      <path d="M12 4 L12 20" />
      <path d="M5 13 L12 20 L19 13" />
    </>
  ),
  settings: (
    <>
      <circle cx="12" cy="12" r="3" />
      <path d="M12 2.5 L12 5.5 M12 18.5 L12 21.5 M2.5 12 L5.5 12 M18.5 12 L21.5 12 M5.5 5.5 L7.5 7.5 M16.5 16.5 L18.5 18.5 M18.5 5.5 L16.5 7.5 M7.5 16.5 L5.5 18.5" />
    </>
  ),
  sun: (
    <>
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2 L12 5 M12 19 L12 22 M2 12 L5 12 M19 12 L22 12 M4.5 4.5 L6.5 6.5 M17.5 17.5 L19.5 19.5 M19.5 4.5 L17.5 6.5 M6.5 17.5 L4.5 19.5" />
    </>
  ),
  bolt: (
    <>
      <path d="M13 2 L5 14 L11 14 L10 22 L19 9 L13 9 Z" />
    </>
  ),
  loading: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 3 L12 8" />
      <path d="M12 16 L12 21" />
    </>
  ),
};

interface IconProps extends SVGProps<SVGSVGElement> {
  name: IconName;
  size?: number;
}

export default function Icon({ name, size = 20, ...rest }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="square"
      strokeLinejoin="miter"
      aria-hidden="true"
      {...rest}
    >
      {PATHS[name]}
    </svg>
  );
}
