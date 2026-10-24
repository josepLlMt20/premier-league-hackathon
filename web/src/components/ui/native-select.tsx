import * as React from 'react';

import { cn } from '@/lib/utils';
import { formFieldBase, formFieldSingleLine } from './_shared';

export interface NativeSelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {}

const NativeSelect = React.forwardRef<HTMLSelectElement, NativeSelectProps>(
  ({ className, children, ...props }, ref) => (
    <div className="relative">
      <select
        ref={ref}
        className={cn(formFieldBase, formFieldSingleLine, 'cursor-pointer', className)}
        {...props}
      >
        {children}
      </select>
    </div>
  ),
);
NativeSelect.displayName = 'NativeSelect';

export { NativeSelect };
