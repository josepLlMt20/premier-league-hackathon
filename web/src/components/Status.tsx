import { Button } from './ui/button';
import { copy, type Language } from '../domain/copy';
export function Status({
  language,
  error,
  children,
  retry,
}: {
  language: Language;
  error?: boolean;
  children: React.ReactNode;
  retry?: () => void;
}) {
  return (
    <div className={error ? 'status status-error' : 'status'} role={error ? 'alert' : 'status'}>
      <p>{children}</p>
      {retry && (
        <Button variant="secondary" onClick={retry}>
          {copy[language].retry}
        </Button>
      )}
    </div>
  );
}
