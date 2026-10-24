import * as React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';

import { cn } from '@/lib/utils';

/**
 * Heyclicky Badge — the lowercase section label.
 *
 * Small, wide-tracked, lowercase type in a full-round chip. The default chip
 * is the same lit silver gradient the segmented controls use, so labels read
 * as part of the desktop chrome rather than as coloured status pills.
 */
const badgeVariants = cva(
  [
    'inline-flex items-center justify-center gap-1.5 whitespace-nowrap',
    'rounded-full font-bold lowercase tracking-[0.08em]',
    'transition-[background,box-shadow,color] duration-200 ease-out',
  ].join(' '),
  {
    variants: {
      variant: {
        default: 'bg-[image:var(--gradient-chip)] text-foreground shadow-[var(--shadow-button)]',
        primary:
          'bg-[image:var(--gradient-primary)] text-primary-foreground shadow-[var(--shadow-control)]',
        secondary: 'bg-secondary text-secondary-foreground',
        outline: 'border border-border bg-card text-foreground',
        muted: 'bg-muted-foreground/25 text-card',
        success: 'bg-success/15 text-success',
        warning: 'bg-warning/20 text-warning',
        destructive:
          'bg-[image:var(--gradient-destructive)] text-destructive-foreground shadow-[var(--shadow-control)]',
      },
      size: {
        sm: 'px-2 py-0.5 text-[0.625rem]',
        default: 'px-3 py-1 text-[0.6875rem]',
        lg: 'px-3.5 py-1.5 text-xs',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  },
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>, VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, size, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ variant, size }), className)} {...props} />;
}

export { Badge, badgeVariants };
