import { ArrowRightIcon } from '@phosphor-icons/react';
import type { ButtonHTMLAttributes, ReactNode } from 'react';
import { Link, type LinkProps } from 'react-router';
import { cn } from '@/lib/cn';

type Variant = 'primary' | 'secondary' | 'quiet';

const base =
  'group relative inline-flex min-h-12 items-center justify-center gap-3 rounded-full font-medium whitespace-nowrap ' +
  'transition-[transform,background-color,color,box-shadow] duration-500 ease-spring active:scale-[0.98] ' +
  'disabled:pointer-events-none disabled:opacity-50';

const variants: Record<Variant, string> = {
  primary: 'bg-accent text-accent-ink shadow-soft hover:brightness-110',
  secondary: 'bg-surface text-ink ring-1 ring-line hover:bg-surface-sunk',
  quiet: 'text-ink-soft underline-offset-4 hover:text-ink hover:underline',
};

const padding: Record<Variant, string> = {
  primary: 'px-6 py-3',
  secondary: 'px-6 py-3',
  quiet: 'px-2 py-2',
};

function TrailingArrow() {
  return (
    <span
      aria-hidden
      className="-mr-3 flex size-8 items-center justify-center rounded-full bg-accent-ink/15 transition-transform duration-500 ease-spring group-hover:translate-x-0.5 group-hover:-translate-y-px group-hover:scale-105"
    >
      <ArrowRightIcon size={16} weight="bold" />
    </span>
  );
}

interface CommonProps {
  variant?: Variant;
  arrow?: boolean;
  className?: string;
  children: ReactNode;
}

export function Button({
  variant = 'primary',
  arrow = false,
  className,
  children,
  type = 'button',
  ...rest
}: CommonProps & ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      type={type}
      className={cn(base, variants[variant], padding[variant], arrow && 'pr-4', className)}
      {...rest}
    >
      {children}
      {arrow && <TrailingArrow />}
    </button>
  );
}

export function ButtonLink({
  variant = 'primary',
  arrow = false,
  className,
  children,
  ...rest
}: CommonProps & LinkProps) {
  return (
    <Link
      className={cn(base, variants[variant], padding[variant], arrow && 'pr-4', className)}
      {...rest}
    >
      {children}
      {arrow && <TrailingArrow />}
    </Link>
  );
}
