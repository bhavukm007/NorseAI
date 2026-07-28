interface BrandMarkProps {
  className?: string;
  compact?: boolean;
}

export function BrandMark({ className = "" }: BrandMarkProps) {
  return (
    <span className={`norse-mark ${className}`.trim()}>
      <img alt="" aria-hidden="true" src="/logo-transparent.png" />
    </span>
  );
}
