import * as React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';

import { cn } from '@/lib/utils';

/** Plain provenance label; no decorative status dot implies live AI. */
const badgeVariants = cva(['studio-badge'].join(' '), {
  variants: {
    variant: {
      default: '',
      primary: 'text-primary',
      secondary: 'bg-secondary text-secondary-foreground',
      outline: 'border border-border bg-card text-foreground',
      muted: 'bg-muted-foreground/25 text-card',
      success: 'bg-success/15 text-success',
      warning: 'bg-warning/20 text-warning',
      destructive: 'text-destructive',
    },
    size: {
      sm: '',
      default: '',
      lg: '',
    },
  },
  defaultVariants: {
    variant: 'default',
    size: 'default',
  },
});

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>, VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, size, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ variant, size }), className)} {...props} />;
}

export { Badge, badgeVariants };
