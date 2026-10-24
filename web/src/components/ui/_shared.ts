export const formFieldBase =
  'w-full rounded-md px-3.5 text-sm ' +
  'bg-input text-foreground ' +
  'border border-border ' +
  'placeholder:text-muted-foreground ' +
  'transition-[border-color,box-shadow] duration-200 ease-out ' +
  'hover:border-ring/40 ' +
  'focus-visible:outline-none focus-visible:border-ring ' +
  'focus-visible:ring-2 focus-visible:ring-ring/25 focus-visible:ring-offset-0 ' +
  'disabled:cursor-not-allowed disabled:opacity-50 disabled:bg-muted';

/** Height + vertical padding for single-line form fields (h-10, the pill height) */
export const formFieldSingleLine = 'flex h-10 py-2';

/** Vertical padding and min-height for multi-line form fields */
export const formFieldMultiLine = 'flex min-h-[84px] py-2.5 resize-y';

/**
 * The floating panel surface every Base UI menu drops onto.
 *
 * A white window body behind a hairline and the one soft far-throw shadow.
 * The caller sets its own radius, so this carries no corner.
 */
export const hlPopSurface =
  'border border-border bg-popover text-popover-foreground ' + 'shadow-[var(--shadow-m)]';

/**
 * The floating panel surface, shared by every menu that drops over the page.
 *
 * A white window body behind a hairline, a 10px window corner, and the one
 * soft far-throw shadow. This is the same recipe Select, Menubar and
 * NavigationMenu declare inline, so a panel built from it matches them.
 */
export const popoverSurface =
  'rounded-lg border border-border bg-popover text-popover-foreground ' +
  'shadow-[var(--shadow-m)]';
