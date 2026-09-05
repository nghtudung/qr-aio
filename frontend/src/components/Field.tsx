import { ReactNode } from "react";

type Props = {
  label: string;
  children: ReactNode;
};

export function Field({ label, children }: Props) {
  return (
    <label className="space-y-1.5">
      <span className="label">{label}</span>
      {children}
    </label>
  );
}
