// MingCute line icons, exact source returned by Better Design / Iconify.
import type { SVGProps } from 'react';
type Props = SVGProps<SVGSVGElement>;
export function PlayLineIcon(props: Props) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" {...props}>
      <path
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        d="M6.661 4.88a.47.47 0 0 1 .656-.378c1.032.441 3.375 1.502 6.354 3.222s5.071 3.22 5.97 3.893a.468.468 0 0 1 0 .755c-.889.667-2.954 2.148-5.97 3.89c-3.019 1.742-5.334 2.79-6.356 3.226a.468.468 0 0 1-.653-.378c-.135-1.11-.389-3.662-.389-7.116c0-3.452.254-6.003.388-7.115Z"
      />
    </svg>
  );
}
export function PauseLineIcon(props: Props) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" {...props}>
      <path
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeWidth="2"
        d="M8 5v14m8-14v14"
      />
    </svg>
  );
}
export function FastRewindLineIcon(props: Props) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" {...props}>
      <path
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        d="M11.612 6.863a.328.328 0 0 0-.468-.263c-.704.327-2.25 1.09-4.206 2.313A41 41 0 0 0 2.94 11.74a.33.33 0 0 0 0 .514c.58.473 1.966 1.553 4 2.825c1.982 1.24 3.51 1.993 4.206 2.316a.328.328 0 0 0 .467-.263c.09-.804.258-2.645.258-5.135s-.168-4.329-.258-5.134Z"
      />
      <path
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        d="M20.612 6.863a.328.328 0 0 0-.468-.263c-.704.327-2.25 1.09-4.206 2.313a41 41 0 0 0-3.999 2.827a.33.33 0 0 0 0 .514c.58.473 1.966 1.553 4 2.825c1.982 1.24 3.51 1.993 4.205 2.316a.328.328 0 0 0 .468-.263c.09-.804.258-2.645.258-5.135s-.168-4.329-.258-5.134Z"
      />
    </svg>
  );
}
export function CloseLineIcon(props: Props) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" {...props}>
      <path
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeWidth="2"
        d="m5.636 5.637l12.728 12.728m-12.728 0L18.364 5.637"
      />
    </svg>
  );
}

export { FootballLineIcon, TargetLineIcon, SettingsLineIcon, ArrowRightLineIcon } from './football';
